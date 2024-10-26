# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import itertools
import multiprocessing as mp
import os
import time
import warnings
from argparse import ArgumentParser
from collections import defaultdict
from functools import partial
from multiprocessing import cpu_count, Pool, Process
from typing import List, Optional, Sequence, Union

import cv2
import json_tricks as json
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from adhoc_image_dataset import AdhocImageDataset
from classes_and_palettes import (
    COCO_KPTS_COLORS,
    COCO_WHOLEBODY_KPTS_COLORS,
    GOLIATH_KPTS_COLORS,
    GOLIATH_SKELETON_INFO,
    COCO_SKELETON_INFO,
    COCO_WHOLEBODY_SKELETON_INFO
)
from pose_utils import nms, top_down_affine_transform, udp_decode

from tqdm import tqdm

from worker_pool import WorkerPool

try:
    from mmdet.apis import inference_detector, init_detector
    from mmdet.structures import DetDataSample, SampleList
    from mmdet.utils import get_test_pipeline_cfg

    has_mmdet = True
except (ImportError, ModuleNotFoundError):
    has_mmdet = False


warnings.filterwarnings("ignore", category=UserWarning, module="torchvision")
warnings.filterwarnings("ignore", category=UserWarning, module="mmengine")
warnings.filterwarnings("ignore", category=UserWarning, module="torch.functional")
warnings.filterwarnings("ignore", category=UserWarning, module="json_tricks.encoders")

timings = {}
BATCH_SIZE = 48


def preprocess_pose(orig_img, bboxes_list, input_shape, mean, std):
    """Preprocess pose images and bboxes."""
    #print(f"Original image shape: {orig_img.shape}")
    preprocessed_images = []
    centers = []
    scales = []
    for bbox in bboxes_list:
        img, center, scale = top_down_affine_transform(orig_img.copy(), np.array(bbox))
        img = cv2.resize(
            img, (input_shape[1], input_shape[0]), interpolation=cv2.INTER_LINEAR
        ).transpose(2, 0, 1)
        #print(f"Resized and transposed image shape: {img.shape}")  # Confirm resized shape
        img = torch.from_numpy(img)
        img = img[[2, 1, 0], ...].float()
        mean = torch.Tensor(mean).view(-1, 1, 1)
        std = torch.Tensor(std).view(-1, 1, 1)
        img = (img - mean) / std
        preprocessed_images.append(img)
        centers.extend(center)
        scales.extend(scale)
    return preprocessed_images, centers, scales

def batch_inference_topdown(
    model: nn.Module,
    imgs: List[Union[np.ndarray, str]],
    dtype=torch.bfloat16,
    flip=False,
):
    with torch.no_grad(), torch.autocast(device_type="cuda", dtype=dtype):
        imgs_tensor = torch.stack(imgs).cuda()  # Stack list of images into a tensor and move to GPU
        heatmaps = model(imgs_tensor)
        if flip:
            heatmaps_ = model(imgs_tensor.flip(-1))
            heatmaps = (heatmaps + heatmaps_) * 0.5
    return heatmaps.cpu()


