# Read Me

## Pre-requisites

To get started, make sure that you have a CUDA 12.x version, with a compatible Ubuntu version. Also make sure to have mini-conda and Python pre-installed.

### Personal Computers:

Create the following environment:

```
conda create --name openmmlab python=3.9 -y
conda activate openmmlab
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
pip install sympy=1.13.1
pip install fsspec

pip install -U openmim
mim install mmengine
mim install "mmcv>=2.0.1, <2.2.0"
mim install "mmdet>=3.1.0, <3.3.0"
```

### Jetson Nano:

```
conda create --name openmmlab python=3.9 -y
conda activate openmmlab
pip3 install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu12

pip install -U openmim
mim install mmengine
mim install "mmcv>=2.0.1, <2.2.0"
mim install "mmdet>=3.1.0, <3.3.0"
```
If the libstdc++ version is causing issues, ensure to install the correct version and assert:
```
LD_PRELOAD=/home/USER/miniconda3/pkgs/libstdcxx-ng-13.2.0-h9a76618_5/lib/libstdc++.so.6 mim install "mmcv>=2.0.1, <2.2.0"
LD_PRELOAD=/home/USER/miniconda3/pkgs/libstdcxx-ng-13.2.0-h9a76618_5/lib/libstdc++.so.6 mim install "mmcv>=2.0.1, <2.2.0"
LD_PRELOAD=/home/USER/miniconda3/pkgs/libstdcxx-ng-13.2.0-h9a76618_5/lib/libstdc++.so.6 mim install "mmdet>=3.1.0, <3.3.0"
```

Clone the mmpose repo, and install all requirements:

```
git clone https://github.com/open-mmlab/mmpose.git
cd mmpose
pip install -r requirements.txt
pip install -v -e .
```

Navigate:

```
cd projects/rtmpose3d
mkdir outputs
mkdir inputs
mkdir checkpoints
```

Download the following configuration and checkpoint files into their respective folders:

```
configs/rtmdet_m_640-8xb32_coco-person.py 
checkpoints/rtmdet_m_640-8xb32_coco-person.pth 
configs/rtmw3d-l_8xb64_cocktail14-384x288.py 
checkpoints/rtmw3d-l_8xb64_cocktail14-384x288.pth
```

## Running the Motion Capture

First, make sure to export the folder:

```
export PYTHONPATH=$PYTHONPATH:/path/to/mmpose/projects/rtmpose3d
```

From the repo, download the following files and move them into the demo folder: 

```
demo/body3d_mocap.py
demo/preprocessing.py
```

To run the motion capture program:

```
python demo/body3d_mocap.py configs/rtmdet_m_640-8xb32_coco-person.py checkpoints/rtmdet_m_640-8xb32_coco-person.pth configs/rtmw3d-l_8xb64_cocktail14-384x288.py checkpoints/rtmw3d-l_8xb64_cocktail14-384x288.pth --input webcam --output-root outputs/ --show --max-bboxes 2 --save-predictions
```

To run the motion estimation program:

```
python demo/motion_estimation.py
```

## TODO:

1) Explicitly make a version that does not display the estimation in real-time.
2) Investigate potential inference speed-up opportunities.
3) Investigate conditions for optimal performance. 
