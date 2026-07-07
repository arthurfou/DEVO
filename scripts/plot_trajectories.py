"""
Visualise les trajectoires 3D estimées par DEVO pour un run RPG donné.
Compare optionnellement avec le ground truth.

Usage :
    python scripts/plot_trajectories.py --rundir results/rpg_evs/2026-07-06_map_test
    python scripts/plot_trajectories.py --rundir results/rpg_evs/2026-07-06_map_test \
                                        --datapath /path/to/rpg/rpg_dataset
"""

import os
import glob
import argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401


def load_tum(path):
    data = np.loadtxt(path)
    if data.ndim == 1:
        data = data[np.newaxis, :]
    return data[:, 1:4]  # tx ty tz


def find_scene_dirs(rundir):
    return sorted([
        d for d in glob.glob(os.path.join(rundir, "*_trial_*"))
        if os.path.isdir(d)
    ])


def find_est_traj(scene_dir):
    txts = glob.glob(os.path.join(scene_dir, "*_Trial*.txt"))
    return txts[0] if txts else None


def find_gt_traj(scene_dir, datapath, side="left"):
    scene_name = os.path.basename(scene_dir).split("_trial_")[0].lower()
    if datapath is None:
        return None
    gt = os.path.join(datapath, scene_name, f"gt_stamped_{side}.txt")
    return gt if os.path.exists(gt) else None


def align_to_origin(pts):
    return pts - pts[0]


def plot_all(rundir, datapath, side, save):
    scene_dirs = find_scene_dirs(rundir)
    if not scene_dirs:
        print(f"Aucun dossier de scène trouvé dans {rundir}")
        return

    n = len(scene_dirs)
    ncols = min(3, n)
    nrows = (n + ncols - 1) // ncols

    fig = plt.figure(figsize=(6 * ncols, 5 * nrows))
    fig.suptitle(os.path.basename(rundir), fontsize=13, fontweight="bold")

    for i, scene_dir in enumerate(scene_dirs):
        scene_name = os.path.basename(scene_dir).split("_trial_")[0]
        ax = fig.add_subplot(nrows, ncols, i + 1, projection="3d")
        ax.set_title(scene_name, fontsize=10)

        est_path = find_est_traj(scene_dir)
        if est_path is None:
            ax.text(0.5, 0.5, 0.5, "no data", transform=ax.transAxes, ha="center")
            continue

        est = align_to_origin(load_tum(est_path))
        ax.plot(est[:, 0], est[:, 1], est[:, 2], color="royalblue", linewidth=1.5, label="DEVO")
        ax.scatter(*est[0], color="green", s=40, zorder=5, label="start")
        ax.scatter(*est[-1], color="red", s=40, zorder=5, label="end")

        gt_path = find_gt_traj(scene_dir, datapath, side)
        if gt_path:
            gt = align_to_origin(load_tum(gt_path))
            ax.plot(gt[:, 0], gt[:, 1], gt[:, 2], color="darkorange",
                    linewidth=1.0, linestyle="--", label="GT")

        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_zlabel("z")
        ax.legend(fontsize=7)

    plt.tight_layout()

    if save:
        outpath = os.path.join(rundir, "trajectories.png")
        fig.savefig(outpath, dpi=150, bbox_inches="tight")
        print(f"Figure sauvegardée -> {outpath}")
    else:
        plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rundir", required=True, help="Dossier d'un run (ex: results/rpg_evs/2026-07-06_map_test)")
    parser.add_argument("--datapath", default=None, help="Chemin vers rpg_dataset pour afficher le GT")
    parser.add_argument("--side", default="left", choices=["left", "right"])
    parser.add_argument("--no-save", action="store_true", help="Affiche au lieu de sauvegarder")
    args = parser.parse_args()

    plot_all(args.rundir, args.datapath, args.side, save=not args.no_save)
