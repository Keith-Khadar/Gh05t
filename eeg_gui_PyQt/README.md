# Real-Time EEG Visualization GUI

## Overview

The Graphic User Interface (GUI) is a Python-based real-time visualization tool for viewing multi-channel EEG data over Bluetooth from an ESP32 microcontroller. 

#### Features

- **Real-Time Data Visualization**: Plots live EEG data for multitude of channels.
- **BLE Connectivity**: Connects to an ESP32 device via Bluetooth.
- **Read Pre-recorded files**: The GUI supports various file types: edf, csv, tsv, dat, and txt.
- **Customizable GUI**: Easy to adapt for additional features like saving data or adjusting plot parameters.
- **Export files**: Can export the data retrieved over BLE and provides the option to the user select file type.

#### Dependencies
1. **Hardware**
    - ESP32-C6 microcontroller (sending EEG signals)
2. **Software**
    - Python 3.7+
    - Bluetooth support on host computer
3. **Libraries**
    - Refer to requirements.txt to install supporting Python libraries

## Setup Instructions

### 1. ESP32 Setup
Refer to the ESP32 folder, ```esp32\README.md```, for specific setup instructions

### 2. Install Dependencies
Using the requirements.txt, install the library dependencies required for the GUI to run for your environment.

### 3. Run the GUI
Run the main script to start the GUI. The python script will scan for bluetooth devices automatically when the option is selected.

```bash
python main.py
```

## Code Architecture

- **`main.py`**: Main script for the GUI.
- **`utils/`**: Folder containing all the helper classes and functions.
  - **`ble_handler_.py`**: Creates client to recieve incoming information from the ESP32 BLE server.
  - **`plot_manager.py`**: Plots various types of Graphs specified by the user.
  - **`file_handler.py`**: Handles the file uploading, handling, and exporting for data. 
- **`resource/`**: Contains any png or supporting files for the GUI
- **`example_eeg_data/`**: Includes eeg data that can be used to test the visualizer.
- **`test/`**: Contains all the unit testing for the GUI.
- **`requirements.txt`**: List of required Python libraries.

## Troubleshooting/Known Bugs
- None.

## Future Work
- The GUI can currently only read from .edf files when uploading. Future work would include expanding the capabilities to .csv, .dat, and .txt files. 
- Apply ability for the user to change the layout and/or add more plot selections.
- Add the capability to import ML model to plot markers or notes on the waveform.
- The EEG topography map is not connected to real information. In the future, this will be show the real locations of the electrodes on the headset and determine the contour lines/distribution frequency on the head. 
