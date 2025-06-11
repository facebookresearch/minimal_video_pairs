## Reproducibility

### Qwen2-VL 7B

```
python -m accelerate.commands.launch \
  --num_processes=8 \
  -m lmms_eval \
  --model qwen2_vl \
  --model_args pretrained=Qwen/Qwen2-VL-7B-Instruct,max_pixels=151200,max_num_frames=16 \
  --tasks mvp_mini \
  --batch_size 1 \
  --log_samples \
  --log_samples_suffix qwen2_vl \
  --output_path ./logs
```

|                Tasks                |Version|Filter|n-shot|    Metric     |   | Value |   |Stderr|
|-------------------------------------|-------|------|-----:|---------------|---|------:|---|------|
|mvp_mini                             |    N/A|none  |      |pair_accuracy  |↑  |29.2337|±  |   N/A|
|mvp_mini                             |    N/A|none  |      |single_accuracy|↑  |62.2698|±  |   N/A|
| - mvp_mini_human_object_interactions|Yaml   |none  |     0|pair_accuracy  |↑  |32.2851|±  |   N/A|
| - mvp_mini_human_object_interactions|Yaml   |none  |     0|single_accuracy|↑  |63.3648|±  |   N/A|
| - mvp_mini_intuitive_physics        |Yaml   |none  |     0|pair_accuracy  |↑  |18.9171|±  |   N/A|
| - mvp_mini_intuitive_physics        |Yaml   |none  |     0|single_accuracy|↑  |57.0853|±  |   N/A|
| - mvp_mini_robot_object_interactions|Yaml   |none  |     0|pair_accuracy  |↑  |21.2000|±  |   N/A|
| - mvp_mini_robot_object_interactions|Yaml   |none  |     0|single_accuracy|↑  |58.5000|±  |   N/A|
| - mvp_mini_temporal_reasoning       |Yaml   |none  |     0|pair_accuracy  |↑  |44.5328|±  |   N/A|
| - mvp_mini_temporal_reasoning       |Yaml   |none  |     0|single_accuracy|↑  |70.1292|±  |   N/A|

| Groups |Version|Filter|n-shot|    Metric     |   | Value |   |Stderr|
|--------|-------|------|------|---------------|---|------:|---|------|
|mvp_mini|    N/A|none  |      |pair_accuracy  |↑  |29.2337|±  |   N/A|
|mvp_mini|    N/A|none  |      |single_accuracy|↑  |62.2698|±  |   N/A|


### InternVL 2.5 8B

```
python -m accelerate.commands.launch \
  --num_processes=8 \
  -m lmms_eval \
  --model internvl2 \
  --model_args pretrained=OpenGVLab/InternVL2_5-8B,modality=video \
  --tasks mvp_mini \
  --batch_size 1 \
  --log_samples \
  --log_samples_suffix internvl2 \
  --output_path ./logs
```

|                Tasks                |Version|Filter|n-shot|    Metric     |   | Value |   |Stderr|
|-------------------------------------|-------|------|-----:|---------------|---|------:|---|------|
|mvp_mini                             |    N/A|none  |      |pair_accuracy  |↑  |39.9227|±  |   N/A|
|mvp_mini                             |    N/A|none  |      |single_accuracy|↑  |68.2662|±  |   N/A|
| - mvp_mini_human_object_interactions|Yaml   |none  |     0|pair_accuracy  |↑  |38.0853|±  |   N/A|
| - mvp_mini_human_object_interactions|Yaml   |none  |     0|single_accuracy|↑  |67.5926|±  |   N/A|
| - mvp_mini_intuitive_physics        |Yaml   |none  |     0|pair_accuracy  |↑  |23.0645|±  |   N/A|
| - mvp_mini_intuitive_physics        |Yaml   |none  |     0|single_accuracy|↑  |60.1959|±  |   N/A|
| - mvp_mini_robot_object_interactions|Yaml   |none  |     0|pair_accuracy  |↑  |38.7000|±  |   N/A|
| - mvp_mini_robot_object_interactions|Yaml   |none  |     0|single_accuracy|↑  |66.3500|±  |   N/A|
| - mvp_mini_temporal_reasoning       |Yaml   |none  |     0|pair_accuracy  |↑  |59.8410|±  |   N/A|
| - mvp_mini_temporal_reasoning       |Yaml   |none  |     0|single_accuracy|↑  |78.9264|±  |   N/A|

| Groups |Version|Filter|n-shot|    Metric     |   | Value |   |Stderr|
|--------|-------|------|------|---------------|---|------:|---|------|
|mvp_mini|    N/A|none  |      |pair_accuracy  |↑  |39.9227|±  |   N/A|
|mvp_mini|    N/A|none  |      |single_accuracy|↑  |68.2662|±  |   N/A|
