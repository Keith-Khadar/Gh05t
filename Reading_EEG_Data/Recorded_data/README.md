# EEG data collection and labelling

## Overview
This project captures the 8 channel EEG data, processes the received hex values into decimal format, and logs them into a CSV file. The script also records whether the user's eyes are closed based on keyboard input (tab key).

## Files
- eeg_data_to_file.py: The python script for collecting and labelling blinking EEG data (10 seconds).
- labeled_data folder: This folder has 10 csv files of labelled EEG data.
- unlabeled_data folder: This folder has 10 csv files of unlabelled EEG data.

## Features
- Reads data from an ESP32 via a serial connection
- Converts hexadecimal EEG readings into decimal values
- Logs data with a timestamp in a CSV file
- Detects "Eyes closed" state using the `Tab` key by running a background keyboard listener

## Installation
### Prerequisites
Ensure you have Python installed on your system.

### Required Python Packages
Install the required dependencies using pip:
```sh
pip install pynput
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
3. Press the `Tab` key to indicate that your eyes are closed. Release it to reset the state.
4. Press `Esc` to stop the script.

## File Output
The script creates a CSV file (`received_data.csv`) with the following columns:
- Sample index
- EEG data from 8 electrodes (Fp1, Fp2, C3, C4, P7, P8, O1, O2)
- Timestamp
- Eyes closed (1 if `Tab` is pressed, 0 otherwise)

![image](https://github.com/user-attachments/assets/4a46b578-f61c-4438-a378-ca1189c3cf49)
Figure: Sample CSV file

## Note
- The data files can be fed into the machine learning pipeline for gathering valuable insights from blinking data.
- Logging data to a file is a time-intensive process, which may introduce delays in recording all incoming data. As a result, capturing all samples per second may not always be achievable.
