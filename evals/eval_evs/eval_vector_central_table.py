"""Tableau central DEVO sur VECtor (Vanilla / M1 / M2 / M3).
Note : résolution 480×640, différente du training EVIMO (260×346).
"""
import os
import csv
import argparse

import torch
from devo.config import cfg
from utils.eval_utils import assert_eval_config
from utils.ms_dataset_factory import make_ms_factory, _mean_ate

from eval_vector_evs import evaluate


def run_row(name, cfg, args, devo_weights, factory, common):
    print(f"\n=== [vector-table] {name} ===")
    args.expname = "central_" + name.replace(" ", "_").replace("(", "").replace(")", "")
    res, _ = evaluate(cfg, args, devo_weights, dyn_mask_provider_factory=factory, **common)
    return _mean_ate(res), res


def write_table(rows, outdir):
    os.makedirs(outdir, exist_ok=True)
    base = next((a for n, a in rows if n == "DEVO vanilla" and a is not None), None)
    with open(os.path.join(outdir, "central_table.md"), "w") as f:
        f.write("| Configuration | ATE moyen | Δ vs vanilla |\n|---|---|---|\n")
        for name, ate in rows:
            delta = "" if (ate is None or base is None) else f"{100*(base-ate)/base:+.1f}%"
            f.write(f"| {name} | {'—' if ate is None else f'{ate:.4f}'} | {delta} |\n")
    with open(os.path.join(outdir, "central_table.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["config", "ate_mean", "delta_pct_vs_vanilla"])
        for name, ate in rows:
            delta = "" if (ate is None or base is None) else f"{100*(base-ate)/base:.2f}"
            w.writerow([name, "" if ate is None else f"{ate:.6f}", delta])
    print(f"[vector-table] → {outdir}/central_table.md")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('--config', default="config/eval_vector.yaml")
    p.add_argument('--datapath', required=True)
    p.add_argument('--val_split', default="splits/vector/vector_val.txt")
    p.add_argument('--weights', required=True)
    p.add_argument('--ms_config', required=True)
    p.add_argument('--ms_decoupled', default=None)
    p.add_argument('--ms_coupled_sup', default=None)
    p.add_argument('--ms_coupled_selfsup', default=None)
    p.add_argument('--devo_coupled_sup', default=None)
    p.add_argument('--devo_coupled_selfsup', default=None)
    p.add_argument('--side', default="left")
    p.add_argument('--threshold', type=float, default=None)
    p.add_argument('--trials', type=int, default=1)
    p.add_argument('--stride', type=int, default=1)
    p.add_argument('--outdir', default="results/vector_central_table")
    p.add_argument('--expname', default="central")
    p.add_argument('--seed', type=int, default=1234)
    args = p.parse_args()
    assert_eval_config(args)

    cfg.merge_from_file(args.config)
    torch.manual_seed(args.seed)
    args.plot = False
    args.save_trajectory = True
    common = dict(datapath=args.datapath, split_file=args.val_split,
                  trials=args.trials, plot=False, save=True, stride=args.stride,
                  side=args.side)

    def ms_factory(weights):
        return make_ms_factory("vector", weights, args.ms_config,
                               side=args.side, threshold=args.threshold)

    rows = [("DEVO vanilla", run_row("DEVO vanilla", cfg, args, args.weights, None, common)[0])]
    rows.append(("DEVO + M1 (découplé)", run_row("DEVO + M1 (découplé)", cfg, args, args.weights,
                 ms_factory(args.ms_decoupled), common)[0] if args.ms_decoupled else None))
    rows.append(("DEVO + M2 (couplé sup)", run_row("DEVO + M2 (couplé sup)", cfg, args,
                 args.devo_coupled_sup or args.weights, ms_factory(args.ms_coupled_sup), common)[0] if args.ms_coupled_sup else None))
    rows.append(("DEVO + M3 (couplé auto-sup)", run_row("DEVO + M3 (couplé auto-sup)", cfg, args,
                 args.devo_coupled_selfsup or args.weights, ms_factory(args.ms_coupled_selfsup), common)[0] if args.ms_coupled_selfsup else None))

    print("\n==================== TABLEAU VECtor ====================")
    for name, ate in rows:
        print(f"  {name:35s}: {'—' if ate is None else f'{ate:.4f}'}")
    write_table(rows, args.outdir)
