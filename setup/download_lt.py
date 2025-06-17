# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import os
import json
import tensorflow as tf
import tensorflow_datasets as tfds
from PIL import Image
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

def decode_inst(inst):
    """Utility to decode encoded language instruction"""
    return bytes(inst[np.where(inst != 0)].tolist()).decode("utf-8")

def save_frame(frame, global_video_id, i):
    """Save a single frame as an image."""
    Image.fromarray(frame).save(f'language_table/video_{global_video_id}_frame_{i}.jpg')

def process_slice(slice_index, num_slices):
    DATASET_VERSION = '0.0.1'
    DATASET_NAME = 'language_table'  # CHANGEME: change this to load another dataset.

    dataset_directories = {
        'language_table': 'gs://gresearch/robotics/language_table',
        'language_table_sim': 'gs://gresearch/robotics/language_table_sim',
        'language_table_blocktoblock_sim': 'gs://gresearch/robotics/language_table_blocktoblock_sim',
        'language_table_blocktoblock_4block_sim': 'gs://gresearch/robotics/language_table_blocktoblock_4block_sim',
        'language_table_blocktoblock_oracle_sim': 'gs://gresearch/robotics/language_table_blocktoblock_oracle_sim',
        'language_table_blocktoblockrelative_oracle_sim': 'gs://gresearch/robotics/language_table_blocktoblockrelative_oracle_sim',
        'language_table_blocktoabsolute_oracle_sim': 'gs://gresearch/robotics/language_table_blocktoabsolute_oracle_sim',
        'language_table_blocktorelative_oracle_sim': 'gs://gresearch/robotics/language_table_blocktorelative_oracle_sim',
        'language_table_separate_oracle_sim': 'gs://gresearch/robotics/language_table_separate_oracle_sim',
    }

    dataset_path = os.path.join(dataset_directories[DATASET_NAME], DATASET_VERSION)
    builder = tfds.builder_from_directory(dataset_path)
    builder.download_and_prepare()
    episode_ds = builder.as_dataset(split='train')

    captions = {}

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

    ids = set()
    for x in video_ids:
        if x.startswith("language_table"):
            ids.add(int(x.replace("language_table/video_", "").replace(".mp4", "")))

    # Convert the set of IDs to a TensorFlow constant for efficient comparison
    ids_tensor = tf.constant(list(ids), dtype=tf.int64)

    # Filter the dataset to only include episodes with IDs in the `ids` set
    def filter_fn(idx, _):
        return tf.reduce_any(tf.equal(idx, ids_tensor))

    filtered_ds = episode_ds.enumerate().filter(filter_fn)

    print('START DOWNLOAD')
    with ThreadPoolExecutor() as executor:
        for local_video_id, episode in tqdm(filtered_ds):
            global_video_id = local_video_id.numpy()
            frames = []
            for i, step in enumerate(episode['steps'].as_numpy_iterator()):
                frame = step['observation']['rgb']
                frames.append(frame)
                # Save each frame as an image in parallel
                executor.submit(save_frame, frame, global_video_id, i)

            # Decode the instruction
            # instruction = decode_inst(step['observation']['instruction'])
            # captions[f'video_{global_video_id}'] = instruction

            # Save captions to a JSON file
            # with open(f'captions_{slice_index}.json', 'w')


if __name__ == '__main__':
    slice_index = 0
    num_slices = 1

    process_slice(slice_index, num_slices)
