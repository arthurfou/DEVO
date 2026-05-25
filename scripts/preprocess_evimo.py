"""
Preprocess EVIMO raw bag files into the format expected by DEVO.

Outputs per sequence:
  evs.npy          - float64 array (N, 4): [ts_us, x, y, p]
  gt_stamped.txt   - [ts_us tx ty tz qx qy qz qw] ground truth poses
  tss_imgs_us.txt  - image timestamps used for voxel slicing
  rectify_map.h5   - undistortion/rectification map

Events are parsed directly from raw ROS1 bytes (no per-event Python loop)
and stored as binary .npy for fast loading.

Usage:
  python scripts/preprocess_evimo.py --datapath /path/to/evimo/eval
"""

import os
import argparse
import glob
import struct
import numpy as np
import cv2
import h5py

from rosbags.rosbag1 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg


H, W = 260, 346  # DVS346 resolution

# ROS1 binary layout for dvs_msgs/Event:
#   uint16 x, uint16 y, uint32 ts.sec, uint32 ts.nsec, uint8 polarity
_EVENT_DTYPE = np.dtype([
    ('x', '<u2'), ('y', '<u2'),
    ('ts_sec', '<u4'), ('ts_nsec', '<u4'),
    ('polarity', 'u1')
])
_EVENT_SIZE = 13  # bytes per event


def _parse_event_array_bytes(data: bytes):
    """Parse dvs_msgs/EventArray from raw ROS1 bytes using numpy — no Python loop."""
    pos = 0
    # Header.seq
    pos += 4
    # Header.stamp (sec + nsec)
    pos += 8
    # Header.frame_id: uint32 len + chars
    frame_id_len = struct.unpack_from('<I', data, pos)[0]
    pos += 4 + frame_id_len
    # height, width (uint32 each)
    pos += 8
    # events array length
    n_events = struct.unpack_from('<I', data, pos)[0]
    pos += 4

    if n_events == 0:
        return None

    raw = np.frombuffer(data, dtype=_EVENT_DTYPE, count=n_events, offset=pos)
    ts_us = raw['ts_sec'].astype(np.float64) * 1e6 + raw['ts_nsec'].astype(np.float64) / 1e3
    return np.column_stack([
        ts_us,
        raw['x'].astype(np.float64),
        raw['y'].astype(np.float64),
        raw['polarity'].astype(np.float64),
    ])


def extract_events_fast(bagpath):
    """Read all events from bag using direct binary parsing — O(n) numpy, no per-event Python."""
    batches = []
    with Reader(bagpath) as reader:
        conns = [c for c in reader.connections if c.topic == '/dvs/events']
        for conn, timestamp, rawdata in reader.messages(connections=conns):
            batch = _parse_event_array_bytes(bytes(rawdata))
            if batch is not None:
                batches.append(batch)
    if not batches:
        return np.empty((0, 4))
    arr = np.vstack(batches)
    return arr[np.argsort(arr[:, 0])]


def load_typestore(bagpath):
    typestore = get_typestore(Stores.ROS1_NOETIC)
    with Reader(bagpath) as reader:
        add_types = {}
        for conn in reader.connections:
            fmt, msgdef = conn.msgdef
            add_types.update(get_types_from_msg(msgdef, conn.msgtype))
        typestore.register(add_types)
    return typestore


def extract_gt(bagpath, typestore):
    rows = []
    with Reader(bagpath) as reader:
        conns = [c for c in reader.connections if c.topic == '/vicon/DVS346']
        for conn, timestamp, rawdata in reader.messages(connections=conns):
            msg = typestore.deserialize_ros1(rawdata, conn.msgtype)
            if msg.occluded:
                continue
            ts_us = msg.header.stamp.sec * 1e6 + msg.header.stamp.nanosec / 1e3
            p, q = msg.position, msg.orientation
            rows.append((ts_us, p.x, p.y, p.z, q.x, q.y, q.z, q.w))
    if not rows:
        return np.empty((0, 8))
    arr = np.array(rows, dtype=np.float64)
    return arr[np.argsort(arr[:, 0])]


def extract_image_timestamps(bagpath, typestore):
    tss = []
    with Reader(bagpath) as reader:
        conns = [c for c in reader.connections if c.topic == '/dvs/image_raw']
        for conn, timestamp, rawdata in reader.messages(connections=conns):
            msg = typestore.deserialize_ros1(rawdata, conn.msgtype)
            ts_us = msg.header.stamp.sec * 1e6 + msg.header.stamp.nanosec / 1e3
            tss.append(ts_us)
    return np.array(sorted(tss), dtype=np.float64)


