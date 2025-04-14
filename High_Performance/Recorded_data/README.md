# EEG data collection and labelling

## Overview
This project captures the 8 channel EEG data, processes the received hex values into decimal format, and logs them into a CSV file. The script also allows live labeling of data based on whether the user’s eyes are open or closed, using simple keyboard input ('c' for closed, 'o' for open).

## Features
- Reads data from an ESP32 via a serial connection.
- Converts hexadecimal EEG readings into decimal values.
- Logs data with a timestamp in a CSV file.
- Allows real-time labeling using the keyboard:
'c' → Mark as "eyes closed"
'o' → Mark as "eyes open"
- Keyboard listener runs in a background thread while collecting data.

## Installation
### Prerequisites
Ensure you have Python installed on your system.

### Required Python Packages
Install the required dependencies using pip:
```sh
pip install pyserial
```

## Hardware Setup
1. Connect the ESP32 + ADS1299 development board to your computer via a USB-C cable.
2. Ensure the correct serial port (`COM4` in this case) is selected in the script.

## Usage
1. Run the script:
   ```sh
   python3 eeg_data_to_file.py
   ```
2. The script will automatically start listening for incoming serial data.
3. Press the `c` key to indicate that your eyes are closed and press `o` key to indicate that your eyes are open.
4. Press `Ctrl+C` to stop the script.

## File Output
The script creates a CSV file (`received_data.csv`) with the following columns:
- Sample index
- EEG data from 8 electrodes (Fp1, Fp2, C3, C4, P7, P8, O1, O2)
- Timestamp
- Eyes closed (1 if `Tab` is pressed, 0 otherwise)

![image](https://github.com/user-attachments/assets/5133e521-4e2c-4f54-bab3-1245036c9915)
Figure: Sample CSV file

## Note
- The data files can be fed into the machine learning pipeline for gathering valuable insights from blinking data.
- Logging data to a file is a time-intensive process, which may introduce delays in recording all incoming data. As a result, capturing all samples per second may not always be achievable.
