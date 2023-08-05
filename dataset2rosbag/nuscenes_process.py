# -*- coding: UTF-8 -*-
import os
import argparse
import shutil
import json
import numpy as np
from nuscenes.nuscenes import NuScenes
from nuscenes.utils.geometry_utils import transform_matrix
from pyquaternion import Quaternion


# Project ：SuperGluePretrainedNetwork 
# File    ：nuscenes_process.py
# Author  ：fzhiheng
# Date    ：2023/7/27 下午3:19


# 将nuscenes数据集中的图片保存到指定的文件夹中
def save_images(dataset_root, save_to_root, scene_seq="all", save_mode="sample", camera_name="CAM_FRONT", copy=False):
    """

    Args:
        dataset_root: nuscenes数据集的根目录
        save_to_root: 保存的根目录
        save_mode: 保存模式，有两种，一种是sample，一种是all
        camera_name: 相机名称，有CAM_FRONT, CAM_FRONT_RIGHT, CAM_BACK_RIGHT, CAM_BACK, CAM_BACK_LEFT, CAM_FRONT_LEFT，如果是all模式，则将所有相机的图片都保存下来

    Returns:

    """
    nusc = NuScenes(version='v1.0-mini', dataroot=dataset_root, verbose=True)
    if camera_name != "all":
        camera_names = [camera_name]
    else:
        camera_names = ['CAM_FRONT', 'CAM_FRONT_RIGHT', 'CAM_BACK_RIGHT', 'CAM_BACK', 'CAM_BACK_LEFT',
                        'CAM_FRONT_LEFT']

    pairs_paths = []
    roots_paths = []
    scene_names = []
    for scene in nusc.scene:
        print(f"process scene {scene['name']}")
        scene_name = scene['name']
        if not (scene_name == f"scene-{scene_seq}" or scene_seq == "all"):
            continue
        save_scene_root = os.path.join(save_to_root, scene_name)
        os.makedirs(save_scene_root, exist_ok=True)

        for camera_name in camera_names:
            print(f"process camera_name {camera_name}")
            # 创建相机文件夹
            if save_mode == "sample":
                camera_root = os.path.join(save_scene_root, "sample-img", camera_name)
                pairs_txt_root = os.path.join(save_scene_root, "sample")
            elif save_mode == "sweep":  # sweep中的图像是包含所有的相机图像的
                camera_root = os.path.join(save_scene_root, "sweep-img", camera_name)
                pairs_txt_root = os.path.join(save_scene_root, "sweep")
            else:
                raise ValueError("save_mode must be sample or all")
            if copy:
                os.makedirs(camera_root, exist_ok=True)
            os.makedirs(pairs_txt_root, exist_ok=True)

            first_sample_token = scene['first_sample_token']
            sample = nusc.get('sample', first_sample_token)
            sensor = nusc.get('sample_data', sample['data'][camera_name])

            # 写入内参与外参
            sensor_calib = nusc.get('calibrated_sensor', sensor['calibrated_sensor_token'])
            translation = sensor_calib['translation']
            rotation = sensor_calib['rotation']
            camera_intrinsic = sensor_calib['camera_intrinsic']
            extrinsic_matrix = transform_matrix(np.array(translation), Quaternion(rotation)).tolist()
            intrinsic = {"fx": camera_intrinsic[0][0], "fy": camera_intrinsic[1][1], "cx": camera_intrinsic[0][2],
                         "cy": camera_intrinsic[1][2], "translation": translation, "rotation": rotation,
                         "matrix": extrinsic_matrix}

            with open(os.path.join(save_scene_root, f"{camera_name}.json"), "w", encoding='utf8') as fp:
                json.dump(intrinsic, fp, ensure_ascii=False, indent=4)

            filename = sensor["filename"]
            src_path = os.path.join(dataset_root, filename)
            image_root = os.path.dirname(src_path)
            base_name = os.path.basename(src_path)
            if copy:
                dst_path = os.path.join(camera_root, base_name)
                shutil.copy(src_path, dst_path)

            files = []
            times = []
            roots = []
            while (1):
                filename = sensor["filename"]
                timestamp = sensor['timestamp']
                src_path = os.path.join(dataset_root, filename)
                base_name = os.path.basename(src_path)
                files.append(base_name)
                times.append(timestamp)
                roots.append(os.path.dirname(src_path))
                if copy:
                    dst_path = os.path.join(camera_root, base_name)
                    shutil.copy(src_path, dst_path)
                if save_mode == "sample":
                    if sample['next']:
                        sample = nusc.get('sample', sample['next'])
                        sensor = nusc.get('sample_data', sample['data'][camera_name])
                    else:
                        break
                else:
                    if sensor['next']:
                        sensor = nusc.get('sample_data', sensor['next'])
                    else:
                        break


            # 保存图像根路径
            image_roots = [f"{last} {cur}" for last, cur in zip(roots[:-1], roots[1:])]
            root_save_path = os.path.join(pairs_txt_root, f"{camera_name}_root.txt")
            with open(root_save_path, "w") as f:
                content = "\n".join(image_roots)
                f.write(content)

            # ====================== 保存pairs ======================
            pairs = [f"{last} {cur}" for last, cur in zip(files[:-1], files[1:])]
            pairs_save_path = os.path.join(pairs_txt_root, f"{camera_name}.txt")
            with open(pairs_save_path, "w") as f:
                content = "\n".join(pairs)
                f.write(content)

            # ====================== 保存时间戳 ======================
            time_pairs = [f"{last} {cur}" for last, cur in zip(times[:-1], times[1:])]
            time_save_path = os.path.join(pairs_txt_root, f"{camera_name}_time.txt")
            with open(time_save_path, "w") as f:
                content = "\n".join(time_pairs)
                f.write(content)

            roots_paths.append(root_save_path)
            pairs_paths.append(pairs_save_path)
            scene_names.append(scene_name)

        return roots_paths, pairs_paths, scene_names


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="train")
    parser.add_argument("--mini_root", type=str, default=None,
                        help="nuscenes mini 数据集路径，如果不指定，则需要指定image_root")
    parser.add_argument("--scene", type=str, default="all", help="mini数据集中需要生成的scene,默认全部生成")
    parser.add_argument("--save_mode", type=str, default="sweep", help="sample or sweep")
    parser.add_argument("--save_cam", type=str, default="CAM_FRONT", help="需要保存的相机")
    parser.add_argument("--output", type=str, default="./nuscenes_output", help="生成的图片和pairs文本的输出路径")
    parser.add_argument("--copy", type=bool, default=False,
                        help="是否将图片复制到指定的文件夹中，如果为False，则只生成pairs文本")

    parser.add_argument("--image_root", type=str, default=None,
                        help="image root, 该参数只有在mini数据集路径不指定的情况下才有用")
    parser.add_argument("--txt_name", type=str,
                        help="生成的txt名字，在给定image_root的情况下，该参数才有作用，不指定的话使用image_root路径作为的名字")

    parser.add_argument("--glue_output", type=str, default="./glue_output", help="匹配生成的路径")
    parser.add_argument("--glue", action='store_true', default=False, help="是否进行匹配")
    parser.add_argument("--max_keypoints", type=int, default=1024, help="是否进行匹配")
    parser.add_argument("--nms_radius", type=int, default=3, help="是否进行匹配")
    parser.add_argument("--resize", type=int, default=1600, help="是否进行匹配")

    args = parser.parse_args()

    if args.mini_root is not None:
        roots_paths, pairs_paths, scene_names = save_images(args.mini_root, args.output, args.scene, args.save_mode,
                                                                args.save_cam, args.copy)
    else:
        raise ValueError("mini_root must be specified")

    # 进行match
    if args.glue:
        # TODO 多进程
        for input_dir, input_pairs, scene_name in zip(roots_paths, pairs_paths, scene_names):
            output_path = os.path.join(args.glue_output, scene_name, args.save_mode)
            txt_name = os.path.basename(input_pairs).split(".")[0]
            output_path = os.path.join(output_path, f"{txt_name}_{args.resize}_{args.max_keypoints}")
            os.makedirs(output_path, exist_ok=True)
            cmd = f"python3 ./match_pairs.py --resize {args.resize} --superglue outdoor --max_keypoints {args.max_keypoints} " \
                  f"--nms_radius {args.nms_radius} --resize_float --input_pairs {input_pairs} --input_dir {input_dir} " \
                  f"--output_dir {output_path}"
            os.system(cmd)
