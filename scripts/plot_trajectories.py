"""
Visualise les trajectoires 3D estimées par DEVO pour un run RPG donné.
Compare optionnellement avec le ground truth.

Usage :
    # PNG (image 2D)
    python scripts/plot_trajectories.py --rundir results/rpg_evs/2026-07-06_map_test

    # PLY (navigable en 3D dans MeshLab), avec alignement Sim3 si GT disponible
    python scripts/plot_trajectories.py --rundir results/rpg_evs/2026-07-06_map_test --ply

    # Les deux + GT
    python scripts/plot_trajectories.py --rundir results/rpg_evs/2026-07-06_map_test \
                                        --datapath /path/to/rpg/rpg_dataset --ply
"""

import os
import copy
import glob
import struct
import argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

from evo.core.trajectory import PoseTrajectory3D
from evo.core import sync


def load_tum(path):
    """Charge un fichier TUM : timestamp tx ty tz qx qy qz qw"""
    data = np.loadtxt(path)
    if data.ndim == 1:
        data = data[np.newaxis, :]
    return data  # (N, 8)


def make_evo_traj(data):
    """Crée un objet PoseTrajectory3D depuis les données TUM brutes (timestamps en µs)."""
    tss_s = data[:, 0] / 1e6  # µs → s
    xyz = data[:, 1:4]
    # DEVO stocke les quaternions en xyzw, evo attend wxyz
    quat_xyzw = data[:, 4:8]
    quat_wxyz = np.roll(quat_xyzw, shift=1, axis=1)
    return PoseTrajectory3D(positions_xyz=xyz, orientations_quat_wxyz=quat_wxyz, timestamps=tss_s)


def sim3_align(est_data, gt_data):
    """
    Aligne la trajectoire estimée sur le GT via Sim3 (rotation + translation + échelle).
    Retourne les positions alignées de est et les positions du GT synchronisées.
    """
    traj_est = make_evo_traj(est_data)
    traj_gt = make_evo_traj(gt_data)

    traj_gt_sync, traj_est_sync = sync.associate_trajectories(traj_gt, traj_est, max_diff=0.1)

    traj_est_aligned = copy.deepcopy(traj_est_sync)
    traj_est_aligned.align(traj_gt_sync, correct_scale=True)

    return traj_est_aligned.positions_xyz, traj_gt_sync.positions_xyz


def find_scene_dirs(rundir):
    return sorted([
        d for d in glob.glob(os.path.join(rundir, "*_trial_*"))
        if os.path.isdir(d)
    ])


def find_est_traj(scene_dir):
    txts = glob.glob(os.path.join(scene_dir, "*_Trial*.txt"))
    return txts[0] if txts else None


def find_gt_traj(scene_dir, datapath, side="left", dataset="rpg"):
    scene_name = os.path.basename(scene_dir).split("_trial_")[0].lower()
    if datapath is None:
        return None
    if dataset == "evimo":
        # Box_Raw_Seq_00 -> box/raw/seq_00
        scene_path = scene_name.replace("_raw_", "/raw/").replace("_seq_", "/seq_")
        gt = os.path.join(datapath, scene_path, "gt_stamped.txt")
    else:
        gt = os.path.join(datapath, scene_name, f"gt_stamped_{side}.txt")
    return gt if os.path.exists(gt) else None


def write_ply_polylines(path, trajectories):
    """
    Écrit plusieurs trajectoires dans un seul PLY (vertices + edges).
    trajectories : liste de (pts, (r, g, b))
    """
    total_verts = sum(len(pts) for pts, _ in trajectories)
    total_edges = sum(len(pts) - 1 for pts, _ in trajectories)
    header = (
        "ply\n"
        "format binary_little_endian 1.0\n"
        f"element vertex {total_verts}\n"
        "property float x\n"
        "property float y\n"
        "property float z\n"
        "property uchar red\n"
        "property uchar green\n"
        "property uchar blue\n"
        f"element edge {total_edges}\n"
        "property int vertex1\n"
        "property int vertex2\n"
        "end_header\n"
    )
    with open(path, "wb") as f:
        f.write(header.encode("ascii"))
        for pts, (r, g, b) in trajectories:
            for p in pts:
                f.write(struct.pack("<fffBBB", float(p[0]), float(p[1]), float(p[2]), r, g, b))
        offset = 0
        for pts, _ in trajectories:
            for i in range(len(pts) - 1):
                f.write(struct.pack("<ii", offset + i, offset + i + 1))
            offset += len(pts)


def export_ply(rundir, datapath, side, dataset="rpg"):
    scene_dirs = find_scene_dirs(rundir)
    for scene_dir in scene_dirs:
        scene_name = os.path.basename(scene_dir).split("_trial_")[0]

        est_path = find_est_traj(scene_dir)
        if est_path is None:
            continue

        est_data = load_tum(est_path)
        gt_path = find_gt_traj(scene_dir, datapath, side, dataset)

        if gt_path:
            gt_data = load_tum(gt_path)
            est_pts, gt_pts = sim3_align(est_data, gt_data)
            trajectories = [
                (est_pts, (70, 130, 200)),   # bleu  = DEVO aligné
                (gt_pts,  (220, 120, 30)),   # orange = GT
            ]
            note = "Sim3 aligné"
        else:
            est_pts = est_data[:, 1:4] - est_data[0, 1:4]
            trajectories = [(est_pts, (70, 130, 200))]
            note = "non aligné (pas de GT)"

        out = os.path.join(scene_dir, "trajectory.ply")
        write_ply_polylines(out, trajectories)
        print(f"[{scene_name}] -> {out} ({note})")


def export_png(rundir, datapath, side, dataset="rpg"):
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

        est_data = load_tum(est_path)
        gt_path = find_gt_traj(scene_dir, datapath, side, dataset)

        if gt_path:
            gt_data = load_tum(gt_path)
            est_pts, gt_pts = sim3_align(est_data, gt_data)
            ax.plot(gt_pts[:, 0], gt_pts[:, 1], gt_pts[:, 2], color="darkorange",
                    linewidth=1.0, linestyle="--", label="GT")
        else:
            est_pts = est_data[:, 1:4] - est_data[0, 1:4]

        ax.plot(est_pts[:, 0], est_pts[:, 1], est_pts[:, 2], color="royalblue", linewidth=1.5, label="DEVO")
        ax.scatter(*est_pts[0], color="green", s=40, zorder=5, label="start")
        ax.scatter(*est_pts[-1], color="red", s=40, zorder=5, label="end")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_zlabel("z")
        ax.legend(fontsize=7)

    plt.tight_layout()
    outpath = os.path.join(rundir, "trajectories.png")
    fig.savefig(outpath, dpi=150, bbox_inches="tight")
    print(f"Figure sauvegardée -> {outpath}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rundir", required=True,
                        help="Dossier d'un run (ex: results/rpg_evs/2026-07-06_map_test)")
    parser.add_argument("--datapath", default=None,
                        help="Chemin vers rpg_dataset pour afficher le GT")
    parser.add_argument("--side", default="left", choices=["left", "right"])
    parser.add_argument("--dataset", default="rpg", choices=["rpg", "evimo"],
                        help="Type de dataset pour trouver le GT")
    parser.add_argument("--ply", action="store_true",
                        help="Exporte les trajectoires en PLY (navigable dans MeshLab)")
    args = parser.parse_args()

    if args.ply:
        export_ply(args.rundir, args.datapath, args.side, args.dataset)
    else:
        export_png(args.rundir, args.datapath, args.side, args.dataset)
