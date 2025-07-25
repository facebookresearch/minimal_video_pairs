# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import io
import json
import os
import pathlib
import re
import time
from typing import List, Tuple

import datasets
from accelerate import Accelerator, DistributedType
from lmms_eval.api.instance import Instance
from lmms_eval.api.model import lmms
from lmms_eval.api.registry import register_model
from loguru import logger as eval_logger
from PIL import Image
from tqdm import tqdm

try:
    from google import genai as genai_api
    from google.genai.types import SafetySetting, HarmBlockThreshold, HarmCategory

    NUM_SECONDS_TO_SLEEP = 30
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    genai = genai_api.Client(api_key=GOOGLE_API_KEY)

except Exception as e:
    eval_logger.error(f"Error importing generativeai: {str(e)}")
    genai = None

try:
    import soundfile as sf
except Exception as e:
    eval_logger.warning(
        f"Error importing soundfile, audio generation will not work: {str(e)}"
    )


@register_model("gemini_api")
class GeminiAPI(lmms):
    def __init__(
        self,
        model_version: str = "gemini-1.5-pro",
        # modality: str = "image",
        timeout: int = 120,
        continual_mode: bool = True,
        response_persistent_folder: str = "./logs/gemini_persistent_folder",
        interleave: bool = False,
        # We will cache the Gemini API response in this path and use it for future requests
        **kwargs,
    ) -> None:
        super().__init__()
        self.model_version = model_version
        self.timeout = timeout
        self.model = genai
        self.continual_mode = continual_mode
        self.response_persistent_file = ""
        self.interleave = interleave
        # if self.continual_mode and response_persistent_folder is None:
        #     raise ValueError("Continual mode requires a persistent path for the response. We will cache the Gemini API response in this path and use it for future requests. Please provide a valid path.")
        if self.continual_mode:
            self.response_persistent_folder = response_persistent_folder
            if not os.path.exists(self.response_persistent_folder):
                os.makedirs(self.response_persistent_folder)
            self.response_persistent_file = os.path.join(
                self.response_persistent_folder, f"{self.model_version}_response.json"
            )

        if os.path.exists(self.response_persistent_file):
            with open(self.response_persistent_file, "r") as f:
                self.response_cache = json.load(f)
            self.cache_mode = "resume"
        else:
            self.response_cache = {}
            self.cache_mode = "start"

        accelerator = Accelerator()
        if accelerator.num_processes > 1:
            assert (
                self.continual_mode is False
            ), "Continual mode is not supported with distributed inference."
            assert accelerator.distributed_type in [
                DistributedType.FSDP,
                DistributedType.MULTI_GPU,
                DistributedType.DEEPSPEED,
            ], "Unsupported distributed type provided. Only DDP and FSDP are supported."
            self.accelerator = accelerator
            if self.accelerator.is_local_main_process:
                eval_logger.info(
                    f"Using {accelerator.num_processes} devices with data parallelism"
                )
            self._rank = self.accelerator.local_process_index
            self._world_size = self.accelerator.num_processes
        else:
            self.accelerator = accelerator
            self._rank = self.accelerator.local_process_index
            self._world_size = self.accelerator.num_processes

        self.device = self.accelerator.device

        # self.modality = modality

        self.video_pool = []

    def free_video(self):
        for video in self.video_pool:
            video.delete()
        self.video_pool = []

    def flatten(self, input):
        new_list = []
        for i in input:
            for j in i:
                new_list.append(j)
        return new_list

    def get_image_size(self, image):
        # Create a BytesIO object to store the image bytes
        img_byte_array = io.BytesIO()

        # Save the image to the BytesIO object
        image.save(img_byte_array, format="PNG")

        # Get the size of the BytesIO object
        img_size = img_byte_array.tell()

        return img_size

    def encode_video(self, video_path):
        uploaded_obj = self.model.files.upload(file=video_path)
        time.sleep(5)
        self.video_pool.append(uploaded_obj)
        return uploaded_obj

    def encode_audio(self, audio):
        audio_io = io.BytesIO()
        sf.write(audio_io, audio["array"], audio["sampling_rate"], format="WAV")
        return self.model.files.upload(file=audio_io, mime_type="audio/wav")

    def convert_modality(self, images):
        for idx, img in enumerate(images):
            if isinstance(img, dict) and "sampling_rate" in img:  # audio
                audio = self.encode_audio(img)
                images[idx] = audio
            elif isinstance(img, str):  # video
                try:
                    images[idx] = self.encode_video(img)
                except Exception as e:
                    eval_logger.error(f"Error converting video: {str(e)}")
        return images

    def construct_interleaved_input(self, content, media):
        pattern = r"<media_(\d+)>"
        parts = re.split(pattern, content)
        result = []
        for i, part in enumerate(parts):
            if i % 2 == 0:
                if part == "":
                    continue
                result.append(part)
            else:
                result.append(media[int(part)])

        return result

    def generate_until(self, requests) -> List[str]:
        res = []
        pbar = tqdm(
            total=len(requests), disable=(self.rank != 0), desc="Model Responding"
        )

        def get_uuid(task, split, doc_id):
            return f"{task}___{split}___{doc_id}"

        for contexts, gen_kwargs, doc_to_visual, doc_id, task, split in [
            reg.args for reg in requests
        ]:
            if self.continual_mode and self.cache_mode == "resume":
                doc_uuid = get_uuid(task, split, doc_id)
                if doc_uuid in self.response_cache:
                    content = self.response_cache[doc_uuid]
                    if content:
                        res.append(content)
                        pbar.update(1)
                        continue

            if "max_new_tokens" not in gen_kwargs:
                gen_kwargs["max_new_tokens"] = 1024
            if "temperature" not in gen_kwargs:
                gen_kwargs["temperature"] = 0

            config = genai_api.types.GenerateContentConfig(
                max_output_tokens=gen_kwargs["max_new_tokens"],
                temperature=gen_kwargs["temperature"],
                safety_settings=[
                    SafetySetting(category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,threshold=HarmBlockThreshold.BLOCK_NONE),
                    SafetySetting(category=HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=HarmBlockThreshold.BLOCK_NONE),
                    SafetySetting(category=HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=HarmBlockThreshold.BLOCK_NONE),
                    SafetySetting(category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=HarmBlockThreshold.BLOCK_NONE),
                ],
            )

            visuals = [doc_to_visual(self.task_dict[task][split][doc_id])]
            visuals = self.flatten(visuals)
            visuals = self.convert_modality(visuals)

            if self.interleave:
                message = self.construct_interleaved_input(contexts, visuals)
            else:
                message = [contexts] + visuals

            for attempt in range(5):
                try:
                    content = self.model.models.generate_content(
                        model=self.model_version,
                        contents=message,
                        config=config,
                    )
                    content = content.text
                    break
                except Exception as e:
                    eval_logger.info(
                        f"Attempt {attempt + 1} failed with error: {str(e)}"
                    )
                    if isinstance(e, ValueError):
                        try:
                            eval_logger.info(
                                f"Prompt feed_back: {content.prompt_feedback}"
                            )
                            content = ""
                            break
                        except Exception:
                            pass
                    if (
                        attempt < 5 - 1
                    ):  # If we have retries left, sleep and then continue to next attempt
                        time.sleep(NUM_SECONDS_TO_SLEEP)
                    else:  # If this was the last attempt, log and return empty
                        eval_logger.error(
                            f"All 5 attempts failed. Last error message: {str(e)}"
                        )
                        content = ""
            res.append(content)
            pbar.update(1)

            self.free_video()

            if self.continual_mode is True:  # Cache the response
                doc_uuid = get_uuid(task, split, doc_id)
                self.response_cache[doc_uuid] = content
                with open(self.response_persistent_file, "w") as f:
                    json.dump(self.response_cache, f)

        pbar.close()
        return res

    def generate_until_multi_round(self, requests) -> List[str]:
        raise NotImplementedError(
            "TODO: Implement multi-round generation for Gemini API"
        )

    def loglikelihood(self, requests: List[Instance]) -> List[Tuple[float, bool]]:
        # TODO
        assert False, "Gemini API not support"

    def get_image_audio_text_interleaved_messsage(
        self, image_path, audio_path, question
    ):
        # image_path for list of image path
        # audio_path for list of audio path
        # question for question

        # fixed image token and no audio in text
        for index in range(1, 1 + len(image_path)):
            question = question.replace(f"[img{index}]", "<image>")
        for index in range(1, 1 + len(audio_path)):
            question = question.replace(f"[audio{index}]", "<audio>")

        text = question

        info_list = []
        image_counter = 0
        audio_counter = 0
        for part in re.split(r"(<image>|<audio>)", text):
            if part == "<image>":
                info_list.append(Image.open(image_path[image_counter]))
                image_counter += 1
            elif part == "<audio>":
                info_list.append(
                    {
                        "mime_type": "audio/wav",
                        "data": pathlib.Path(audio_path[audio_counter]).read_bytes(),
                    }
                )
                audio_counter += 1
            else:
                if part == " ":
                    continue
                info_list.append(part)

        return info_list

    def get_video_audio_text_interleaved_message(
        self, video_path, audio_path, question
    ):
        # image_path for list of image path
        # audio_path for list of audio path
        # question for question

        # fixed video token and no audio in text
        for index in range(1, 1 + len(video_path)):
            question = question.replace(f"[video{index}]", "<video>")
        for index in range(1, 1 + len(audio_path)):
            question = question.replace(f"[audio{index}]", "<audio>")

        text = question

        info_list = []
        video_counter = 0
        audio_counter = 0
        for part in re.split(r"(<video>|<audio>)", text):
            if part == "<video>":
                current_video_file_name = video_path[video_counter]
                current_video_file = self.model.files.upload(
                    file=current_video_file_name
                )
                while current_video_file.state.name == "processing":
                    print("uploading file")
                    time.sleep(5)
                    current_video_file = genai.get_file(current_video_file.name)
                if current_video_file.state.name == "FAILED":
                    print("uploading file failed, next question")
                    return 0
                info_list.append(current_video_file)
                video_counter += 1
            elif part == "<audio>":
                info_list.append(
                    {
                        "mime_type": "audio/wav",
                        "data": pathlib.Path(audio_path[audio_counter]).read_bytes(),
                    }
                )
                audio_counter += 1
            else:
                if part == " ":
                    continue
                info_list.append(part)

        return info_list
