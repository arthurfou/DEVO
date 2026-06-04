"""
reeval_se3.py — Recalcule les erreurs de rotation avec align_type=se3 / align_num_frames=1.

Sans argument : traite tous les runs dans results/evimo_evs/.
Avec --runs : traite seulement les runs spécifiés.

Usage:
    conda run -n devofou python scripts/reeval_se3.py
    conda run -n devofou python scripts/reeval_se3.py --runs results/evimo_evs/2026-06-03_original
"""

import os
import sys
import glob
import yaml
import argparse
import re
import numpy as np
from natsort import natsorted
from tabulate import tabulate

DEVO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RPG_SCRIPT = os.path.join(
    DEVO_ROOT, "thirdparty/rpg_trajectory_evaluation/scripts/analyze_trajectory_single.py"
)

EVAL_CFG = {"align_type": "se3", "align_num_frames": 1}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def scene_from_folder(folder):
    """'Box_Raw_Seq_00_trial_0_step_DEVO' → 'Box_Raw_Seq_00'"""
    return re.sub(r"_trial_\d+_step_.*", "", os.path.basename(folder))


def trial_from_folder(folder):
    """'Box_Raw_Seq_00_trial_2_step_DEVO' → 2"""
    m = re.search(r"_trial_(\d+)_step_", os.path.basename(folder))
    return int(m.group(1)) if m else 0


def find_trial_folders(run_dir):
    """Return sorted list of trial folders inside run_dir."""
    pattern = os.path.join(run_dir, "*_trial_*_step_*")
    folders = [f for f in glob.glob(pattern) if os.path.isdir(f)]
    return natsorted(folders)


def compute_traj_length(gt_file):
    """Trajectory length in metres from stamped_groundtruth.txt."""
    data = np.loadtxt(gt_file, comments="#")
    if data.ndim == 1 or data.shape[0] < 2:
        return 1.0  # avoid division by zero
    pos = data[:, 1:4]
    return float(np.sum(np.linalg.norm(np.diff(pos, axis=0), axis=1)))


def load_stats(folder):
    """Load the (only) absolute_err_statistics_*.yaml present."""
    rpg_path = os.path.join(folder, "saved_results", "traj_est")
    files = natsorted(glob.glob(os.path.join(rpg_path, "absolute_err_stat*.yaml")))
    if not files:
        return None
    with open(files[-1]) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Per-folder processing
# ---------------------------------------------------------------------------

def process_folder(folder, dry_run=False):
    """Place eval_cfg.yaml, remove old sim3 stats, re-run RPG eval."""

    # 1. Write eval_cfg.yaml
    cfg_path = os.path.join(folder, "eval_cfg.yaml")
    with open(cfg_path, "w") as f:
        yaml.dump(EVAL_CFG, f, default_flow_style=False)

    # 2. Remove old sim3 absolute stats (so natsorted[-1] picks the new se3 one)
    rpg_path = os.path.join(folder, "saved_results", "traj_est")
    for old in glob.glob(os.path.join(rpg_path, "absolute_err_statistics_sim3*.yaml")):
        if not dry_run:
            os.remove(old)
        else:
            print(f"  [dry] would delete {old}")

    if dry_run:
        return None

    # 3. Re-run RPG trajectory evaluation
    cmd = (
        f"python {RPG_SCRIPT} {folder} "
        f"--recalculate_errors --png --plot 2>/dev/null"
    )
    ret = os.system(cmd)
    if ret != 0:
        print(f"  [WARN] RPG eval failed for {folder}")
        return None

    return load_stats(folder)


# ---------------------------------------------------------------------------
# 0_res_se3.txt generation
# ---------------------------------------------------------------------------

