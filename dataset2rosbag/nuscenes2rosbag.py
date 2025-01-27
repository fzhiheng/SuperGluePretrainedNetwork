# -*- coding: UTF-8 -*-
import os
import glob
import rosbag
import argparse
import numpy as np
from sensor_msgs.msg import PointCloud, ChannelFloat32
from geometry_msgs.msg import Point32
from sensor_msgs.msg import ChannelFloat32
import rospy
import json

# Project ：SuperGluePretrainedNetwork
# File    ：nuscenes2rosbag.py
# Author  ：fzhiheng
# Date    ：2023/8/3 下午7:54

"""
将提取到的特征点信息转换为rosbag
"""


# 像素坐标转换为归一化坐标
def pixel2normalized(pixel: np.ndarray, K):
    """
    Args:
        pixel: 像素坐标
        K: 相机内参
    Returns:
        normalized: 归一化坐标
    """
    fx = K[0][0]
    fy = K[1][1]
    cx = K[0][2]
    cy = K[1][2]

    n = pixel.shape[0]
    normalized = np.ones((n, 3))
    normalized[:, 0] = (pixel[:, 0] - cx) / fx
    normalized[:, 1] = (pixel[:, 1] - cy) / fy

    return normalized


def write_rosbag(npz_root, intrinsic_path, save_path):

    bag = rosbag.Bag(save_path, 'w')
    # 读取相机内参
    with open(intrinsic_path, "r") as f:
        intrinsic = json.load(f)
        fx = intrinsic["fx"]
        fy = intrinsic["fy"]
        cx = intrinsic["cx"]
        cy = intrinsic["cy"]
        K = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]])

    npz_paths = glob.glob(os.path.join(npz_root, "*.npz"))
    npz_paths = sorted(npz_paths)

    last_keypoint_map = {}
    n_id = 0
    message_length = 0
    for i, path in enumerate(npz_paths):
        # 由于nuscenes的图片的命名方式中包含时间戳，因此可以直接从文件名中获取时间戳
        # n015-2018-07-24-11-22-45+0800__CAM_FRONT__1532402927612460.jpg,这张图片的时间戳为1532402927612460
        cur_time = os.path.basename(path).split("_")[-2]
        cur_time = int(cur_time)
        last_time = os.path.basename(path).split("_")[5]
        last_time = int(last_time)
        dt = (cur_time - last_time) / 1e6

        cam_name = os.path.basename(path).split("_")[3]
        # cam_name = cam_name.lower()
        npz = np.load(path)

        # 读取npz中的数据
        # 对于 keypoints 中的每个关键点，matches 数组表示 keypoints1 中匹配关键点的索引，如果关键点未匹配，则为-1。
        keypoints0 = npz["keypoints0"]
        keypoints1 = npz["keypoints1"]
        matches = npz["matches"]
        match_confidence = npz["match_confidence"]

        # 筛选匹配成功的特征点
        valid = np.where(matches > -1)
        matches = matches[valid]
        keypoints0 = keypoints0[valid]
        match_confidence = match_confidence[valid]

        # 对match_confidence从大到小进行排序
        index = np.argsort(match_confidence)[::-1]
        match_confidence = match_confidence[index]
        matches = matches[index]
        keypoints0 = keypoints0[index]
        keypoints1 = keypoints1[matches]

        print("valid matches: ", keypoints0.shape[0])
        if i == 0:
            xyz = pixel2normalized(keypoints0, K).tolist()  # 归一化坐标
            points = [Point32(x, y, z) for x, y, z in xyz]
            last_ids = [i for i in range(len(points))]
            n_id = last_ids[-1]
            camera_ids = [0 for i in range(len(points))]
            pus = keypoints0[:, 0].tolist()
            pvs = keypoints0[:, 1].tolist()
            vel_u = np.zeros((keypoints0.shape[0])).tolist()
            vel_v = vel_u
            channels = [ChannelFloat32("feature_id", last_ids), ChannelFloat32("camera_id", camera_ids),
                        ChannelFloat32("p_u", pus), ChannelFloat32("p_v", pvs),
                        ChannelFloat32("velocity_x", vel_u), ChannelFloat32("velocity_y", vel_v)]

            last_keypoint_map = {(pu, pv): ids for pu, pv, ids in zip(pus, pvs, last_ids)}

            # 创建一个PointCloud类型的消息
            point_cloud = PointCloud()
            stamp = rospy.Time.from_sec(last_time / 1e6)
            point_cloud.header.stamp = stamp
            point_cloud.points = points
            point_cloud.channels = channels
            topic_name = f"/feature_tracker/feature_{cam_name}"
            bag.write(topic_name, point_cloud, stamp)
            message_length += 1

        cur_keypoint_map = {}
        xyz = pixel2normalized(keypoints1, K).tolist()  # 归一化坐标
        camera_ids = np.zeros((keypoints1.shape[0])).tolist()
        points = [Point32(x, y, z) for x, y, z in xyz]
        last_pus = keypoints0[:, 0].tolist()
        last_pvs = keypoints0[:, 1].tolist()
        cur_pus = keypoints1[:, 0].tolist()
        cur_pvs = keypoints1[:, 1].tolist()
        cur_ids = []
        for cur_u, cur_v, last_u, last_v in zip(cur_pus, cur_pvs, last_pus, last_pvs):
            if (last_u, last_v) in last_keypoint_map:
                id = last_keypoint_map[(last_u, last_v)]
            else:
                n_id += 1
                id = n_id
            cur_ids.append(id)
            cur_keypoint_map[(cur_u, cur_v)] = id

        vels = (keypoints1 - keypoints0) / dt  # 速度
        vel_u = vels[:, 0].tolist()
        vel_v = vels[:, 1].tolist()
        # channels = [cur_ids, camera_ids, cur_pus, cur_pvs, vel_u, vel_v]
        channels = [ChannelFloat32("feature_id", cur_ids), ChannelFloat32("camera_id", camera_ids),
                    ChannelFloat32("p_u", cur_pus), ChannelFloat32("p_v", cur_pvs),
                    ChannelFloat32("velocity_x", vel_u), ChannelFloat32("velocity_y", vel_v)]

        # with rosbag.Bag(save_path, 'w+') as bag:
        point_cloud = PointCloud()
        stamp = rospy.Time.from_sec(cur_time / 1e6)
        point_cloud.header.stamp = stamp
        point_cloud.points = points
        point_cloud.channels = channels
        bag.write(f"/feature_tracker/feature_{cam_name}", point_cloud, stamp)
        message_length += 1

        last_keypoint_map = cur_keypoint_map

    bag.close()
    print(f"write to {save_path}, has {message_length} messages")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="train")
    parser.add_argument("--npz_root", type=str, help="匹配后的结果保存路径")
    parser.add_argument("--intrinsic_path", type=str, help="相机对应的内参文件")
    parser.add_argument("--output", type=str, default=None, help="rosbag保存路径")
    parser.add_argument("--rosbag_name", type=str, default=None, help="输出的rosbag的名字")
    args = parser.parse_args()

    npz_root = args.npz_root
    save_root = args.output if args.output else os.path.dirname(npz_root)
    save_name = args.output if args.output else f"{os.path.basename(npz_root)}.bag"
    save_path = os.path.join(save_root, save_name)
    os.makedirs(save_root, exist_ok=True)
    write_rosbag(npz_root, args.intrinsic_path, save_path)
