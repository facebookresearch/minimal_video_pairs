# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import os
import csv
from moviepy.editor import ImageSequenceClip
import json

def make_video(path_to_png, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    image_files = [
        os.path.join(path_to_png, f"scene_{i:03}.png")
        for i in range(1, 101)
        if os.path.exists(os.path.join(path_to_png, f"scene_{i:03}.png"))
    ]

    clip = ImageSequenceClip(image_files, fps=24)

    clip.write_videofile(out_path + '.mp4', codec='libx264')

with open('intphys_pairs.csv',newline='') as csvfile:
    csvreader = csv.DictReader(csvfile,  delimiter=';')
    for row in csvreader:
        path1 = f'dev/{row["Property"]}/{"0" if len(row["id"]) == 1 else ""}{row["id"]}/{int(row["Video1"])+1}/scene'
        path2 = f'dev/{row["Property"]}/{"0" if len(row["id"]) == 1 else ""}{row["id"]}/{int(row["Video2"])+1}/scene'
        video_id1 = f'intphys/{path1.replace("scene", "").replace("dev", "").replace("/","_")}'[:-1]
        video_id2 = f'intphys/{path2.replace("scene", "").replace("dev", "").replace("/","_")}'[:-1]
        make_video(path1, video_id1)
        make_video(path2, video_id2)

