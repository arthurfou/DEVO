"""M4 — générateur du TABLEAU CENTRAL du papier (voir ../../../PLAN.md §4).

Observation clé : les 6 lignes s'évaluent identiquement — `DEVO + un fournisseur de masque` —
et ne diffèrent que par l'ORIGINE du masque. Ce script lance chaque ligne disponible (celles
dont les checkpoints sont fournis), collecte l'ATE, et écrit le tableau en Markdown + CSV.

    ligne                         | fournisseur de masque
    ------------------------------|------------------------------------------------
    DEVO vanilla                  | (aucun)
    DEVO + oracle GT              | OracleDynMaskProvider (plafond)
    DEVO + appris découplé (M1)   | LearnedDynMaskProvider(convlstm entraîné séparément)
    DEVO + couplé supervisé (M2)  | LearnedDynMaskProvider(MS fine-tuné couplé, GT)   [+ DEVO couplé]
    DEVO + couplé auto-sup (M3)   | LearnedDynMaskProvider(MS fine-tuné couplé, sans GT) [+ DEVO couplé]

⚠️ Ce script NE fabrique aucun chiffre : il exécute les évals réelles (GPU requis) et agrège
leurs sorties. Sans checkpoint pour une ligne, la ligne est marquée "—" (non lancée).

À lancer depuis la racine du repo DEVO, env `devo`, `ms_model` installé.
"""
import os
import csv
import argparse

import torch
from devo.config import cfg
from utils.eval_utils import assert_eval_config

from eval_evimo_evs import evaluate
from eval_evimo_m1_decoupled import make_oracle_factory, make_learned_factory, _mean_ate


def run_row(name, cfg, args, devo_weights, factory, common):
    """Lance une évaluation (une ligne du tableau) et renvoie (ate_moyen, dict_par_scene)."""
    print(f"\n=== [table] {name} (DEVO={os.path.basename(devo_weights)}) ===")
    args.expname = "central_" + name.replace(" ", "_").replace("(", "").replace(")", "")
    res, _ = evaluate(cfg, args, devo_weights, dyn_mask_provider_factory=factory, **common)
    return _mean_ate(res), res


def write_table(rows, outdir):
    """rows: list de (nom, ate_moyen_ou_None). Écrit central_table.md et .csv."""
    os.makedirs(outdir, exist_ok=True)
    md = os.path.join(outdir, "central_table.md")
    csvp = os.path.join(outdir, "central_table.csv")

    base = next((a for n, a in rows if n == "DEVO vanilla" and a is not None), None)
    with open(md, "w") as f:
        f.write("| Configuration | ATE moyen | Δ vs vanilla |\n|---|---|---|\n")
        for name, ate in rows:
            if ate is None:
                f.write(f"| {name} | — | — |\n")
            else:
                delta = "" if base is None else f"{100*(base-ate)/base:+.1f}%"
                f.write(f"| {name} | {ate:.4f} | {delta} |\n")
    with open(csvp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["config", "ate_mean", "delta_pct_vs_vanilla"])
        for name, ate in rows:
            delta = "" if (ate is None or base is None) else f"{100*(base-ate)/base:.2f}"
            w.writerow([name, "" if ate is None else f"{ate:.6f}", delta])
    print(f"\n[table] écrit -> {md}\n[table] écrit -> {csvp}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('--config', default="config/eval_evimo.yaml")
    p.add_argument('--datapath', required=True)
    p.add_argument('--val_split', default="splits/evimo/evimo_val.txt")
    p.add_argument('--mask_root', required=True, help='racine npz EVIMO (events/ts + GT oracle)')
    p.add_argument('--ms_config', required=True, help='yaml archi du modèle MS (commun aux MS ckpts)')
    # checkpoint DEVO vanilla (obligatoire) + variantes DEVO fine-tunées (optionnelles)
    p.add_argument('--weights', required=True, help='DEVO vanilla (.pth)')
    p.add_argument('--devo_coupled_sup', default=None, help='DEVO fine-tuné couplé M2 (optionnel)')
    p.add_argument('--devo_coupled_selfsup', default=None, help='DEVO fine-tuné couplé M3 (optionnel)')
    # checkpoints MS (chaque ligne dispo si son ckpt est fourni)
    p.add_argument('--ms_decoupled', default=None, help='convlstm entraîné séparément (M1)')
    p.add_argument('--ms_coupled_sup', default=None, help='MS fine-tuné couplé supervisé (M2)')
    p.add_argument('--ms_coupled_selfsup', default=None, help='MS fine-tuné couplé auto-sup (M3)')
    # options
    p.add_argument('--threshold', type=float, default=None, help='binarisation masque appris')
    p.add_argument('--thicken_radius', type=int, default=2)
    p.add_argument('--trials', type=int, default=1)
    p.add_argument('--stride', type=int, default=1)
    p.add_argument('--outdir', default="results/central_table")
    p.add_argument('--expname', default="central")
    p.add_argument('--seed', type=int, default=1234,
                   help='seed torch pour la variance eval (DEVO fait torch.rand_like pour depth init)')
    args = p.parse_args()
    assert_eval_config(args)

    cfg.merge_from_file(args.config)
    torch.manual_seed(args.seed)
    import numpy as np, random
    np.random.seed(args.seed); random.seed(args.seed)
    print(f"[central_table] seed torch/numpy/random = {args.seed}", flush=True)
    args.plot = False
    args.save_trajectory = True
    common = dict(datapath=args.datapath, split_file=args.val_split,
                  trials=args.trials, plot=False, save=True, stride=args.stride)

    def learned(ms_weights):
        return make_learned_factory(args.mask_root, ms_weights, args.ms_config, threshold=args.threshold)

    rows = []
    # 1) vanilla
    rows.append(("DEVO vanilla",
                 run_row("DEVO vanilla", cfg, args, args.weights, None, common)[0]))
    # 2) oracle (plafond)
    rows.append(("DEVO + oracle GT",
                 run_row("DEVO + oracle GT", cfg, args, args.weights,
                         make_oracle_factory(args.mask_root, thicken_radius=args.thicken_radius), common)[0]))
    # 3) appris découplé (M1)
    if args.ms_decoupled:
        rows.append(("DEVO + appris découplé (M1)",
                     run_row("DEVO + appris découplé (M1)", cfg, args, args.weights,
                             learned(args.ms_decoupled), common)[0]))
    else:
        rows.append(("DEVO + appris découplé (M1)", None))
    # 4) couplé supervisé (M2)
    if args.ms_coupled_sup:
        rows.append(("DEVO + couplé supervisé (M2)",
                     run_row("DEVO + couplé supervisé (M2)", cfg, args,
                             args.devo_coupled_sup or args.weights,
                             learned(args.ms_coupled_sup), common)[0]))
    else:
        rows.append(("DEVO + couplé supervisé (M2)", None))
    # 5) couplé auto-sup (M3)
    if args.ms_coupled_selfsup:
        rows.append(("DEVO + couplé auto-sup (M3)",
                     run_row("DEVO + couplé auto-sup (M3)", cfg, args,
                             args.devo_coupled_selfsup or args.weights,
                             learned(args.ms_coupled_selfsup), common)[0]))
    else:
        rows.append(("DEVO + couplé auto-sup (M3)", None))

    print("\n==================== TABLEAU CENTRAL ====================")
    for name, ate in rows:
        print(f"  {name:32s}: {'—' if ate is None else f'{ate:.4f}'}")
    write_table(rows, args.outdir)