def img_save_and_vis(
    img, results, input_shape, heatmap_scale, kpt_colors, kpt_thr, radius, skeleton_info, thickness
):
    """Draw keypoints and skeleton directly on the image for real-time visualization."""
    #print(f"Frame shape before overlay: {img.shape}")
    heatmap = results["heatmaps"]
    centres = results["centres"]
    scales = results["scales"]
    instance_keypoints = []
    instance_scores = []
    x_offset = 0
    y_offset = 0
    x_scale = 1
    y_scale = 1
    #x_scale = 640/1024
    #y_scale = 480/768

    for i in range(len(heatmap)):
        result = udp_decode(
            heatmap[i].cpu().unsqueeze(0).float().data[0].numpy(),
            input_shape,
            (int(input_shape[0] / heatmap_scale), int(input_shape[1] / heatmap_scale)),
        )

        keypoints, keypoint_scores = result
        keypoints = (keypoints / input_shape) * scales[i] + centres[i] - 0.5 * scales[i]
        instance_keypoints.append(keypoints[0])
        instance_scores.append(keypoint_scores[0])

    instance_keypoints = np.array(instance_keypoints).astype(np.float32)
    instance_scores = np.array(instance_scores).astype(np.float32)

    for kpts, score in zip(instance_keypoints, instance_scores):
        for kid, kpt in enumerate(kpts):
            if score[kid] < kpt_thr or kpt_colors[kid] is None:
                continue
            kpt_shifted = (int((kpt[0] + x_offset)*x_scale), int((kpt[1] + y_offset)*y_scale))
            color = tuple(int(c) for c in kpt_colors[kid][::-1])
            img = cv2.circle(img, kpt_shifted, int(radius), color, -1)

        for skid, link_info in skeleton_info.items():
            pt1_idx, pt2_idx = link_info['link']
            color = link_info['color'][::-1]  # BGR

            if pt1_idx < len(kpts) and pt2_idx < len(kpts):
                pt1, pt1_score = kpts[pt1_idx], score[pt1_idx]
                pt2, pt2_score = kpts[pt2_idx], score[pt2_idx]
                
                if pt1_score > kpt_thr and pt2_score > kpt_thr:
                    x1, y1 = int((pt1[0]+x_offset)*x_scale), int((pt1[1]+y_offset)*y_scale)
                    x2, y2 = int((pt2[0]+x_offset)*x_scale), int((pt2[1]+y_offset)*y_scale)
                    cv2.line(img, (x1, y1), (x2, y2), color, thickness=max(1, thickness))
    #print(f"Overlaying skeleton on frame of shape: {img.shape}")
    #img = cv2.resize(img, (640, 480))
    return img


def fake_pad_images_to_batchsize(imgs):
    return F.pad(imgs, (0, 0, 0, 0, 0, 0, 0, BATCH_SIZE - imgs.shape[0]), value=0)

def load_model(checkpoint, use_torchscript=False):
    if use_torchscript:
        return torch.jit.load(checkpoint)
    else:
        return torch.export.load(checkpoint).module()
    
def check_camera_dimensions():

    # Open camera
    cap = cv2.VideoCapture(0)

    # Check if the camera opened successfully
    if not cap.isOpened():
        print("Error: Could not open video.")
    else:
        # Get current camera width and height
        current_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        current_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"Current camera resolution: {current_width}x{current_height}")

        # Set desired resolution (e.g., 640x480 or 1920x1080)
        desired_width = 1920  # or other width like 640
        desired_height = 1080  # or other height like 480
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, desired_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, desired_height)

        # Check if the resolution was set correctly
        new_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        new_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"New camera resolution: {new_width}x{new_height}")

        # Capture a frame to test the resolution
        ret, frame = cap.read()
        if ret:
            cv2.imshow('Camera Frame', frame)
            cv2.waitKey(0)
        else:
            print("Failed to capture frame.")

        # Release resources
        cap.release()
        cv2.destroyAllWindows()

def main():
    """Main loop for real-time pose estimation."""
    # Model initialization
    pose_checkpoint = '/home/jibby2k1/Documents/CpE1/Gh05t_Design/checkpoints/sapiens_0.3b_coco_best_coco_AP_796_torchscript.pt2'
    pose_estimator = load_model(pose_checkpoint, use_torchscript=True)
    pose_estimator.eval().to("cuda" if torch.cuda.is_available() else "cpu")

    cap = cv2.VideoCapture(0)  # Open webcam
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1024)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 768)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Preprocess frame
        preprocessed_image, centers, scales = preprocess_pose(frame, [[0, 0, frame.shape[1], frame.shape[0]]], (1024, 768), [123.5, 116.5, 103.5], [58.5, 57.0, 57.5])
        
        # Inference
        with torch.no_grad():
            # Ensure input tensor is 4D: [batch_size, channels, height, width]
            input_tensor = preprocessed_image[0].unsqueeze(0).to("cuda" if torch.cuda.is_available() else "cpu")
            pose_results = pose_estimator(input_tensor)

        # Process results for visualization
        results = {
            "heatmaps": [pose_results[0].cpu()],
            "centres": centers,
            "scales": scales
        }
        frame = img_save_and_vis(frame, results, (1024, 768), heatmap_scale=4, kpt_colors=COCO_KPTS_COLORS, kpt_thr=0.3, radius=9, skeleton_info=COCO_SKELETON_INFO, thickness=2)

        # Display frame
        cv2.imshow("Pose Estimation", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Run the function
    #check_camera_dimensions()
    main()