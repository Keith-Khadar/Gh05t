# Communication Between ADS1299 and ESP32

## Overview

The Firebeetle ESP32 Development board is used to communicate to the ADS1299 custom PCB over SPI. Once channel data is received by the ESP32, the data is sent over BLE to the user device with the custom GUI to read and visualize the EEG channels. 

#### Features

- **Easy Setup**: All the connections are already presented to the user. Easy uploading to the microcontroller will enable quick use of the device. 
- **Customizability**: Any ESP32 with the output support of 3.3V and 5V (when plugged in via usb or external power), BLE, and SPI, can support the setup outlined.

#### Dependencies
1. **Hardware**
    - Firebeetle ESP32 v4.0 microcontroller
    - ADS1299 PCB
    - Female header wires or soldering to create connections between ADS1299 PCB and microcontroller.
2. **Software**
    - Arduino IDE (for uploading the .ino to the microcontroller)
3. **Libraries**
    - ADS1299 library
    - Arduino BLE Libraries: BLEDevice, BLEServer, BLEUtils, BLE2902

## Setup Instructions
### 1. Wiring
The connections listed should be universal when using the ADS1299. Refer to your PCB schematic for specific leads and/or ADS1299 Datasheet. In our case, our ADS1299 PCB had these direct connections:

| ADS1299 PCB       | Firebeetle ESP32 | Description    |
| --------          | -------          | -------        |
| SCLK              | SCLK [GPIO 18]   | Set to 2MHz[^1]    |
| MISO [DOUT]       | MISO [GPIO 19]   | Data channel output (ADS1299 → ESP32)[^1]  |
| MOSI [DIN]        | MOSI [GPIO 23]   | Data channel input (ESP32 → ADS1299)[^1]   |
| CS or SS          | SS [GPIO 5]      | Chip select (low during communication)[^1] |
| DRDY              | GPIO 4           | Data ready (low when new data available)[^1] |
| RST               | GPIO 2           | Reset (active low)[^2]
| AVDD              | 5V [VCC]         | Analog Nominal 5V[^3]      |
| DVDD              | 3.3V             | Digital Nominal 1.8V[^3]   |
| AGND and DGND     | GND              | Tied ground                |

[^1]: https://www.ti.com/lit/ds/symlink/ads1299.pdf#page=38
[^2]: https://www.ti.com/lit/ds/symlink/ads1299.pdf#page=35
[^3]: https://www.ti.com/lit/ds/symlink/ads1299.pdf#page=8

### 2. Clone the Repository
If not already done so, clone the respository

```bash
git clone https://github.com/Keith-Khadar/Gh05t
```

## 3. Upload the Sketch
Copy the esp32\ADS1299 library and place it under your libraries directory of your Arduino IDE. You can usually find this under  ```"C:\Users\"USER"\Documents\Arduino\libraries"```. By adding the library, you can refer to it when flashing the sketch.

 - ***ADS12999 LIBRARY***: The library folder was retrieved from OpenBCI[^4] which used the ADS1299 library that was created by Conor Russomanno[^5] initially. The only changes that we made were for ESP32 adapation instead of the Arduino Uno.

[^4]: https://github.com/chipaudette/OpenBCI
[^5]: https://github.com/conorrussomanno/ADS1299

Flash the ```esp32\esp32_ble_eeg\ADS1299_SPI_ESP.ino``` program to the ESP32 microcontroller using either Arduino IDE or PlatformIO. Ensure the output of the ESP32 reports the BLE server broadcasting.

### 4. Confirm Connections and Broadcasting
In order to confirm proper connections with the PCB, there is debugging points in the sketch. Open the Serial Monitor and connect to 115200 baud rate in order to read the outputs of the device. 

The device should output the ID of the ADS1299 that is being used. In our case the ID register should output 0x3E (0b00111110)[^6]. If it outputs 0x00 there is something wrong with the wiring or the ADS1299 is not being supplied enough power (most likely the analog (AVDD))

[^6]: https://www.ti.com/lit/ds/symlink/ads1299.pdf#page=45

In order to confirm the BLE broadcast, you can check any device that has bluetooth support and see if the device name "ADS1299 BLE" is shown in the list. 

### 5. Update Configuration
Edit the `ble_handler.py` file, under utils folder, to update the ESP32 service and characteristic UUID:

```python
SERVICE_UUID = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"  # Replace with ESP32 Service UUID
CHARACTERISTIC_UUID = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" # Replace with ESP32 Characteristic UUID
```

There are UUID already defined in the code, but if you like to keep unique devices, we recommend to change the UUID.

### 6. Connect to the GUI
Refer to the GUI section for setup.

## Troubleshooting/Known Bugs
- None

## Future Work
- Creation of a mobile application would make it easier for the user to see the broadcasted data from the ESP32, rather than using a computer.