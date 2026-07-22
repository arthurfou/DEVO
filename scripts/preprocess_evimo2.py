"""Préprocessing EVIMO2 -> format DEVO par scène.

Lit chaque répertoire de séquence EVIMO2 (samsung_mono) et produit :
  evs.npy          (N,4) float64: [ts_us, x, y, p]
  tss_imgs_us.txt  timestamps frames en µs (relatifs, t0=0)
  calib.txt        "fx fy cx cy"
  gt_stamped.txt   "ts tx ty tz qx qy qz qw" (poses caméra GT)
  rectify_map.h5   identité (480×640, samsung_mono déjà rectifié)

Usage:
    python scripts/preprocess_evimo2.py \\
        --src  /home/i/i0002573/arthur_ipal/datasets/evimo2/samsung_mono/imo/eval \\
        --dst  /home/i/i0002573/arthur_ipal/datasets/evimo2/eval_preprocessed

Structure src attendue :
    {src}/{seq_name}/
        dataset_events_t.npy
        dataset_events_xy.npy
        dataset_events_p.npy
        dataset_info.npz   → K, index, meta.frames[i].{ts, cam.pos.{t,q}}

Chaque {seq_name}/ produit {dst}/{seq_name}/ avec les 5 fichiers DEVO.
"""
import argparse
import os
import sys

import h5py
import numpy as np


def _make_identity_rectify_map(H: int, W: int, out_path: str) -> None:
    xs, ys = np.meshgrid(np.arange(W), np.arange(H))
    rmap = np.stack([xs, ys], axis=-1).astype(np.float32)
    with h5py.File(out_path, "w") as hf:
        hf.create_dataset("rectify_map", data=rmap)


def preprocess_sequence(src_dir: str, out_dir: str, verbose: bool = True) -> None:
    os.makedirs(out_dir, exist_ok=True)

    # ── Events ───────────────────────────────────────────────────────────────
    ev_t  = np.load(os.path.join(src_dir, "dataset_events_t.npy")).astype(np.float64)   # sec
    ev_xy = np.load(os.path.join(src_dir, "dataset_events_xy.npy")).astype(np.float64)  # (N,2) x,y
    ev_p  = np.load(os.path.join(src_dir, "dataset_events_p.npy")).astype(np.float64)   # polarity

    ts_us = ev_t * 1e6  # secondes → µs
    evs = np.stack([ts_us, ev_xy[:, 0], ev_xy[:, 1], ev_p], axis=1)
    np.save(os.path.join(out_dir, "evs.npy"), evs)

    # ── Info ─────────────────────────────────────────────────────────────────
    fi     = np.load(os.path.join(src_dir, "dataset_info.npz"), allow_pickle=True)
    K      = fi["K"]           # (3,3)
    meta   = fi["meta"].item()
    frames = meta["frames"]    # list of dicts

    # ── Timestamps frames ────────────────────────────────────────────────────
    ts_rel = np.array([f["ts"] for f in frames], dtype=np.float64)  # secondes relatives
    tss_us = ts_rel * 1e6
    np.savetxt(os.path.join(out_dir, "tss_imgs_us.txt"), tss_us)

    # ── Intrinsèques ─────────────────────────────────────────────────────────
    fx, fy = float(K[0, 0]), float(K[1, 1])
    cx, cy = float(K[0, 2]), float(K[1, 2])
    with open(os.path.join(out_dir, "calib.txt"), "w") as fp:
        fp.write(f"{fx} {fy} {cx} {cy}\n")

    # ── Poses GT ─────────────────────────────────────────────────────────────
    # format DEVO : "ts tx ty tz qx qy qz qw"
    # EVIMO2 : frame['cam']['pos']['t'] = {x,y,z}, frame['cam']['pos']['q'] = {w,x,y,z}
    gt_lines = []
    for f in frames:
        ts = float(f["ts"])
        try:
            pos = f["cam"]["pos"]
            t = pos["t"]
            q = pos["q"]
            tx, ty, tz = float(t["x"]), float(t["y"]), float(t["z"])
            qx, qy, qz, qw = float(q["x"]), float(q["y"]), float(q["z"]), float(q["w"])
            gt_lines.append(f"{ts:.9f} {tx:.9f} {ty:.9f} {tz:.9f} "
                            f"{qx:.9f} {qy:.9f} {qz:.9f} {qw:.9f}")
        except (KeyError, TypeError) as e:
            print(f"  [warn] pose manquante pour frame ts={ts}: {e}")

    with open(os.path.join(out_dir, "gt_stamped.txt"), "w") as fp:
        fp.write("\n".join(gt_lines) + ("\n" if gt_lines else ""))

    # ── Rectify map (identité, samsung_mono déjà rectifié) ──────────────────
    H, W = 480, 640
    _make_identity_rectify_map(H, W, os.path.join(out_dir, "rectify_map.h5"))

    if verbose:
        print(f"  -> {out_dir}  ({len(ev_t)//1e6:.1f}M events, {len(frames)} frames)")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--src", required=True,
                   help="Répertoire contenant les sous-répertoires de séquences EVIMO2")
    p.add_argument("--dst", required=True,
                   help="Répertoire de sortie au format DEVO")
    p.add_argument("--seq", default=None,
                   help="Traiter une seule séquence (nom du sous-répertoire)")
    args = p.parse_args()

    if args.seq:
        src = os.path.join(args.src, args.seq)
        dst = os.path.join(args.dst, args.seq)
        print(f"[{args.seq}]")
        preprocess_sequence(src, dst)
        return

    # Découverte automatique
    seq_dirs = sorted([
        d for d in os.listdir(args.src)
        if os.path.isdir(os.path.join(args.src, d))
        and os.path.exists(os.path.join(args.src, d, "dataset_info.npz"))
    ])

    if not seq_dirs:
        print(f"Aucune séquence trouvée sous {args.src}", file=sys.stderr)
        sys.exit(1)

    print(f"Preprocessing {len(seq_dirs)} séquences -> {args.dst}")
    ok, errors = 0, []
    for name in seq_dirs:
        src = os.path.join(args.src, name)
        dst = os.path.join(args.dst, name)
        print(f"[{name}]")
        try:
            preprocess_sequence(src, dst)
            ok += 1
        except Exception as e:
            print(f"  [ERROR] {e}")
            errors.append((name, str(e)))

    print(f"\nDone: {ok}/{len(seq_dirs)}" + (f", {len(errors)} erreurs" if errors else ""))
    for n, e in errors:
        print(f"  ERREUR {n}: {e}")


if __name__ == "__main__":
    main()
