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
   pip install bleak matplotlib numpy
   ```

## Setup Instructions

### 1. ESP32-C6 Setup

### 2. Clone the Repository
Clone the respository with GUI code

```bash
git clone https://github.com/Keith-Khadar/Gh05t
cd EEG_GUI
```

### 3. Update Configuration
Edit the `bleak.py` file, under utils folder, to update the ESP32-C6 service and characteristic UUID:

```python
SERVICE_UUID = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"  # Replace with ESP32 Service UUID
CHARACTERISTIC_UUID = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" # Replace with ESP32 Characteristic UUID
```

### 4. Run the GUI
Ensure the computer is connected to the ESP32-C6 via bluetooth and run the main script to start the GUI:

```bash
python gui.py
```

## Code Architecture

- **`gui.py`**: Main script for the GUI.
- **`utils/`**: Folder containing all the helper classes and functions.
  - **`bleak.py`**: Creates client to recieve incoming information from the Xiao ESP32 BLE server.
  - **`frequency.py`**: Plots a frequnecy spectrum of the signals.
  - **`grid.py`**: Controls the grid display of all the plots.
  - **`ratio.py`**: Plots a MNE, topomap, of the locations of the electrodes relative to the head.
  - **`waveform.py`**: Plots all the channel signals in a time plot. 
- **`requirements.txt`**: List of required Python libraries.

## Troubleshooting
- There is no recorded bugs.

## Future Work

- The GUI can currently only read from .edf files when uploading. Future work would include expanding the capabilities to .csv, .dat, and .txt files. 
- Apply ability for the user to change the layout or types of plots shown.
- Add the capability to import ML model to plot markers or notes on the waveform.
- When connected to bluetooth, only the waveform plot uses the information in real-time. The frequency and topomap needs to also be updated. 

