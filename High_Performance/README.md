# High-Performance Microcontroller Board

## Overview:
The High-Performance Microcontroller Board integrates a 24-bit ADC to capture high-resolution EEG signals and transmits the data wirelessly using an ESP32-based development board. 
The setup allows seamless data transfer to an ESP32-C6 module, which then relays the EEG data over WiFi (ESPNOW) to a connected laptop for analysis and visualization.
![image](https://github.com/user-attachments/assets/9b8633bc-526a-4d3a-a7fb-4e275b2d3879)

Figure:EEG dataset pipeline from data collection to visualization

## System workflow:
1. EEG signals are captured from snap electrodes and processed using an ESP32 development board.
2. The ESP32 development board transmits the 8-channel EEG data wirelessly via ESPNOW to the ESP32-C6 module.
3. The ESP32-C6 receives the data and relays it to the Arduino Serial Monitor for verification.
4. A Python script captures the data from the laptop's serial port and records it in a text file. 
5. The data is formatted for compatibility with the OpenBCI GUI for visualization and further analysis.
6. Additionally, another python script records the labeled data in csv file for evaluation using the machine learning pipeline.
7. Filtering techniques are applied to extract alpha wave frequencies (8-10 Hz), confirming the presence of neural activity.
8. Initial testing involved verifying ADC readings with a DC voltage input, ensuring data accuracy before integrating electrodes.
   ![data collection stages](https://github.com/user-attachments/assets/1ad5dc23-a819-4ac8-99bb-d55ae5c50f29)

## Data transmission and performance
1. The system initially transmitted data at **1 sample per second** to establish a stable connection.
2. Once stable, the sampling rate was increased to **250 samples per second**.
3. ESPNOW protocol was used to establish a reliable WiFi link between the ESP32 devices.
4. The hardware was validated by successfully detecting alpha waves, demonstrating its efficiency in EEG signal acquisition.

## Key features of the High-Performance Microcontroller Board
1. **Optimized PCB design**: The board features a **four-layer PCB**, minimizing ground and supply plane resistance to reduce noise.
2. **High-resolution ADC**: The **ADS1299** offers a **96 dB PSRR at 60 Hz**, ensuring minimal interference and high precision.
3. **Battery-powered operation**: Runs on a **low-resistance rechargeable battery**, reducing power noise and increasing reliability.
4. **Integrated pre-amplifiers**: The ADS1299 has built-in **programmable gain amplifiers**, reducing external component requirements and failure risks.
5. **Dual polarity power supply**: Converts single-polarity battery voltage into **dual polarity supply**, allowing the ADC to handle positive and negative inputs.
6. **Power-efficient ESP32 processor**: Equipped with **dual 32-bit RISC cores**, consuming an average of **78.32 mW** in active mode.
7. **Wireless connectivity**: Supports **Bluetooth & WiFi**, with ESPNOW ensuring **250 samples/sec continuous operation**.
8. **Rechargeable & portable**: Features a **USB-rechargeable battery**, on/off and reset switches, and a lightweight design for improved user experience.
9. **Expandable channel support**: The system supports an additional **ADS1299 module**, increasing EEG channels from **8 to 16**.

## Files
1. **document_data.py**: This Python script is responsible for capturing and processing the EEG data received from the ESP32-C6 over the serial port (formatted for viewing using OpenBCI GUI).
2. **ReceiverCode/ReceiverCode.ino**: This Arduino sketch runs on the ESP32-C6, which acts as the receiver of the EEG data transmitted via WiFi (ESPNOW).
3. **SenderCode/SenderCode.h**: Header file containing function prototypes and constants used by SenderCode.cpp and SenderCode.ino.
4. **SenderCode/SenderCode.cpp**: This file implements core functions for acquiring EEG signals and transmitting them via ESPNOW.
5. **SenderCode/SenderCode.ino**: The main Arduino sketch for the ESP32 (EEG signal acquisition & transmission).
6. **Recorded_Data/eeg_data_to_file.py:** The python script for collecting and labelling blinking EEG data (formatted for easy processing using machine learning pipeline).
7. **Recorded_Data/labeled_data folder** This folder has 10 csv files of labelled EEG data.
8. **Recorded_Data/unlabeled_data folder** This folder has 10 csv files of unlabelled EEG data.
9. **High_performance_board_protective_case/high_performance_board_protective_case.stl** The 3D model of a custom-designed protective case meant to safeguard a high-performance board from physical damage, environmental factors, and overheating.

## **Installation & Setup**

### **1. Downloads**
- **Arduino IDE**
- **ESP32 Board Package** (via Arduino Board Manager)
- **Python (3.8+)**
- **PySerial Library** (`pip install pyserial`)
- **OpenBCI GUI**
- **pynput Library** (`pip install pynput`)

### **2. Hardware Requirements**
- **ESP32 Dev Board with ESP32-S3-WROOM-1 and 24-bit ADC** [https://www.aliexpress.us/item/3256806073268159.html?spm=a2g0o.order_list.order_list_main.20.54681802966XjN&gatewayAdapt=glo2usa](https://www.aliexpress.us/item/3256806073268159.html?spm=a2g0o.order_list.order_list_main.20.54681802966XjN&gatewayAdapt=glo2usa)
- **ESP32-C6**  
- **EEG Headset** 
- **2 USB Cables** (USB-C)

## **Setup and execution**
### **1. Setting Up the ESP32 & ESP32-C6**
- Install Arduino IDE and ESP32 board package.
- Upload **SenderCode.ino** to the ESP32 high-performance board.
- Upload **ReceiverCode.ino** to the ESP32-C6 module.

### **2. Running the Python Script**
For visualization:
- `pip install pyserial`
- `python3 document_data.py`
For data labelling:
- `pip install pynput`
- `python3 eeg_data_to_file.py`

## Usage Instructions
1. **Hardware setup**
   A- Connect EEG snap electrodes to the ADS1299 board.
   B- Ensure the ESP32 development board and ESP32-C6 module are powered and configured.
   C- Ensure that all the electrodes are in contact with the scalp.
![image](https://github.com/user-attachments/assets/4b2af03a-59c5-4d7e-bbba-4e2725e26962)

Figure:EEG Headset and high performance board (encased in custom case)

3. **Data acquisition**
   A- Open the Arduino Serial Monitor to check real-time EEG data transmission.
   B- Run the provided Python script to capture data from the serial port.
![reciever](https://github.com/user-attachments/assets/a38cc0d9-1d12-4a00-a44a-9e0ed74b7f91)

Figure:Receiver code run on XIAO-ESP32-C6 board to obtain 8-channel data via WiFi visible in the serial monitor
![python_script](https://github.com/user-attachments/assets/b7d3d6ac-e961-4d5c-bfa1-aba720ed82bc)

Figure:Python script writing the data  to a text file

5. **Visualization and analysis**
   A- View the recorded data in OpenBCI GUI to visualze the EEG data for all 8 channels.
![GUI](https://github.com/user-attachments/assets/e260e019-36f6-4e70-bbdf-fcbd84b48b2d)
   
Figure:EEG 8 channel data in the GUI Interface
![image](https://github.com/user-attachments/assets/bfdb3e86-17a6-45f8-96cd-d8cfb03f0391)

Figure:EEG 8 channel data recorded in csv file

## Protective case design overview
![image](https://github.com/user-attachments/assets/9cd528c7-44c5-493f-83ec-1138f3c89896)

## References
1. [https://www.ti.com/product/ADS1299](https://www.ti.com/product/ADS1299)
2. [https://docs.openbci.com/](https://docs.openbci.com/)
3. [https://datasheet.octopart.com/ADS1299IPAG-Texas-Instrumentsdatasheet-17020782.pdf](https://datasheet.octopart.com/ADS1299IPAG-Texas-Instruments-datasheet-17020782.pdf)
4. [https://openbci.com/community/concentratetoday-neurofeedback-enhancing-concentration-level/](https://openbci.com/community/concentratetoday-neurofeedback-enhancing-concentration-level/)
