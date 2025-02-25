# High-Performance Microcontroller Board

## Overview:
The High-Performance Microcontroller Board integrates a 24-bit ADC to capture high-resolution EEG signals and transmits the data wirelessly using an ESP32-based development board. 
The setup allows seamless data transfer to an ESP32-C6 module, which then relays the EEG data over WiFi (ESPNOW) to a connected laptop for analysis and visualization.
![final_img](https://github.com/user-attachments/assets/43cc4ee9-4ac0-4c07-87eb-3f372cc2ac09)

## System workflow:
1. EEG signals are captured from snap electrodes and processed using an ESP32 development board.
2. The ESP32 development board transmits the 8-channel EEG data wirelessly via ESPNOW to the ESP32-C6 module.
3. The ESP32-C6 receives the data and relays it to the Arduino Serial Monitor for verification.
4. A Python script captures the data from the laptop's serial port and records it in a text file.
5. The data is formatted for compatibility with the OpenBCI GUI for visualization and further analysis.
6. Filtering techniques are applied to extract alpha wave frequencies (8-10 Hz), confirming the presence of neural activity.
7. Initial testing involved verifying ADC readings with a DC voltage input, ensuring data accuracy before integrating electrodes.

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

## Usage Instructions
1. **Hardware setup**
   A- Connect EEG snap electrodes to the ADS1299 board.
   B- Ensure the ESP32 development board and ESP32-C6 module are powered and configured.
   C- Ensure that all the electrodes are in contact with the scalp.
   ![image](https://github.com/user-attachments/assets/ed849d00-407b-4b9b-b622-1c76eea5a5d5)

3. **Data acquisition**
   A- Open the Arduino Serial Monitor to check real-time EEG data transmission.
   B- Run the provided Python script to capture data from the serial port.
![reciever](https://github.com/user-attachments/assets/a38cc0d9-1d12-4a00-a44a-9e0ed74b7f91)
![python_script](https://github.com/user-attachments/assets/b7d3d6ac-e961-4d5c-bfa1-aba720ed82bc)
   
5. **Visualization and analysis**
   A- View the recorded data in OpenBCI GUI to visualze the EEG data for all 8 channels.
   ![GUI](https://github.com/user-attachments/assets/e260e019-36f6-4e70-bbdf-fcbd84b48b2d)

## References
1. [https://www.ti.com/product/ADS1299](https://www.ti.com/product/ADS1299)
2. [https://docs.openbci.com/](https://docs.openbci.com/)
3. [https://datasheet.octopart.com/ADS1299IPAG-Texas-Instrumentsdatasheet-17020782.pdf](https://datasheet.octopart.com/ADS1299IPAG-Texas-Instruments-datasheet-17020782.pdf)
4. [https://openbci.com/community/concentratetoday-neurofeedback-enhancing-concentration-level/](https://openbci.com/community/concentratetoday-neurofeedback-enhancing-concentration-level/)
