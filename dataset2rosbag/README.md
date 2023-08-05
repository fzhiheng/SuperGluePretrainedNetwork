# 图片整理的数据集结构
相机包含六个：`CAM_FRONT`, `CAM_FRONT_LEFT`, `CAM_FRONT_RIGHT`, `CAM_BACK`, `CAM_BACK_LEFT`, `CAM_BACK_RIGHT`

经过脚本nuscenes_process.py处理，生成成对的txt文件，每个txt文件包含一帧图片的路径，如下：
其中step表示匹配的时候相隔的帧数
````
└── scene-0061
    ├── sample
    │   ├── CAM_BACK.txt
    │   ├── ...
    │   ├── CAM_LEFT.txt
    │   ├── TIME_CAM_BACK.txt
    │   ├── ...
    │   └── TIME_CAM_LEFT.txt
    ├── sweep   
    │   ├── CAM_BACK.txt
    │   ├── ...
    │   └── TIME_CAM_LEFT.txt
    ├── sweep-step   
    │   ├── CAM_BACK.txt
    │   ├── ...
    │   └── TIME_CAM_LEFT.txt
    ├── CAM_BACK.json
    ├── ...json
    └── CAM_LEFT.json 
````

，若选择生成新的文件夹，则在数据集下会新增：
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

1. 从nuscenes mini数据集中生成pairs:

`python -m dataset2rosbag.nuscenes_process --mini_root /path/to/v1.0-mini --scene 0061 --save_mode sweep --save_cam CAM_FRONT`

2. 若生成pairs的同时，生成匹配关系

`python -m dataset2rosbag.nuscenes_process --mini_root /path/to/v1.0-mini --scene 0061 --save_mode sweep --save_cam CAM_FRONT --glue`

待选参数：
`--max_keypoints 1024`
`--nms_radius 3`
`--resize 1600`



3. 若仅从pairs生成匹配关系

`./match_pairs.py --resize 1600 --superglue outdoor --max_keypoints 2048 --nms_radius 3 --resize_float --input_dir /path/to/img --input_pairs /path/to/pairs.txt --output_dir /path/to/output `