def compute_rectify_map(calib_path):
    vals = np.loadtxt(calib_path)
    fx, fy, cx, cy = vals[:4]
    dist = vals[4:]
    if len(dist) == 4:
        dist = np.append(dist, 0.0)
    K = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]], dtype=np.float64)
    K_new, _ = cv2.getOptimalNewCameraMatrix(K, dist, (W, H), alpha=0, newImgSize=(W, H))
    coords = np.stack(np.meshgrid(np.arange(W), np.arange(H))).reshape((2, -1)).astype("float32")
    criteria = (cv2.TERM_CRITERIA_MAX_ITER | cv2.TERM_CRITERIA_EPS, 100, 0.001)
    pts = cv2.undistortPointsIter(coords, K, dist, np.eye(3), K_new, criteria=criteria)
    return pts.reshape((H, W, 2)), K_new


def preprocess_sequence(seqdir, typestore):
    bagfiles = glob.glob(os.path.join(seqdir, "*.bag"))
    assert len(bagfiles) == 1
    bagpath = bagfiles[0]
    calib_path = os.path.join(seqdir, "calib.txt")
    sz_mb = os.path.getsize(bagpath) / 1e6
    print(f"  Bag: {os.path.basename(bagpath)} ({sz_mb:.0f} MB)")

    # Events (fast binary parse)
    evs_path = os.path.join(seqdir, "evs.npy")
    if not os.path.exists(evs_path):
        evs = extract_events_fast(bagpath)
        np.save(evs_path, evs)
        print(f"  Saved {len(evs):,} events → {evs_path}")
    else:
        print(f"  evs.npy already exists, skipping")

    # GT
    gt_path = os.path.join(seqdir, "gt_stamped.txt")
    if not os.path.exists(gt_path):
        gt = extract_gt(bagpath, typestore)
        if len(gt) == 0:
            print("  WARNING: no GT found, skipping")
            return
        np.savetxt(gt_path, gt, fmt="%.6f", delimiter=" ",
                   header="timestamp[us] tx ty tz qx qy qz qw")
        print(f"  Saved {len(gt)} GT poses → {gt_path}")
    else:
        print(f"  gt_stamped.txt already exists, skipping")

    # Image timestamps
    tss_path = os.path.join(seqdir, "tss_imgs_us.txt")
    if not os.path.exists(tss_path):
        tss = extract_image_timestamps(bagpath, typestore)
        if len(tss) == 0:
            print("  WARNING: no image timestamps found, skipping")
            return
        np.savetxt(tss_path, tss, fmt="%.3f")
        print(f"  Saved {len(tss)} image timestamps → {tss_path}")
    else:
        print(f"  tss_imgs_us.txt already exists, skipping")

    # Rectify map
    rmap_path = os.path.join(seqdir, "rectify_map.h5")
    if not os.path.exists(rmap_path):
        rectify_map, K_new = compute_rectify_map(calib_path)
        with h5py.File(rmap_path, 'w') as f:
            f.create_dataset('rectify_map', data=rectify_map.astype(np.float32))
        fx, fy, cx, cy = K_new[0,0], K_new[1,1], K_new[0,2], K_new[1,2]
        print(f"  Saved rectify map → {rmap_path} (fx={fx:.1f} fy={fy:.1f})")
    else:
        print(f"  rectify_map.h5 already exists, skipping")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--datapath', required=True)
    args = parser.parse_args()

    seqdirs = sorted(glob.glob(os.path.join(args.datapath, "*/raw/seq_*")))
    if not seqdirs:
        print(f"No sequences found under {args.datapath}")
        return

    print(f"Found {len(seqdirs)} sequences")
    first_bag = glob.glob(os.path.join(seqdirs[0], "*.bag"))[0]
    typestore = load_typestore(first_bag)

    for seqdir in seqdirs:
        print(f"\nSequence: {os.path.relpath(seqdir, args.datapath)}")
        try:
            preprocess_sequence(seqdir, typestore)
        except Exception as e:
            import traceback
            print(f"  ERROR: {e}")
            traceback.print_exc()

    print("\nDone.")


if __name__ == '__main__':
    main()
