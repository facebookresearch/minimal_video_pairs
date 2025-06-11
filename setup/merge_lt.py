# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import os
import json
import cv2
from glob import glob
from tqdm import tqdm

def convert_images_to_video(input_folder='language_table', output_folder='language_table_slow', fps=5):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    video_ids = set()
    for file in glob(f'{input_folder}/video_*_frame_*.jpg'):
        video_id = '_'.join(file.split('_')[3:4])
        video_ids.add(video_id)

    for video_id in tqdm(video_ids):
        frames = []
        frame_number = 0

        while True:
            frame_file = f'{input_folder}/video_{video_id}_frame_{frame_number}.jpg'
            if os.path.exists(frame_file):
                frames.append(frame_file)
                frame_number += 1
            else:
                break

        if not frames:
            continue

        # Read the first frame to get the dimensions
        frame = cv2.imread(frames[0])
        height, width, layers = frame.shape

        video_path = os.path.join(output_folder, f'video_{video_id}.mp4')
        video = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

        for frame_file in frames:
            frame = cv2.imread(frame_file)
            video.write(frame)

        video.release()

    print(f"Videos saved to {output_folder}")

if __name__ == '__main__':
    convert_images_to_video()
