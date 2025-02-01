# Real-Time EEG Visualization GUI

## Overview

The Graphic User Interface (GUI) is a Python-based real-time visualization tool for viewing multi-channel EEG data over Bluetooth from an ESP32-C6 microcontroller. 

#### Features

- **Real-Time Data Visualization**: Plots live EEG data for multitude of channels.
- **BLE Connectivity**: Connects to an ESP32-C6 device via Bluetooth.
- **Read Pre-recorded files**: The GUI supports various file types: edf, csv, tsv, dat, and txt.
- **Customizable GUI**: Easy to adapt for additional features like saving data or adjusting plot parameters.

#### Dependencies
1. **Hardware**
    - ESP32-C6 microcontroller (sending EEG signals)
2. **Software**
    - Python 3.7+
    - Bluetooth support on host computer
3. **Libraries**
    - Install Python libraries using:

```bash
pip install PyQt bleak matplotlib numpy
```

## Setup Instructions

### 1. ESP32-C6 Setup
Flash the ```esp32_ble_eeg.ino``` program to the ESP32-C6 board using either Arduino IDE or PlatformIO. Ensure the output of the ESP32-C6 reports the BLE server broadcasting.

### 2. Clone the Repository
Clone the respository with GUI code

```bash
git clone https://github.com/Keith-Khadar/Gh05t
cd EEG_GUI_PYQT
```

### 3. Update Configuration
Edit the `ble_manager_.py` file, under utils folder, to update the ESP32-C6 service and characteristic UUID:

```python
SERVICE_UUID = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"  # Replace with ESP32 Service UUID
CHARACTERISTIC_UUID = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" # Replace with ESP32 Characteristic UUID
```

### 4. Run the GUI
Run the main script to start the GUI. The python script will scan for bluetooth devices automatically when the option is selected.

```bash
python main.py
```

## Code Architecture

- **`main.py`**: Main script for the GUI.
- **`utils/`**: Folder containing all the helper classes and functions.
  - **`ble_handler_.py`**: Creates client to recieve incoming information from the Xiao ESP32 BLE server.
  - **`plot_manager.py`**: Plots various types of Graphs specified by the user.
  - **`grid_manager.py`**: Controls the grid display of all the plots.
  - **`file_handler.py`**: Handles the file uploading, handling, and exporting for data. 
- **`requirements.txt`**: List of required Python libraries.

## Troubleshooting/Known Bugs
- Adding the FFT plot will replace the currently shown plot. It doesn't add the new plot next to the pre-existing one. 

## Future Work
- The GUI can currently only read from .edf files when uploading. Future work would include expanding the capabilities to .csv, .dat, and .txt files. 
- Apply ability for the user to change the layout and/or add more plot selections.
- Add the capability to import ML model to plot markers or notes on the waveform.
- The EEG topography map is not connected to real information. In the future, this will be show the real locations of the electrodes on the headset and determine the contour lines/distribution frequency on the head. 

