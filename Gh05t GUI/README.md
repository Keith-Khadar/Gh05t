# Real-Time EEG Visualization GUI
## Overview

The Graphic User Interface (GUI) is a Python-based real-time visualization tool for viewing multi-channel EEG data over Bluetooth from an ESP32 microcontroller. 

#### Features

- **Real-Time Data Visualization**: Plots live EEG data for multitude of channels in various formats: time, polar fft, and fft.
- **Various forms of data input**: The user has multiple data input options, allowing them flexibility to use various types of hardware.
- **Read Pre-recorded files**: The GUI supports edf and csv.
- **Customizable GUI**: Easy to adapt for additional features like saving data or adjusting plot parameters.
- **Export files**: Can export the incoming data.

#### Dependencies
1. **Hardware** (Optional)
    - **ADS1299 PCB**: Navigate to the esp32 folder, ```esp32\README.md```, for specific setup instructions for Firebeetle ESP32.
    - **Low Cost**: Navigate to the Low Cost folder, ```rpi_low_cost\gh0st\README.md```, for specific setup instructions for the RPi Pico W.
2. **Software**
    - Python 3.7+
    - Bluetooth support on host computer
3. **Libraries**
    - Refer to ```requirements.txt``` to install supporting Python libraries

## Setup Instructions

#### 1. Install Dependencies
Using the ```requirements.txt```, install the library dependencies required for the GUI to run for your environment.

#### 2. Run the GUI
Run the main script to start the GUI. The python script will scan for bluetooth devices automatically when the option is selected.

```bash
python main.py
```

#### 3*. (Optional) Connect to WebSocket Host
The GUI automatically opens the WebSocket at start up. It only broadcasts labels, which requires the user to enable the manual or ML labeling in order to start broadcasting the information. The WebSocket URL is shown to the user next to the Data Input button (the IP4 Addr of the local machine with the PORT number).

The WebSocket broadcasts the labels for the benefit of external applications. For more information, refer to ```Applications``` folder in the repository.

## Code Architecture

- **`main.py`**: Main script for the GUI.
- **`utils/`**: Folder containing all the helper classes and functions.
  - **`ble_handler_.py`**: Creates client to recieve incoming information from the ESP32 BLE server.
  - **`file_handler.py`**: Handles the file uploading, handling, and exporting for data. 
  - **`plot_manager.py`**: Plots various types of Graphs specified by the user.
  - **`signal_processing.py`**: Creates filters and applies signal processing to incoming data.
  - **`websocket_handler.py`**: Handles the websocket communication for the low cost hardware data input. 
- **`resource/`**: Contains any png or supporting files for the GUI
- **`example_eeg_data/`**: Includes eeg data that can be used to test the visualizer.
- **`data/`**: Holds the binary folder where the incoming data will be stored before export. Additionally can be a folder to hold an exported data files.
- **`test/`**: Contains all the unit testing for the GUI.
- **`requirements.txt`**: List of required Python libraries.

## GUI Navigation
The user first must specify how they are inputting data to be read. There are four options to the user for inputting data:
- **ADS1299 PCB**: This is if the user created their own PCB with the ADS1299 chip which communicates to a DFRobot Firebeetle ESP32 development board and sends the data via BLE.
- **Low Cost**: This is if the user does not have the ADS1299 and creates their own low cost breadboard/featherboard circuit that uses an external 12-bit ADC to communicate with the DFRobot Firebeetle ESP32 development to send data over BLE.
- **File Import**: If the user has no hardware to interface with, file import is supported for type .edf.

![Image](https://github.com/user-attachments/assets/1f83893d-0a6c-4ae3-8a1f-48e3472557cb)

Once the data is imported, the user has the ability to add and remove plots from the visual. They can play or stop the incoming data stream to look closer at the plots. Additionally, there is a button to allow the user to export the data if they want to create a local file on their machine with the incoming data stream.

## Troubleshooting/Known Bugs
- None.

## Future Work
- The GUI can currently only read from .edf files when uploading. Future work would include expanding the capabilities to .dat and .txt files. 
- Add the ability to scrub through the data on a timeline.
- Package the GUI into a single .EXE once completed with features. This will be done with PyInstaller.