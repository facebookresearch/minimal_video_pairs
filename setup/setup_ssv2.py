# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

from moviepy.editor import VideoFileClip
import json
import os

def convert_webm_to_mp4(input_file, output_file):
    try:
        # Load the video file
        clip = VideoFileClip(input_file)
        # Write the video file as mp4
        clip.write_videofile(output_file, codec='libx264')
        print(f"Conversion successful: {output_file}")
    except Exception as e:
        print(f"An error occurred: {e}")

for x in os.listdir('ssv2'):
    path = f'ssv2/{x}'
    output_file = f'ssv2/{x[:-4]}mp4'
    convert_webm_to_mp4(path, output_file)
