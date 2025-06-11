# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import sys
import json
import os

source = sys.argv[1]

test = json.load(open('../test.json', 'r'))
video_ids = []
for x in test:
    if x['source'] == source:
        if source == 'ssv2':
            video_ids.append(x['video_id1'] + '.webm')
            video_ids.append(x['video_id2'] + '.webm')
        else:
            video_ids.append(x['video_id1'] + '.mp4')
            video_ids.append(x['video_id2'] + '.mp4')

for file in os.listdir(f'{source}'):
    if file not in video_ids:
        os.remove(f'{source}/{file}')
