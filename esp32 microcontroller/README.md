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
| AVDD**            | 5V [VCC]         | Analog Nominal 5V[^3]      |
| AVSS**            | GND              | Analog Referenced to GND   |
| DVDD              | 3.3V             | Digital Nominal 1.8V[^3]   |
| AGND and DGND     | GND              | Tied ground                |

** The ADS1299 can be powered using unipolar power supplies (5V on AVDD and referenced to GND on VSS) and with bipolar supplies (2.5V on AVDD and -2.5V on AVSS).

[^1]: https://www.ti.com/lit/ds/symlink/ads1299.pdf#page=38
[^2]: https://www.ti.com/lit/ds/symlink/ads1299.pdf#page=35
[^3]: https://www.ti.com/lit/ds/symlink/ads1299.pdf#page=8

### 2. Clone the Repository
If not already done so, clone the respository

```bash
git clone https://github.com/Keith-Khadar/Gh05t
```

## 3. Upload the Sketch
Copy the esp32\ADS1299 library and place it under your libraries directory of your Arduino IDE. You can usually find this under  ```"C:\Users\"USER"\Documents\Arduino\libraries"```. By adding the library, you can reference to it when flashing the sketch.
 - ***SKETCH***: Depending on the microcontroller that is used, the user may need to change the sketch to configure it to their device. The only line that needs to be changed is ```ADS.initialize(4,2,5,4,0);``` This line controls the pinout for the DRDY, RST, and CS. 

 - ***ADS12999 LIBRARY***: The library folder was retrieved from OpenBCI[^4] which used the ADS1299 library that was created by Conor Russomanno[^5] initially. The only changes that we made were for ESP32 adapation instead of the Arduino Uno.
   - Adaption includes:
     - Changing the SPI interface to fit ESP32 instead of Arduino Uno. This is changing how it is setup and how data is sent/received.
     - The only line that will need to change according to the users setup is ```SPI.begin(18, 19, 23, CS); SPI.beginTransaction(SPISettings(2000000, MSBFIRST, SPI_MODE1));``` 
    These lines control the SPI clock and pinouts for the DOUT and DIN. If a different esp32 is being used, the pinouts with be different (refer to wiring table for our pinout setup).

[^4]: https://github.com/chipaudette/OpenBCI
[^5]: https://github.com/conorrussomanno/ADS1299

Flash the ```esp32\esp32_ble_eeg\ADS1299_SPI_ESP.ino``` program to the ESP32 microcontroller using either Arduino IDE or PlatformIO. Ensure the output of the ESP32 reports the BLE server broadcasting.

### 4. Confirm Connections and Broadcasting
In order to confirm proper connections with the PCB, there is debugging points in the sketch. Open the Serial Monitor and connect to 115200 baud rate in order to read the outputs of the device. 

The device should output the ID of the ADS1299 that is being used. In our case the ID register should output 0x3E (0b00111110)[^6]. If it outputs 0x00 there is something wrong with the wiring or the ADS1299 is not being supplied enough power (most likely the analog (AVDD or AVSS)).
  - We encountered an issue where we were able to read from the registers but was not able to read from the channels properly. Make sure to triple check wiring and the analog power is being supplied properly with minimal noise. 

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
- Expanding the documentation to support more microcontrollers.