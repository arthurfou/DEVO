"""M1 — même structure que eval_evimo_m1_decoupled.py mais pour EVIMO2.

Différences vs EVIMO1 :
- _resolve_npz adapté à la structure EVIMO2 (samsung_mono/)
- imports depuis eval_evimo2_evs (H=480, W=640)
- defaults val_split = splits/evimo2/evimo2_val.txt

Fix timestamp identique : _ts_offset() corrige le décalage Unix epoch vs secondes relatives.
Ne pas supprimer ce fix.
"""
import os
import argparse

import numpy as np
import torch
from devo.config import cfg
from utils.eval_utils import assert_eval_config

from eval_evimo2_evs import evaluate  # même dossier


def _resolve_npz(scene, mask_root):
    """scene 'imo/eval/seq_name' -> '{mask_root}/imo/eval/seq_name.npz'.

    mask_root doit pointer vers datasets/evimo2/evimo1_format
    (produit par scripts/convert_evimo2_to_evimo1.py).
    """
    scene = scene.strip("/")

    # Format principal : {mask_root}/{scene}.npz
    c1 = os.path.join(mask_root, scene + ".npz")
    if os.path.exists(c1):
        return c1

    # Fallback : seq_name seul → chercher dans imo/eval/
    parts = scene.split("/")
    seq = parts[-1]
    for subdir in ("imo/eval", "imo/train"):
        c = os.path.join(mask_root, subdir, seq + ".npz")
        if os.path.exists(c):
            return c

    return c1  # retourner pour un message d'erreur lisible


def _ts_offset(datapath_val, npz_path):
    """Offset (s) à soustraire de ts_us/1e6 pour aligner avec les ts relatifs du npz.

    Identique à EVIMO1 — ne pas supprimer : EVIMO2 stocke aussi meta["frames"]["ts"]
    en secondes relatives alors que DEVO utilise Unix epoch µs.
    """
    from ms_model.io.loaders import load_evimo_mask
    tss_file = os.path.join(datapath_val, "tss_imgs_us.txt")
    if not os.path.exists(tss_file):
        return 0.0
    tss_us = np.loadtxt(tss_file)
    if tss_us.ndim == 0:
        tss_us = np.array([float(tss_us)])
    fm = load_evimo_mask(npz_path)
    if len(tss_us) == 0 or len(fm.ts) == 0:
        return 0.0
    devo_t0_s = float(np.sort(tss_us)[0]) / 1e6
    meta_t0_s = float(fm.ts[0])
    if abs(devo_t0_s - meta_t0_s) < 100.0:
        return 0.0
    offset = devo_t0_s - meta_t0_s
    print(f"[ts_offset] {os.path.basename(datapath_val)}: offset={offset:.3f}s "
          f"(DEVO t0={devo_t0_s:.3f}s, meta t0={meta_t0_s:.6f}s)")
    return offset


def make_oracle_factory(mask_root, patch_size=4, thicken_radius=0, device="cuda"):
    from ms_model.oracle import OracleDynMaskProvider

    def factory(scene, datapath_val):
        npz = _resolve_npz(scene, mask_root)
        if not os.path.exists(npz):
            raise FileNotFoundError(f"[M1] npz GT introuvable pour '{scene}': {npz}")
        offset = _ts_offset(datapath_val, npz)
        print(f"[M1] Oracle masks <- {npz}")
        return OracleDynMaskProvider.from_evimo_npz(
            npz, patch_size=patch_size, thicken_radius=thicken_radius,
            device=device, ts_offset_s=offset)

    return factory


def make_learned_factory(mask_root, ms_weights, ms_config, threshold=None, device="cuda"):
    from ms_model.oracle import LearnedDynMaskProvider

    def factory(scene, datapath_val):
        npz = _resolve_npz(scene, mask_root)
        if not os.path.exists(npz):
            raise FileNotFoundError(f"[M1] npz introuvable pour '{scene}': {npz}")
        offset = _ts_offset(datapath_val, npz)
        print(f"[M1] Modèle MS -> masque appris sur {npz}")
        return LearnedDynMaskProvider(
            npz_path=npz, weights_path=ms_weights, config_path=ms_config,
            device=device, threshold=threshold, ts_offset_s=offset)

    return factory


def _mean_ate(results_dict):
    vals = []
    for v in results_dict.values():
        try:
            vals.append(float(v))
        except (TypeError, ValueError):
            continue
    return sum(vals) / len(vals) if vals else float("nan")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default="config/eval_evimo.yaml")
    parser.add_argument('--datapath', default='', help='DEVO EVIMO2 eval_preprocessed/')
    parser.add_argument('--weights', default="DEVO.pth", help='checkpoint VO DEVO')
    parser.add_argument('--val_split', type=str, default="splits/evimo2/evimo2_val.txt")
    parser.add_argument('--mask_root', type=str, required=True, help='racine npz EVIMO2')
    parser.add_argument('--ms_weights', type=str, required=True, help='checkpoint modèle MS (best.pt)')
    parser.add_argument('--ms_config', type=str, required=True, help='yaml entraînement MS')
    parser.add_argument('--threshold', type=float, default=None)
    parser.add_argument('--thicken_radius', type=int, default=2)
    parser.add_argument('--with_oracle', action="store_true")
    parser.add_argument('--no_vanilla', action="store_true")
    parser.add_argument('--trials', type=int, default=1)
    parser.add_argument('--stride', type=int, default=1)
    parser.add_argument('--expname', type=str, default="m1_evimo2")
    args = parser.parse_args()
    assert_eval_config(args)

    cfg.merge_from_file(args.config)
    torch.manual_seed(1234)
    args.plot = False
    args.save_trajectory = True

    common = dict(datapath=args.datapath, split_file=args.val_split,
                  trials=args.trials, plot=False, save=True, stride=args.stride)

    res = {}
    if not args.no_vanilla:
        print("\n=== [M1] Passe VANILLA ===")
        args.expname = "m1_evimo2_vanilla"
        res["vanilla"], _ = evaluate(cfg, args, args.weights, dyn_mask_provider_factory=None, **common)

    print("\n=== [M1] Passe APPRIS (préprocesseur découplé) ===")
    args.expname = "m1_evimo2_learned"
    learned = make_learned_factory(args.mask_root, args.ms_weights, args.ms_config,
                                   threshold=args.threshold)
    res["learned"], _ = evaluate(cfg, args, args.weights, dyn_mask_provider_factory=learned, **common)

    if args.with_oracle:
        print("\n=== [M1] Passe ORACLE (plafond) ===")
        args.expname = "m1_evimo2_oracle"
        oracle = make_oracle_factory(args.mask_root, thicken_radius=args.thicken_radius)
        res["oracle"], _ = evaluate(cfg, args, args.weights, dyn_mask_provider_factory=oracle, **common)

    print("\n==================== [M1] RÉSUMÉ ATE ====================")
    order = [k for k in ("vanilla", "learned", "oracle") if k in res]
    means = {k: _mean_ate(res[k]) for k in order}
    for k in order:
        print(f"  {k:8s}: ATE moyen = {means[k]:.4f}")
    if "vanilla" in means and "learned" in means:
        a, b = means["vanilla"], means["learned"]
        if a == a and b == b:
            d = a - b
            print(f"\n  Δ (vanilla - learned) = {d:+.4f}  ({100*d/a:+.1f}%)"
                  f"  -> {'appris aide' if d > 0 else 'pas de gain'}")
    if "learned" in means and "oracle" in means:
        print(f"  écart appris -> oracle (plafond) = {means['learned'] - means['oracle']:+.4f}")
    print("========================================================")
