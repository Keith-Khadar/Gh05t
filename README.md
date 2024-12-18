# Gh05t

## Project Overview

This project aims to design and develop an EEG headset. The headset will have a compact design, integrated into a removable hat to provide comfort and discreteness. It will be equipped with at least 4 electrodes with the modularity to add additional electrodes if required/desired. The electrodes will connect to an ADC purpose designed for measuring weak signals. The samples generated by the ADC will be sampled by a micro-controller. Using an ESP32 (Seeed Studio XIAO ESP32C6), we can communicate wirelessly and sample at high frequency rates for a low cost. It will communicate with a computer for analysis by a machine learning (ML) model to detect gestures or possibly speech; potentially adding integration with Virtual-Reality. Lastly, the system will also interface with a GUI, allowing users to visualize the EEG data in real-time. We can leverage multiple open-source libraries available through OpenBCI and PiEEG for displaying the GUI.

## Completed Work/In Progress

- **Custom Headset**: Design in progress
- **Custom Electrodes**: Preliminary testing complete - redesign required
- **Custom PCB Breakout Board**: WIP - Schematic and layout complete, soldering in progress
- **Bluetooth Communication**: Demonstrates multichannel data acquisition from an ESP32-C6 board, transmitted via BLE to a laptop, stored in an `.npz` or `.csv` file, and visualized through a plot as proof of concept.
- **Front End Gui**: Proof of concept complete
- **Pose Machine Learning Model**: Proof of concept complete - Refinement Needed
- **EEG Machine Learning Model**: Research phase

## Project Architecture

The architecture of the project is structured as follows:

![GH05T_Architecture](https://github.com/user-attachments/assets/8cabfe92-2fb6-45d9-b9c0-2a09e933ab1f)
### **Hardware**:
---
![GH05T_Hardware](https://github.com/user-attachments/assets/a39db358-9035-4293-9c11-b8de8aaff7cf)
- **CAD**: Custom electrodes made from conductive PLA
- **PCB**: Custom breakout board for ADS1299 ADC
- **Components**: ESP32 (Seeed Studio XIAO ESP32C6), LiPo Battery

### **Software**:
---
![GH05t_Software](https://github.com/user-attachments/assets/494d2cf8-fc81-4a13-91d9-89d26b5bed49)
- **BLE(Bluetooth Low Energy)**: Serialized communication over bluetooth from the Xiao ESP32-C6 to the computer with the GUI or ML model for training.
- **GUI**:
  - Framework:
    - [tkinter](https://docs.python.org/3/library/tkinter.html) & [Matplotlib](https://matplotlib.org/): EEG Graphical User Interface
    - [Bleak](https://pypi.org/project/bleak/): Bluetooth interface library for python
    - [EEGLib](https://eeglib.readthedocs.io/en/latest/index.html): Python library designed for analyzing and processing EEG data
  - Features:
    - Real-time data streaming from Xiao ESP32-C6
    - Ability to upload pre-recorded EEG files, edf
    - Visualize EEG data in a time, frequency, and electrode topography map
  - Styling: WIP
 
- **EEG Signal Pre-processing**:
  - Format:
    - Input: Raw 4 channel electrode data
    - Output: K-Independent Signals (Components)
  - Processing Options:
    - FastICA or JADE: Fast Inference
    - InfoMax or EInfoMax: Versatility & Robustness

- **EEG Signal Machine Learning**:
  - Format:
    - Input: K-Independent Signals (Components)
    - Output: 3D-Pose using 133 Keypoints
  - Target:
    - [RTMPose3d](https://github.com/open-mmlab/mmpose/tree/main/projects/rtmpose3d): Multi-person 3D Pose Estimator, generates Pose Information
    - Motion Estimates: Process pose data to generate *relative* motion estimates
    - [Demo](./pose-recognition/DEMO_GH05T.mp4)
  - Model:
    - Structure: Artifical Neural Network (Regressor)
    - Pre-Training: PCA-Pretraining for optimal features
    - Training: Network Tuning based on Target Data

## Known Bugs

- ~~**Pose ML Model Offset**: The pose recognition machine learning model offsets the generated skeleton by a set amount. ![image](https://github.com/user-attachments/assets/c28c0a2e-da3d-4fa4-a920-4a78a1bb0804)~~

## Difficulties/Challenges

- **3D Printing Fail**: Weak legs on 3D electrodes
  - The initial model found and used for the electrodes has spindly legs. In combination with two snaps of the filament during printing, the legs were incredibly weak and many snapped during removal from the print bed.
  - Fix: Load filament onto spool to eliminate snapping during print. Custom design electrodes with filleted legs to enhance their strength. Increase the number of walls when slicing model for printing.
  - Above fix solved combined with printing on a higher quality printer and in a different orientation fixed the issues. 
- **Snap Plating**: Purchased snaps are covered in non-conductive coating
  - Prevented soldering, but can be scrapped off with a knife.
  - Reduces signal integritty of electrodes.
  - Fix: Looking into alternative unplated snap connectors.
  - Above fix solves the issue in initial testing. Will continue to monitor as further testing is conducted.
- **Inaccurate EEG Data**: Data recorded during initial testing is inaccurate.
  - The poor quality electrodes(see snap plating challenge & 3d printing fail) as well as the ADC optimized for Electromyography (EMG) data recording instead of the use case of Electroencephalography (EEG), resulted in poor quality data.
  - Fix: Custom designed PCB breakout board for the ADS1299 which is designed for EEG data acquisition.
  - Update: Fix in progress
- **Reflow Issus**: Solder pads bridged during reflow of PCB.
  - Fix: Use flux and a hand solder iron to fix individual pads OR reattempt the reflow.
  - Update: Fix in progress

## License

## Contact
