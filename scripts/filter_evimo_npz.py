"""
Filter EVIMO event stream using pre-computed pixel-wise object masks from NPZ files.

All data is derived from EV-IMO alone (NPZ + raw files). No dependency on pre-existing
preprocessed files.

Output per sequence (EV-IMO_filtered/eval/<cat>/raw/<seq>/):
  evs.npy          - filtered events, float64 (N, 4): [ts_us, x, y, p]
  gt_stamped.txt   - camera GT poses at 200 Hz: ts_us tx ty tz qx qy qz qw
  tss_imgs_us.txt  - frame timestamps at ~40 Hz (used for voxel slicing)
  rectify_map.h5   - undistortion/rectification map
  calib.txt        - copied from EV-IMO raw
  extrinsics.txt   - copied from EV-IMO raw
  config.txt       - copied from EV-IMO raw

Usage:
  python scripts/filter_evimo_npz.py \
      --datapath /path/to/EV-IMO/eval \
      --outpath  /path/to/EV-IMO_filtered/eval \
      [--dry_run]
"""

import os
import glob
import json
import shutil
import argparse
import numpy as np
import cv2
import h5py

H, W = 260, 346


def compute_rectify_map(K, D):
    dist = D.copy()
    if len(dist) == 4:
        dist = np.append(dist, 0.0)
    K_new, _ = cv2.getOptimalNewCameraMatrix(K, dist, (W, H), alpha=0, newImgSize=(W, H))
    coords = np.stack(np.meshgrid(np.arange(W), np.arange(H))).reshape((2, -1)).astype("float32")
    criteria = (cv2.TERM_CRITERIA_MAX_ITER | cv2.TERM_CRITERIA_EPS, 100, 0.001)
    pts = cv2.undistortPointsIter(coords, K, dist, np.eye(3), K_new, criteria=criteria)
    return pts.reshape((H, W, 2))


def build_gt_stamped(full_trajectory):
    rows = []
    for entry in full_trajectory:
        ts_us = entry['ts'] * 1e6
        t = entry['cam']['pos']['t']
        q = entry['cam']['pos']['q']
        rows.append([ts_us, t['x'], t['y'], t['z'], q['x'], q['y'], q['z'], q['w']])
    arr = np.array(rows, dtype=np.float64)
    return arr[np.argsort(arr[:, 0])]


