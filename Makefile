## paths
.ONESHELL:
.PHONY: help
.DEFAULT_GOAL := help
SHELL := /bin/bash

## print a help msg to display the comments
help:
	@grep -hE '^[A-Za-z0-9_ \-]*?:.*##.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

USER := $(shell whoami)
PWD := $(shell pwd)
ROOT := $(shell cd ..;  pwd)
HF_HOME:=/home/$(USER)/.cache/huggingface/

prep_evals: # setup files for lmms-eval to run
	cp -Rf tasks/mvp lmms-eval/lmms_eval/tasks/
	cp -Rf models/*.py lmms-eval/lmms_eval/models/
	cp -Rf scripts/*.py lmms-eval/

run_eval_llava_ov: prep_evals
	cd lmms-eval/
	python -m accelerate.commands.launch \
    	--num_processes=8 \
    	-m lmms_eval \
		--model llava_onevision \
		--tasks mvp_mini \
		--batch_size 1 \
		--log_samples \
		--log_samples_suffix llava_onevision \
		--output_path ./logs

run_videochat2: prep_evals
	cd lmms-eval/
	python -m accelerate.commands.launch \
    	--num_processes=8 \
    	-m lmms_eval \
		--model videochat2 \
		--tasks mvp_mini \
		--batch_size 1 \
		--log_samples \
		--log_samples_suffix videochat2 \
		--output_path ./logs

run_internvl2_5: prep_evals
	cd lmms-eval/
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

run_eval_qwen2vl: prep_evals
	cd lmms-eval/	
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

run_eval_internvideo2: prep_evals
	cd lmms-eval/	
	python -m accelerate.commands.launch \
    	--num_processes=8 \
    	-m lmms_eval \
		--model internvideo2 \
		--tasks mvp_mini \
		--batch_size 1 \
		--log_samples \
		--log_samples_suffix internvideo2 \
		--output_path ./logs

run_gemini2: prep_evals
	cd lmms-eval/
	GOOGLE_API_KEY="" python -m accelerate.commands.launch \
    	--num_processes=1 \
    	-m lmms_eval \
		--model gemini_api \
		--model_args model_version=gemini-2.0-flash,timeout=300,continual_mode=False \
		--tasks mvp_mini \
		--batch_size 1 \
		--log_samples \
		--log_samples_suffix gemini_2.0_flash \
		--output_path ./logs

run_gemini2_slurm: prep_evals
	cd lmms-eval/
	GOOGLE_API_KEY="" python -m submit_job \
		--config ../configs/gemini.yaml \
		--tasks mvp_mini \
		--save_loc /checkpoint/amaia/video/koustuvs/experiments/evals/

run_plm: prep_evals
	# conda activate perception_models
	cd lmms-eval/
	python -m accelerate.commands.launch \
    	--num_processes=8 \
    	-m lmms_eval \
		--model plm \
		--model_args pretrained=facebook/Perception-LM-8B \
		--tasks mvp_mini \
		--batch_size 1 \
		--log_samples \
		--log_samples_suffix plm_8B \
		--output_path ./logs

init_env: .env.init 
	source env/bin/activate

.env.init:
	if [ ! -d "env" ]; then
		python3 -m venv env
		source env/bin/activate
		pip install -r requirements.txt
		cd lmms-eval/
		pip install -e .	
	fi
	echo "Setup complete"
	touch .env.init

download_videos: .download.perception_test .download.clevrer .download.grasp .download.inflevel .download.intphys .download.ssv2 .download.star .download.vinoground .download.language_table
	echo "Downloaded all videos"

videos/.init:
	mkdir -p videos
	cp setup/delete_files.py videos/delete_files.py
	touch videos/.init

.download.perception_test: videos/.init
	source env/bin/activate
	cd videos/	
	wget https://storage.googleapis.com/dm-perception-test/zip_data/valid_videos.zip
	unzip valid_videos.zip
	rm valid_videos.zip
	mv videos pt
	python3 delete_files.py pt
	cd ..
	touch $@

.download.clevrer: videos/.init 
	cd videos/
	wget http://data.csail.mit.edu/clevrer/videos/validation/video_validation.zip
	unzip video_validation.zip
	mv video_10000-11000 clevrer
	mv video_11000-12000/* clevrer/
	mv video_12000-13000/* clevrer/
	mv video_13000-14000/* clevrer/
	mv video_14000-15000/* clevrer/
	rm -rf video_11000-12000
	rm -rf video_12000-13000
	rm -rf video_13000-14000
	rm -rf video_14000-15000
	rm video_validation.zip
	cd ..
	touch $@

.download.grasp: videos/.init
	cd videos/
	curl -L -o 'videos.zip' 'https://drive.usercontent.google.com/download?id=1_xPzN0MS3vVlci4yHL5FBH8N_ZpL6mt8&export=download&confirm=t'
	unzip videos.zip
	rm videos.zip
	mv videos grasp
	rm -rf grasp/level1
	cd ..
	touch $@

.download.inflevel: videos/.init 
	cd videos/
	wget https://pub-7320908bcb5b4cdea63c22bc2a38600c.r2.dev/inflevel_lab.tar.gz
	tar -xzf inflevel_lab.tar.gz
	rm inflevel_lab.tar.gz
	mv inflevel_lab inflevel
	cd ..
	touch $@

.download.intphys: videos/.init 
	cd videos/
	source env/bin/activate
	wget https://download-intphys.cognitive-ml.fr/dev.tar.gz
	tar -xzf dev.tar.gz
	rm dev.tar.gz
	cp ../setup/setup_intphys.py setup_intphys.py
	cp ../setup/intphys_pairs.csv intphys_pairs.csv
	python3 setup_intphys.py
	rm -rf dev
	rm setup_intphys.py
	rm intphys_pairs.csv
	cd ..
	touch $@

.download.ssv2: videos/.init 
	cd videos/
	source env/bin/activate
	wget https://apigwx-aws.qualcomm.com/qsc/public/v1/api/download/software/dataset/AIDataset/Something-Something-V2/20bn-something-something-v2-00
	wget https://apigwx-aws.qualcomm.com/qsc/public/v1/api/download/software/dataset/AIDataset/Something-Something-V2/20bn-something-something-v2-01
	unzip 20bn-something-something-v2-00
	unzip 20bn-something-something-v2-01
	cat 20bn-something-something-v2-?? | tar -xvzf -
	mv 20bn-something-something-v2 ssv2
	python3 delete_files.py ssv2
	cp ../setup/setup_ssv2.py setup_ssv2.py
	python3 setup_ssv2.py
	rm setup_ssv2.py
	rm ssv2/*.webm
	cd ..
	touch $@

.download.star: videos/.init 
	cd videos/
	wget https://ai2-public-datasets.s3-us-west-2.amazonaws.com/charades/Charades_v1_480.zip
	unzip Charades_v1_480.zip
	mv Charades_v1_480 star
	python3 delete_files.py star
	cd ..
	touch $@

.download.vinoground: videos/.init 
	source env/bin/activate 
	cd videos/
	huggingface-cli download HanSolo9682/Vinoground --repo-type dataset --local-dir hf_vinoground
	unzip hf_vinoground/vinoground_videos.zip
	mv vinoground_videos vinoground
	rm -rf hf_vinoground
	rm -rf __MACOSX/
	cd ..
	echo "Running vinoground"
	touch $@ 


.download.language_table: videos/.init
	source env/bin/activate	
	mkdir videos/language_table && cd videos/
	cp ../setup/download_lt.py download_lt.py
	cp ../setup/merge_lt.py merge_lt.py
	python3 download_lt.py
	python3 merge_lt.py
	# rm language_table/*.jpg
	rm download_lt.py
	rm merge_lt.py
	cd ..
	touch $@
