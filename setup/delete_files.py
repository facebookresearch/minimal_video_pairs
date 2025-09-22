# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import glob
import json
import os
import sys

from datasets import load_dataset

source = sys.argv[1]

data_names = [
    "human_object_interactions",
    "intuitive_physics",
    "robot_object_interactions",
    "temporal_reasoning",
]
splits = ["mini", "full"]

video_ids = []
for data_name in data_names:
    for split in splits:
        dt = load_dataset("facebook/minimal_video_pairs", data_name, split=split)
        video_ids.extend([x.lstrip("/") for x in dt["video_path"]])


files = glob.glob(f"{source}/**")
for file in files:
    if file not in video_ids:
        os.remove(file)