def process_sequence(seq_rel, datapath, outpath, dry_run=False):
    # seq_rel = 'fast/raw/seq_00'  →  category='fast', seq_name='seq_00'
    parts = seq_rel.split('/')
    category, _, seq_name = parts

    npz_path = os.path.join(datapath, category, 'npz', seq_name + '.npz')
    raw_dir  = os.path.join(datapath, seq_rel)
    out_dir  = os.path.join(outpath, seq_rel)

    if not os.path.exists(npz_path):
        print(f"  WARNING: NPZ not found at {npz_path}, skipping")
        return None

    npz  = np.load(npz_path, allow_pickle=True)
    meta = npz['meta'].item()

    evs_npz = npz['events']   # float32 (N, 4): [t_sec, x, y, polarity]
    masks   = npz['mask']     # float64 (F, H, W): 0=background, N*1000=object N
    K = npz['K'].astype(np.float64)
    D = npz['D'].astype(np.float64)

    frames    = meta['frames']
    full_traj = meta['full_trajectory']

    frame_ts_us = np.array([f['ts'] for f in frames], dtype=np.float64) * 1e6

    # Convert events to float64 µs (same relative time base as frame timestamps)
    evs = evs_npz.astype(np.float64)
    evs[:, 0] *= 1e6

    n_before = len(evs)

    # For each event, find the nearest mask frame by timestamp
    idx   = np.searchsorted(frame_ts_us, evs[:, 0])
    idx_l = np.clip(idx - 1, 0, len(masks) - 1)
    idx_r = np.clip(idx,     0, len(masks) - 1)
    dist_l = np.abs(frame_ts_us[idx_l] - evs[:, 0])
    dist_r = np.abs(frame_ts_us[idx_r] - evs[:, 0])
    nearest = np.where(dist_l <= dist_r, idx_l, idx_r)

    ev_x = np.clip(evs[:, 1].astype(np.int32), 0, W - 1)
    ev_y = np.clip(evs[:, 2].astype(np.int32), 0, H - 1)

    # Keep events where mask is 0 (background)
    keep         = masks[nearest, ev_y, ev_x] == 0
    evs_filtered = evs[keep]

    n_removed    = n_before - len(evs_filtered)
    pct_removed  = 100.0 * n_removed / n_before if n_before > 0 else 0.0
    mask_cov_pct = 100.0 * float((masks > 0).mean())

    stats = {
        'n_before':          int(n_before),
        'n_removed':         int(n_removed),
        'pct_removed':       round(pct_removed, 3),
        'mask_coverage_pct': round(mask_cov_pct, 3),
    }
    print(f"  {n_before:,} events → {n_removed:,} removed ({pct_removed:.2f}%),  mask_cov={mask_cov_pct:.2f}%")

    if dry_run:
        return stats

    os.makedirs(out_dir, exist_ok=True)

    # evs.npy — filtered events
    np.save(os.path.join(out_dir, 'evs.npy'), evs_filtered)

    # gt_stamped.txt — camera poses from full_trajectory
    gt = build_gt_stamped(full_traj)
    np.savetxt(os.path.join(out_dir, 'gt_stamped.txt'), gt, fmt='%.6f', delimiter=' ',
               header='timestamp[us] tx ty tz qx qy qz qw')

    # tss_imgs_us.txt — GT frame timestamps used as voxel time boundaries
    np.savetxt(os.path.join(out_dir, 'tss_imgs_us.txt'), frame_ts_us, fmt='%.3f')

    # rectify_map.h5 — undistortion map from NPZ intrinsics
    rmap = compute_rectify_map(K, D)
    with h5py.File(os.path.join(out_dir, 'rectify_map.h5'), 'w') as hf:
        hf.create_dataset('rectify_map', data=rmap.astype(np.float32))

    # Copy static config files from EV-IMO raw dir
    for fname in ['calib.txt', 'extrinsics.txt', 'config.txt']:
        src = os.path.join(raw_dir, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(out_dir, fname))

    return stats


def main():
    parser = argparse.ArgumentParser(description='Filter EVIMO events using NPZ object masks')
    parser.add_argument('--datapath', required=True, help='Path to EV-IMO/eval')
    parser.add_argument('--outpath',  required=True, help='Output path for filtered dataset')
    parser.add_argument('--dry_run',  action='store_true', help='Compute stats without writing files')
    args = parser.parse_args()

    seqdirs = sorted(glob.glob(os.path.join(args.datapath, '*/raw/seq_*')))
    if not seqdirs:
        print(f'No sequences found under {args.datapath}')
        return

    print(f'Found {len(seqdirs)} sequences')
    if args.dry_run:
        print('DRY RUN — no files will be written\n')

    all_stats = {}
    for seqdir in seqdirs:
        seq_rel = os.path.relpath(seqdir, args.datapath)
        print(f'\nSequence: {seq_rel}')
        try:
            stats = process_sequence(seq_rel, args.datapath, args.outpath, dry_run=args.dry_run)
            if stats is not None:
                all_stats[seq_rel] = stats
        except Exception as e:
            import traceback
            print(f'  ERROR: {e}')
            traceback.print_exc()

    if not all_stats:
        print('\nNo sequences processed.')
        return

    total_before  = sum(s['n_before']  for s in all_stats.values())
    total_removed = sum(s['n_removed'] for s in all_stats.values())
    total_pct     = 100.0 * total_removed / total_before if total_before > 0 else 0.0
    print(f'\nTOTAL: {total_before:,} events, {total_removed:,} removed ({total_pct:.3f}%)')

    if not args.dry_run:
        all_stats['TOTAL'] = {
            'n_before':    total_before,
            'n_removed':   total_removed,
            'pct_removed': round(total_pct, 3),
        }
        os.makedirs(args.outpath, exist_ok=True)
        stats_path = os.path.join(args.outpath, 'filter_stats.json')
        with open(stats_path, 'w') as f:
            json.dump(all_stats, f, indent=2)
        print(f'Stats → {stats_path}')

    print('\nDone.')


if __name__ == '__main__':
    main()
