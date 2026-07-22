"""M1 — baseline « suppression découplée » du plan de recherche (voir ../../../PLAN.md).

Évalue DEVO sur EVIMO avec, en préprocesseur, le masque dynamique prédit par un modèle MS
entraîné SÉPARÉMENT (convlstm, …). C'est le chiffre « art antérieur » (façon RPG) à battre
par l'approche couplée (M2/M3).

Réutilise toute la plomberie de M0 : le masque appris est servi à DEVO via le même hook
`run_voxel(..., dyn_mask_provider=...)`, mais fourni par `LearnedDynMaskProvider` au lieu de
l'oracle GT. Compare 3 passes : vanilla / oracle (plafond) / appris (baseline).

À lancer depuis la racine du repo DEVO :

    conda activate devo
    cd DEVO
    python evals/eval_evs/eval_evimo_m1_decoupled.py \
        --datapath <eval_EVIMO_preprocessé> \
        --weights DEVO.pth \
        --val_split splits/evimo/evimo_val.txt \
        --mask_root /home/arthur/IPAL/arthur_ipal/datasets/evimo_full/eval \
        --ms_weights /home/arthur/IPAL/arthur_ipal/MS_Model/checkpoints/v4-full-run1/best.pt \
        --ms_config  /home/arthur/IPAL/arthur_ipal/MS_Model/configs/convlstm_v4_full.yaml \
        --threshold 0.5

`ms_model` doit être installé dans l'env (`pip install -e MS_Model`).
"""
import os
import argparse

import numpy as np
import torch
from devo.config import cfg
from utils.eval_utils import assert_eval_config

from eval_evimo_evs import evaluate  # même dossier


def _resolve_npz(scene, mask_root):
    """scene 'box/raw/seq_00' -> '{mask_root}/box/npz/seq_00.npz' (adapte si arbo différente)."""
    parts = scene.strip("/").split("/")
    cat, seq = parts[0], parts[-1]
    return os.path.join(mask_root, cat, "npz", f"{seq}.npz")


def _ts_offset(datapath_val, npz_path):
    """Offset (s) à soustraire de ts_us/1e6 pour aligner avec les ts relatifs du npz.

    EVIMO npz stocke meta["frames"]["ts"] en secondes relatives (0.04, 0.07, …).
    DEVO utilise des ts_us en Unix epoch µs (~1.54e15 µs = 1.54e9 s).
    Offset = tss_imgs_us[0]/1e6 − meta_ts[0] ≈ Unix_start_s.
    Sans correction, searchsorted retourne toujours le dernier indice.
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
    # Si déjà même ordre de grandeur (<100 s d'écart) → pas d'offset nécessaire
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
    parser.add_argument('--datapath', default='', help='DEVO EVIMO eval/ (preprocessé)')
    parser.add_argument('--weights', default="DEVO.pth", help='checkpoint VO DEVO')
    parser.add_argument('--val_split', type=str, default="splits/evimo/evimo_val.txt")
    parser.add_argument('--mask_root', type=str, required=True, help='racine npz EVIMO')
    parser.add_argument('--ms_weights', type=str, required=True, help='checkpoint modèle MS (best.pt)')
    parser.add_argument('--ms_config', type=str, required=True, help='yaml entraînement MS')
    parser.add_argument('--threshold', type=float, default=None,
                        help='seuil binarisation du masque appris (défaut: None = score continu doux)')
    parser.add_argument('--thicken_radius', type=int, default=2, help='dilatation masque oracle')
    parser.add_argument('--with_oracle', action="store_true", help='ajoute la passe oracle (plafond)')
    parser.add_argument('--no_vanilla', action="store_true", help='saute la passe vanilla')
    parser.add_argument('--trials', type=int, default=1)
    parser.add_argument('--stride', type=int, default=1)
    parser.add_argument('--expname', type=str, default="m1")
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
        args.expname = "m1_vanilla"
        res["vanilla"], _ = evaluate(cfg, args, args.weights, dyn_mask_provider_factory=None, **common)

    print("\n=== [M1] Passe APPRIS (préprocesseur découplé) ===")
    args.expname = "m1_learned"
    learned = make_learned_factory(args.mask_root, args.ms_weights, args.ms_config,
                                   threshold=args.threshold)
    res["learned"], _ = evaluate(cfg, args, args.weights, dyn_mask_provider_factory=learned, **common)

    if args.with_oracle:
        print("\n=== [M1] Passe ORACLE (plafond) ===")
        args.expname = "m1_oracle"
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
