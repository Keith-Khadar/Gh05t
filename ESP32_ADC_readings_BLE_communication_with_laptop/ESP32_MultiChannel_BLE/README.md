# BLE Multichannel ADC Communication with ESP32-C6

## Overview
A two-part implementation to communicate between an ESP32-C6 board and a laptop via Bluetooth Low Energy (BLE). 
The ESP32 reads multichannel analog signals and sends the data to a connected device using BLE. On the computer side, a Python program connects to the ESP32, 
receives the data, and stores it in a file and plots the voltage readings.

![image](https://github.com/user-attachments/assets/9fc3b1ea-21c7-4ed2-8131-7ace7a2a633e)
Figure: XIAO ESP32C6 Pin list (https://wiki.seeedstudio.com/xiao_pin_multiplexing_esp33c6/)

<p align="center">
  <img src="https://github.com/user-attachments/assets/f12b0e81-636c-47bd-9117-992593881405" alt="Circuit design" />
</p>
Figure: The circuit design for testing the code. (The breadboard has been excluded to enhance clarity.)

## Files
1. **ESP32_MultiChannel_BLE.ino**  : Reads analog signals from three channels,convert the readings into voltage value and sends the voltage values via a BLE characteristic.
2. **ConnectToESP32.py**  : Scans for the ESP32 BLE device, connects and reads BLE data from the ESP32 and then saves the received data to an `.npz` file for later use.
3. **input_data.npz**  : Contains the ESP32 BLE transmitted data.
4. **PlotGraph.py**  : Reads input_data.npz, processes the data for three channels, and visualizes it live in a Tkinter GUI using Matplotlib.
Place the input_data.npz file in the same directory as PlotGraph.py.

## Prerequisites

### Hardware Requirements:
- ESP32-C6 module
- Breadboard
- Power supply (in our case laptop USB connection)
- Appropriate wiring for analog inputs (channels A0, A1, A2) 
- Three potentiometers

### Software Requirements:
- Arduino IDE for programming the ESP32
- VS Code/ PyCharm configured for python
- Python 3.7+ with the following installed:
  - `bleak` (Python BLE library)
  - `numpy` (for saving data)
- Ensure Python packages like asyncio, numpy, tkinter, matplotlib, and threading are installed.
`pip install numpy \\
pip install matplotlib \\
sudo apt-get install python3-tk \\
pip install bleak`

## Usage Instructions

### 1. Setup ESP32
- Flash the `ESP32_MultiChannel_BLE.ino` program to the ESP32-C6 board.
- The program advertises the ESP32 as `XIAO_ESP32C6` over BLE.

### 2. Run the Python Programs
- Ensure that the ESP32 is powered on and within range.
- Run the following command after loading the ESP32 board with the ESP32_MultiChannel_BLE.ino program using Arduino IDE.
- Run the Python script:
  `python3 ConnectToESP32.py`
- The ConnectToESP32.py script will:
  1. Scan for the ESP32 by its BLE name.
  2. Connect and read voltage values from the BLE characteristic.
  3. Save the received data to `input_data.npz`.

### 3. Analyze Saved Data
- Run the Python script:
  python3 PlotGraph.py
- The PlotGraph.py script will:
  1. Read data stored in `input_data.npz`.
  2. Plot a graph fo all three channels using these values. 

## Important Notes

- **Ensure the `.npz` File Exists Before Running the Program:**  
  The Python script attempts to read `input_data.npz` after saving data. If this file is deleted or unavailable, the program will fail to load data.

- **Configured for Windows device:**  
  The code has been tested on a Windows laptop.

## Sample Output

![image](https://github.com/user-attachments/assets/07d5cbc3-f2a9-4058-a162-9bed9cb160d9)

Figure: Output for ESP32_MultiChannel_BLE.ino in Arduino IDE.

![image](https://github.com/user-attachments/assets/5b5c8dd7-9db4-4875-a4f4-b1ec18e5f7ae)

Figure: Output for ConnectToESP32.py.

![image](https://github.com/user-attachments/assets/68eec393-f5ee-42b3-a0f7-db8e0e0fb0fb)

Figure: Output for PlotGraph.py.

Link to code demo:
(https://uflorida-my.sharepoint.com/:v:/g/personal/stuti_ruparel_ufl_edu/ESNoCNtR7i9FpQU0D6yvmBcBnizOJJ-Oh_DsOwetzQaeqw?e=tKyc3b&nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJTdHJlYW1XZWJBcHAiLCJyZWZlcnJhbFZpZXciOiJTaGFyZURpYWxvZy1MaW5rIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXcifX0%3D)