def generate_res_file(run_dir, results):
    """
    results: dict  scene -> list of (trial_idx, stats_dict)
    Writes 0_res_se3.txt in run_dir.
    """
    out_path = os.path.join(run_dir, "0_res_se3.txt")

    with open(out_path, "w") as f:
        for scene in natsorted(results.keys()):
            trials = sorted(results[scene], key=lambda t: t[0])
            # header (only once per scene)
            f.write("\n")
            f.write(
                f"Scene           ATE[cm]  R_rmse_se3[deg]  MPE[%/m]  \\\\\n"
            )
            for trial_idx, stats, mpe in trials:
                ate_cm = stats["trans"]["rmse"] * 100
                r_rmse = stats["rot"]["rmse"]
                f.write(
                    f"{scene}  {ate_cm:.3f}    {r_rmse:.3f}              "
                    f"{mpe:.3f}     \\\\\n"
                )

    print(f"  → {out_path}")
    return out_path


def print_comparison(run_dir, results, old_res_path):
    """Print a table comparing sim3 R_rmse vs se3 R_rmse."""

    # Parse old 0_res.txt
    old_r = {}  # scene -> list of R_rmse values
    if os.path.exists(old_res_path):
        with open(old_res_path) as f:
            lines = f.readlines()
        i = 0
        while i < len(lines):
            if lines[i].strip().startswith("Scene"):
                i += 1
                if i < len(lines):
                    parts = lines[i].strip().split()
                    if len(parts) >= 3:
                        old_r.setdefault(parts[0], []).append(float(parts[2]))
            i += 1

    rows = []
    for scene in natsorted(results.keys()):
        trials = sorted(results[scene], key=lambda t: t[0])
        new_r_vals = [stats["rot"]["rmse"] for _, stats, _ in trials]
        old_r_vals = old_r.get(scene, [])

        med_new = np.median(new_r_vals)
        med_old = np.median(old_r_vals) if old_r_vals else float("nan")
        rows.append([scene, f"{med_old:.1f}°", f"{med_new:.1f}°",
                     f"{med_new - med_old:+.1f}°" if not np.isnan(med_old) else "?"])

    print(f"\n{'='*60}")
    print(f"  Run : {run_dir}")
    print(f"{'='*60}")
    print(tabulate(rows,
                   headers=["Séquence", "R_rmse sim3 [°]", "R_rmse se3 [°]", "Δ"],
                   tablefmt="simple"))
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def process_run(run_dir, dry_run=False):
    trial_folders = find_trial_folders(run_dir)
    if not trial_folders:
        print(f"  Aucun dossier trial trouvé dans {run_dir}")
        return

    print(f"\nTraitement de {run_dir} ({len(trial_folders)} trial(s))...")

    results = {}  # scene -> [(trial_idx, stats, mpe)]

    for folder in trial_folders:
        scene = scene_from_folder(folder)
        trial_idx = trial_from_folder(folder)
        print(f"  {os.path.basename(folder)}")

        stats = process_folder(folder, dry_run=dry_run)

        if not dry_run and stats is not None:
            gt_file = os.path.join(folder, "stamped_groundtruth.txt")
            traj_len = compute_traj_length(gt_file) if os.path.exists(gt_file) else 1.0
            mpe = stats["trans"]["mean"] / traj_len * 100
            results.setdefault(scene, []).append((trial_idx, stats, mpe))

    if not dry_run and results:
        out_path = generate_res_file(run_dir, results)
        print_comparison(run_dir, results, os.path.join(run_dir, "0_res.txt"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs", nargs="*",
        help="Chemins des runs à traiter (défaut : tous dans results/evimo_evs/)"
    )
    parser.add_argument(
        "--dry_run", action="store_true",
        help="Affiche ce qui serait fait sans modifier les fichiers"
    )
    args = parser.parse_args()

    if args.runs:
        run_dirs = [os.path.abspath(r) for r in args.runs]
    else:
        base = os.path.join(DEVO_ROOT, "results", "evimo_evs")
        run_dirs = natsorted([
            d for d in glob.glob(os.path.join(base, "*"))
            if os.path.isdir(d)
        ])

    if not run_dirs:
        print("Aucun run trouvé.")
        sys.exit(1)

    print(f"Runs à traiter : {[os.path.basename(r) for r in run_dirs]}")

    for run_dir in run_dirs:
        process_run(run_dir, dry_run=args.dry_run)

    print("\nTerminé.")


if __name__ == "__main__":
    main()
