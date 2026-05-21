import numpy as np
from scipy.spatial.transform import Rotation as R
import tqdm
from rosbags.rosbag1 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg


def _make_typestore():
    ts = get_typestore(Stores.ROS1_NOETIC)
    add_types = {}
    add_types.update(get_types_from_msg(
        'uint16 x\nuint16 y\ntime ts\nbool polarity',
        'dvs_msgs/msg/Event'
    ))
    add_types.update(get_types_from_msg(
        'Header header\nuint32 height\nuint32 width\ndvs_msgs/Event[] events',
        'dvs_msgs/msg/EventArray'
    ))
    ts.register(add_types)
    return ts


class BagReader:
    """Drop-in replacement for rosbag.Bag using the rosbags library (no ROS install needed)."""

    def __init__(self, path):
        self._reader = Reader(path)
        self._reader.open()
        self._typestore = _make_typestore()

    def get_type_and_topic_info(self):
        return (None, {t: v for t, v in self._reader.topics.items()})

    def get_message_count(self, topic):
        return self._reader.topics[topic].msgcount

    def get_msgtype(self, topic):
        return self._reader.topics[topic].msgtype

    def read_messages(self, topic):
        conns = [c for c in self._reader.connections if c.topic == topic]
        for conn, stamp, raw in self._reader.messages(connections=conns):
            msg = self._typestore.deserialize_ros1(raw, conn.msgtype)
            yield topic, msg, stamp

    def close(self):
        self._reader.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def read_H_W_from_bag(bag, imgtopic):
    for topic, msg, t in bag.read_messages(imgtopic):
        H, W = msg.height, msg.width
        print(f"Read H, W from bag: {H}, {W}")
        return H, W


def read_images_from_rosbag(bag, imgtopic, H=180, W=240):
    imgs = []
    progress_bar = tqdm.tqdm(total=bag.get_message_count(imgtopic))
    for topic, msg, t in bag.read_messages(imgtopic):
        img = np.frombuffer(bytes(msg.data), dtype=np.uint8).reshape(msg.height, msg.width)
        imgs.append(img)
        progress_bar.update(1)
        if abs(H - msg.height) > 2 or abs(W - msg.width) > 2:
            print(f"WARNING: H, W mismatch: {msg.height}, {msg.width}, {H}, {W}")
    return imgs


def read_tss_us_from_rosbag(bag, imgtopic):
    tss_us = []
    for topic, msg, t in bag.read_messages(imgtopic):
        tss_us.append(msg.header.stamp.sec * 1e6 + msg.header.stamp.nanosec / 1e3)
    return tss_us


def read_evs_from_rosbag(bag, evtopic, H=180, W=240):
    print(f"Start reading evs from {evtopic}")
    evs = []
    progress_bar = tqdm.tqdm(total=bag.get_message_count(evtopic))
    for topic, msg, t in bag.read_messages(evtopic):
        for ev in msg.events:
            p = 1 if ev.polarity else 0
            t_us = ev.ts.sec * 1e6 + ev.ts.nanosec / 1e3
            evs.append([ev.x, ev.y, t_us, p])
        progress_bar.update(1)
    return np.array(evs)  # (N, 4)


def read_t0us_evs_from_rosbag(bag, evtopic):
    for topic, msg, t in bag.read_messages(evtopic):
        for ev in msg.events:
            return ev.ts.sec * 1e6 + ev.ts.nanosec / 1e3


def read_poses_from_rosbag(bag, posestopic, T_marker_cam0, T_cam0_cam1):
    progress_bar = tqdm.tqdm(total=bag.get_message_count(posestopic))
    is_odometry = 'Odometry' in bag.get_msgtype(posestopic)

    poses = []
    tss_us_gt = []
    for topic, msg, t in bag.read_messages(posestopic):
        if is_odometry:
            ps = np.array([msg.pose.pose.position.x, msg.pose.pose.position.y, msg.pose.pose.position.z,
                           msg.pose.pose.orientation.x, msg.pose.pose.orientation.y, msg.pose.pose.orientation.z, msg.pose.pose.orientation.w])
        else:
            ps = np.array([msg.pose.position.x, msg.pose.position.y, msg.pose.position.z,
                           msg.pose.orientation.x, msg.pose.orientation.y, msg.pose.orientation.z, msg.pose.orientation.w])

        T_world_marker = np.eye(4)
        T_world_marker[:3, 3] = ps[:3]
        T_world_marker[:3, :3] = R.from_quat(ps[3:]).as_matrix()

        T_world_cam = T_world_marker @ T_marker_cam0 @ T_cam0_cam1
        poses.append(np.concatenate((T_world_cam[:3, 3], R.from_matrix(T_world_cam[:3, :3]).as_quat())))
        tss_us_gt.append(msg.header.stamp.sec * 1e6 + msg.header.stamp.nanosec / 1e3)
        progress_bar.update(1)

    return np.array(poses), tss_us_gt


def read_calib_from_bag(bag, imtopic):
    for topic, msg, t in bag.read_messages(imtopic):
        return msg.K
