# BLE Single channel ADC Communication with ESP32-C6

## Overview
The code demonstrates a successful setup of a BLE (Bluetooth Low Energy) communication between an ESP32-C6 board and a Python script using the `bleak` library.

![image](https://github.com/user-attachments/assets/9fc3b1ea-21c7-4ed2-8131-7ace7a2a633e)
Figure: XIAO ESP32C6 Pin list (https://wiki.seeedstudio.com/xiao_pin_multiplexing_esp33c6/)

<p align="center">
  <img src="https://github.com/user-attachments/assets/b415cdd3-fc51-4de3-aa8b-a30394841169" alt="Circuit design" />
</p>
Figure: The circuit design for testing the code. (The breadboard has been excluded to enhance clarity.)

## Files

### **ESP32_SingleChannel_BLE.ino:**
1. **BLE Initialization**:
   - The `BLEDevice` library is used to create and manage BLE services and characteristics.
   - The BLE service (`SERVICE_UUID`) and characteristic (`CHARACTERISTIC_UUID`) are defined with unique UUIDs.

2. **BLE Characteristic**:
   - The characteristic allows both read and write operations, permitting interaction between the ESP32 and a BLE client.

3. **Analog Input**:
   - The ESP32 reads an analog value from pin `A0`, processes it, and updates the BLE characteristic with the new value in string format.
   - The characteristic notifies the connected BLE client of updates to the value.

4. **Advertising**:
   - The BLE device advertises itself under the name `XIAO_ESP32C6`, allowing it to be discovered by BLE clients like the Python script.

5. **Loop Function**:
   - In the `loop`, the analog value is read every 2 seconds, converted to a string, and updated to the BLE characteristic.
   - The updated value is notified to the BLE client, ensuring real-time data transfer.

### **ConnectToESP32.py:**
1. **Scanning for Devices**:
   - The script scans for nearby BLE devices and looks for a device named `XIAO_ESP32C6`.

2. **Connecting to the ESP32**:
   - If the ESP32 is found, the script connects to it using its BLE address.

3. **Reading BLE Characteristic**:
   - The script reads the BLE characteristic (`CHARACTERISTIC_UUID`) in a loop. This receives the analog values sent by the ESP32.

4. **Data Handling**:
   - The script decodes the received data (`UTF-8` format) and prints it to the console.
   - The loop runs 20 iterations with a 1-second delay between reads, providing continuous data monitoring.


## Prerequisites

### Hardware Requirements:
- ESP32-C6 module
- Breadboard
- Power supply (in our case laptop USB connection)
- Appropriate wiring for analog input (channel A0) 
- Potentiometer

### Software Requirements:
- Arduino IDE for programming the ESP32
- VS Code/ PyCharm
- Python 3.7+ with the following installed:
  `bleak` (Python BLE library)
  `pip install bleak`

## Commands
Run the following command after loading the ESP32 board with the program ESP32_SingleChannel_BLE.ino using Arduino IDE:
python3 ConnectToESP32.py

## Important Notes

- **Ensure the `.npz` File Exists Before Running the Program:**  
  The Python script attempts to read `input_data.npz` after saving data. If this file is deleted or unavailable, the program will fail to load data.

- **Configured for Windows device:**  
  The code has been tested on a Windows laptop.

## Sample Output
![image](https://github.com/user-attachments/assets/e224dcb2-3c19-457a-a340-7501aabee496)

Figure: Output for ESP32_SingleChannel_BLE.ino in Arduino IDE.

![image](https://github.com/user-attachments/assets/08a7d620-5892-4689-b54e-f446c59a353c)
Figure: Output for ConnectToESP32.py.
