"""
compare_evimo_runs.py

Compare two DEVO eval runs (e.g. original vs filtered dataset) by reading
their 0_res.txt files and computing median ± std per scene across trials.

Usage:
    python scripts/compare_evimo_runs.py \
        --run_a results/evimo_evs/2026-06-03_original_5trials \
        --run_b results/evimo_evs/2026-06-03_filtered_2805_5trials \
        --name_a "Original" \
        --name_b "Filtré 2805"
"""

import argparse
import os
import re
import numpy as np


def parse_res_file(path):
    """
    Parse 0_res.txt → dict {scene_name: [ate1, ate2, ...]}

    File format (one block per trial per scene):
        Scene           ATE[cm]  R_rmse[deg]  MPE[%/m]  \\
        Box_Raw_Seq_00  3.203    102.06        2.25      \\
    """
    results = {}
    with open(path) as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Header line: starts with "Scene"
        if line.startswith("Scene"):
            i += 1
            if i >= len(lines):
                break
            data_line = lines[i].strip()
            # Parse: SceneName  ATE  R_rmse  MPE  \\
            parts = data_line.split()
            if len(parts) >= 2:
                scene = parts[0]
                try:
                    ate = float(parts[1])
                    results.setdefault(scene, []).append(ate)
                except ValueError:
                    pass
        i += 1

    return results


def scene_to_label(scene):
    """Convert Box_Raw_Seq_00 → box/raw/seq_00"""
    parts = scene.split("_")
    # Find "Raw" and "Seq" positions
    try:
        raw_idx = next(i for i, p in enumerate(parts) if p.lower() == "raw")
        category = "_".join(parts[:raw_idx]).lower()
        seq_part = "_".join(parts[raw_idx:]).lower()
        return f"{category}/{seq_part}"
    except StopIteration:
        return scene.lower()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_a", required=True, help="Path to first run folder")
    parser.add_argument("--run_b", required=True, help="Path to second run folder")
    parser.add_argument("--name_a", default="Run A")
    parser.add_argument("--name_b", default="Run B")
    args = parser.parse_args()

    res_a_path = os.path.join(args.run_a, "0_res.txt")
    res_b_path = os.path.join(args.run_b, "0_res.txt")

    for p in [res_a_path, res_b_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Not found: {p}")

    data_a = parse_res_file(res_a_path)
    data_b = parse_res_file(res_b_path)

    scenes_a = set(data_a.keys())
    scenes_b = set(data_b.keys())
    common = sorted(scenes_a & scenes_b)

    if not common:
        print("No common scenes found between the two runs.")
        return

    n_trials_a = len(next(iter(data_a.values())))
    n_trials_b = len(next(iter(data_b.values())))

    print(f"\n{'='*78}")
    print(f"  {args.name_a} ({n_trials_a} trials)  vs  {args.name_b} ({n_trials_b} trials)")
    print(f"{'='*78}")
    print(f"  Run A : {args.run_a}")
    print(f"  Run B : {args.run_b}")
    print(f"{'='*78}\n")

    col_scene = 24
    col_val   = 20
    header = (f"{'Séquence':<{col_scene}}"
              f"{'ATE '+args.name_a+' [cm]':>{col_val}}"
              f"{'ATE '+args.name_b+' [cm]':>{col_val}}"
              f"{'Δ (B-A)':>12}"
              f"  {''}")
    print(header)
    print("-" * (col_scene + col_val * 2 + 16))

    medians_a, medians_b, deltas = [], [], []

    for scene in common:
        vals_a = np.array(data_a[scene])
        vals_b = np.array(data_b[scene])

        med_a, std_a = np.median(vals_a), np.std(vals_a)
        med_b, std_b = np.median(vals_b), np.std(vals_b)
        delta = med_b - med_a

        medians_a.append(med_a)
        medians_b.append(med_b)
        deltas.append(delta)

        label = scene_to_label(scene)
        indicator = "✓" if delta < -0.05 * med_a else ("✗" if delta > 0.05 * med_a else "~")

        str_a = f"{med_a:5.2f} ± {std_a:4.2f}"
        str_b = f"{med_b:5.2f} ± {std_b:4.2f}"
        str_d = f"{delta:+.2f}"

        print(f"  {label:<{col_scene-2}}{str_a:>{col_val}}{str_b:>{col_val}}{str_d:>12}  {indicator}")

    print("-" * (col_scene + col_val * 2 + 16))
    global_med_a = np.median(medians_a)
    global_med_b = np.median(medians_b)
    global_delta = global_med_b - global_med_a
    indicator = "✓" if global_delta < 0 else "✗"

    print(f"  {'MÉDIANE GLOBALE':<{col_scene-2}}"
          f"{global_med_a:>{col_val}.2f}"
          f"{global_med_b:>{col_val}.2f}"
          f"{global_delta:>+12.2f}  {indicator}")
    print(f"\n  Légende : ✓ = B meilleur (Δ < -5%)  ~ = équivalent  ✗ = B moins bon (Δ > +5%)\n")

    # Also print scenes only in one run
    only_a = scenes_a - scenes_b
    only_b = scenes_b - scenes_a
    if only_a:
        print(f"  Scènes uniquement dans {args.name_a} : {', '.join(sorted(only_a))}")
    if only_b:
        print(f"  Scènes uniquement dans {args.name_b} : {', '.join(sorted(only_b))}")


if __name__ == "__main__":
    main()
