"""M0 — expérience décisive du plan de recherche (voir ../../../PLAN.md).

Évalue DEVO sur EVIMO **deux fois** — vanilla vs. masque oracle GT injecté dans la score
map — et affiche le delta ATE. Gate go/no-go : si l'oracle améliore l'ATE, le "plafond"
existe et tout le reste du plan tient ; sinon, changer de données AVANT d'investir.

Le masque oracle vient de la segmentation GT EVIMO (npz `mask`+`meta`), sous-échantillonnée
à la résolution de la score map et alignée au timestamp du voxel via
`ms_model.oracle.OracleDynMaskProvider`. L'injection se fait via le hook additif
`run_voxel(..., dyn_mask_provider=...)` -> `DEVO.__call__(dyn_score=...)` (None = vanilla).

À lancer depuis la racine du repo DEVO (pour que `utils`/`config` soient importables) :

    conda activate devo
    python evals/eval_evs/eval_evimo_m0_oracle.py \
        --datapath /chemin/vers/evimo/eval \
        --weights DEVO.pth \
        --val_split splits/evimo/evimo_val.txt \
        --mask_root /home/arthur/IPAL/arthur_ipal/datasets/evimo_full/eval \
        --thicken_radius 2

`ms_model` doit être installé dans l'env (`pip install -e MS_Model`).
"""
import os
import argparse

import torch
from devo.config import cfg
from utils.eval_utils import assert_eval_config

from eval_evimo_evs import evaluate  # même dossier


def make_oracle_factory(mask_root, patch_size=4, thicken_radius=0, device="cuda"):
    """Retourne factory(scene, datapath_val) -> OracleDynMaskProvider.

    Convention de nommage EVIMO : scene "box/raw/seq_00" -> npz masques
    "{mask_root}/box/npz/seq_00.npz". Adapte `resolve_npz` si ton arbo diffère.
    """
    from ms_model.oracle import OracleDynMaskProvider

    def resolve_npz(scene):
        parts = scene.strip("/").split("/")
        cat, seq = parts[0], parts[-1]  # "box", "seq_00"
        return os.path.join(mask_root, cat, "npz", f"{seq}.npz")

    cache = {}

    def factory(scene, datapath_val):
        npz = resolve_npz(scene)
        if not os.path.exists(npz):
            raise FileNotFoundError(
                f"[M0] npz masques GT introuvable pour la scène '{scene}': {npz}\n"
                f"     Vérifie --mask_root ou adapte resolve_npz() dans ce script."
            )
        if npz not in cache:
            print(f"[M0] Oracle masks <- {npz}")
            cache[npz] = OracleDynMaskProvider.from_evimo_npz(
                npz, patch_size=patch_size, thicken_radius=thicken_radius, device=device
            )
        return cache[npz]

    return factory


def _mean_ate(results_dict):
    """Extrait un ATE moyen lisible depuis le dict de résultats de log_results."""
    vals = []
    for k, v in results_dict.items():
        try:
            vals.append(float(v))
        except (TypeError, ValueError):
            continue
    return sum(vals) / len(vals) if vals else float("nan")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default="config/eval_evimo.yaml")
    parser.add_argument('--datapath', default='', help='DEVO EVIMO eval/ (preprocessé: evs.npy, gt_stamped.txt)')
    parser.add_argument('--weights', default="DEVO.pth")
    parser.add_argument('--val_split', type=str, default="splits/evimo/evimo_val.txt")
    parser.add_argument('--mask_root', type=str, required=True, help='racine des npz GT EVIMO (mask+meta)')
    parser.add_argument('--thicken_radius', type=int, default=0, help='dilatation des masques GT (px) avant downsample')
    parser.add_argument('--trials', type=int, default=1)
    parser.add_argument('--stride', type=int, default=1)
    parser.add_argument('--expname', type=str, default="m0_oracle")
    parser.add_argument('--vanilla_only', action="store_true", help='ne lancer que la passe vanilla')
    parser.add_argument('--oracle_only', action="store_true", help='ne lancer que la passe oracle')
    args = parser.parse_args()
    assert_eval_config(args)

    cfg.merge_from_file(args.config)
    torch.manual_seed(1234)
    args.plot = False
    args.save_trajectory = True

    common = dict(datapath=args.datapath, split_file=args.val_split,
                  trials=args.trials, plot=False, save=True, stride=args.stride)

    res = {}
    if not args.oracle_only:
        print("\n=== [M0] Passe VANILLA (dyn_mask_provider=None) ===")
        args.expname = "m0_vanilla"
        res["vanilla"], _ = evaluate(cfg, args, args.weights, dyn_mask_provider_factory=None, **common)

    if not args.vanilla_only:
        print("\n=== [M0] Passe ORACLE (masque GT -> score map) ===")
        args.expname = "m0_oracle"
        factory = make_oracle_factory(args.mask_root, patch_size=4,
                                      thicken_radius=args.thicken_radius)
        res["oracle"], _ = evaluate(cfg, args, args.weights, dyn_mask_provider_factory=factory, **common)

    print("\n==================== [M0] RÉSUMÉ ATE ====================")
    for k, v in res.items():
        print(f"  {k:8s}: {v}")
    if "vanilla" in res and "oracle" in res:
        a, b = _mean_ate(res["vanilla"]), _mean_ate(res["oracle"])
        print(f"\n  ATE moyen vanilla = {a:.4f}")
        print(f"  ATE moyen oracle  = {b:.4f}")
        if a == a and b == b:  # not NaN
            delta = a - b
            pct = 100.0 * delta / a if a else float('nan')
            verdict = "GO (oracle aide)" if delta > 0 else "NO-GO (pas de gain)"
            print(f"  Δ (vanilla - oracle) = {delta:+.4f}  ({pct:+.1f}%)  -> {verdict}")
    print("========================================================")
