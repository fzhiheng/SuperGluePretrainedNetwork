# 文件夹结构
相机包含六个：`CAM_FRONT`, `CAM_FRONT_LEFT`, `CAM_FRONT_RIGHT`, `CAM_BACK`, `CAM_BACK_LEFT`, `CAM_BACK_RIGHT`

经过脚本nuscenes_process.py处理，生成的文件夹结构如下：
````
└── scene-0061
    ├── sample
    │   ├── CAM_FRONT.txt
    │   ├── CAM_FRONT_root.txt
    │   ├── CAM_FRONT_time.txt
    │   └── ...
    ├── sweep   
    │   └── ...
    ├── sweep-step   
    │   └── ...
    ├── CAM_FRONT.json
    └── CAM_*.json 
````
其中`CAM_FRONT.txt`表示图片对，`CAM_FRONT_root.txt`表示图片所在的目录。`CAM_FRONT_time.txt`表示对应的时间戳。

**特别地**，由于nuscenes数据集图片并没有按照场景放在不同的文件夹中，而且由于sample和sweep的区别，同一个场景中的图片也可能不在同一个文件夹中，若SfM需要全部的图片，可以选择将所有的图片整理到一个新的文件夹中，方便操作。只需要在运行脚本的时候加上参数 `--copy`就可以了。



若选择生成新的文件夹，则在数据集下会新增：
````
└── scene-0061
    ├── sample-img
    │   ├── CAM_BACK
    │   │   ├── n015-2018-07-24-11-22-45+0800__CAM_BACK__1532402927637525.jpg
    │   │   ├── ...
    │   │   └── n015-2018-07-24-11-22-45+0800__CAM_BACK__1532402946787525.jpg
    │   ├── ...
    │   └── CAM_LEFT
    └── sweep-img
        ├── CAM_BACK
        ├── ...
        └── CAM_LEFT
````


因为nuscenes数据获取图片是从名字中直接获取的，因此在生成配对的txt文件时，没有必要整理成新的文件夹结构，


# Run

## 输出匹配关系npz文件

**处理nusenes的参数列表如下**

- `--mini_root`：nuscenes mini 数据集路径

- `--scene`：需要处理的scene，默认全部，待选的有`0061，0103，0553，0655，0757，0796，0916，1077，1094，1100`。例如`--scene 0063`或者`--scene 0063 0655`

- `--camera`：需要处理的相机，默认`CAM_FRONT`，待选的有`CAM_FRONT`, `CAM_FRONT_LEFT`, `CAM_FRONT_RIGHT`, `CAM_BACK`, `CAM_BACK_LEFT`, `CAM_BACK_RIGHT`，`all`表示全部，可接多个参数处理若干相机。例如 `--camera CAM_FRONT CAM_FRONT_LEFT`

- `--step`：图片对之间的间隔，`<0` 表示图片对来自于sample相邻帧，否则是sweep中相隔step帧

- `--output`：结果存放根路径，默认./output/pairs

- `--copy`：是否将文件复制到新的文件夹中，默认不需要，需要的话使用`--copy`即可

  

**使用glue生成npz文件的参数如下：**

- `--glue`：启用superglue生成npz文件，默认不需要，需要的话使用`--glue`即可

- `--glue_output`：npz文件生成路径，默认./output/glue

- `--max_keypoints`：每张图片提取的最大特征点数，默认1024

- `--resize`：图片进行特征点提取和匹配前resize的大小，-1表示不进行resize，详见`match_pair.py`

- `--nms_radius`：nms处理的半径大小，默认3

  

### 使用举例

1. 从nuscenes mini数据集中生成pairs:

`python -m utils.preprocess --mini_root /path/to/v1.0-mini --scene 0061 --step 1 --camera CAM_FRONT`

2. 若生成pairs的同时，生成匹配关系

`python -m utils.preprocess --mini_root /path/to/v1.0-mini --scene 0061 --step 1 --camera CAM_FRONT --glue`

3. 若仅从pairs生成匹配关系

`./match_pairs.py --resize 1600 --superglue outdoor --max_keypoints 2048 --nms_radius 3 --resize_float --input_dir /path/to/img --input_pairs /path/to/pairs.txt --output_dir /path/to/output `




## 从npz文件到rosbag

`python3 -m utils.rosbag --npz_root ./output/glue/scene-0061/sweep/CAM_FRONT_1600_1024 --intrinsic_path ./output/pairs/scene-0061/CAM_FRONT.json `



## 合并rosbag 

`python3 -m utils.merge_bag --inputbag bag1 bag2 --outputbag /path/to/outputbag  -v`

参数列表如下：

`--inputbag`：多选，需要合并的bag包

`--outputbag`：合并后包的保存路径

`-t`：需要保存的topic，支持正则表达式匹配