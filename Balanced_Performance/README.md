# Balanced Performance Board

## Overview
The Balanced Performance Board bridges commercial products and DIY EEG boards by featuring high resolution ADC chip, ADS1299, on a DIY PCB, a common microcontroller, and a custom made GUI. 

The specifications include:
|  Section |  Feature  | Specs |
| --- | --- | --- |
| ADS1299 Breakout Board**      | Dimensions              | 56.10mm x 69.00mm         |
|                  | Layers                  | 2-layer PCB                            |
|                  | Electrode Connector     | Straight header pins/connectors        |
| Balanced Backpack Board**      | Dimensions              | 35.56mm x 77.47mm        |
|                  | Layers                  | 2-layer PCB                            |
|                  | Electrode Connector     | 2.54mm right-angle JST                 |
| Microcontroller  | Model                   | DFRobot Firebeetle ESP32 32D           |
|                  | Processor               | Tensilica LX6 dual core                |
|                  | Clock Speed             | <240MHz                                |
|                  | Flash / RAM             | 16MB Flash / 520KB RAM                 |
| ADC              | AFE Chip                | ADS1299                                |
|                  | Number of Channels      | 8 (16 with Daisy Chaining)             |
|                  | ADC Resolution          | 24-bit                                 |
|                  | Input Impedance         | >1 GΩ                                  |
|                  | Gain                    | Programmable up to 24x                 |
|                  | Sampling Rate           | 16kHz - 250Hz per channel              |
| Power            | Supply Voltage          | USB (Supply 3.3V and 5V)               |
| Connectivity     | Interfaces              | USB, Bluetooth (BLE)                   |
|                  | Data Rate               | <1Mbps                                 |

** There are two designs of the Balanced Performance board. The ADS1299 Breakout board is a flat board that has header pins for each input/output for the ADS1299. This board is more meticulous to wire but it provides an easy way to interface with the ADS1299 depending on the project. The Balanced Backpack board acts as a backpack on top of the DFRobot ESP32 microcontroller which makes it compact and easier to connect. It only provides the electrode outputs, everything else is connected to the microcontroller. 

## PCB Designs

|  ADS1299 Breakout Board  |  Balanced Backpack Board  |
| --- | --- |
| ![Image](https://github.com/Keith-Khadar/Gh05t/blob/main/Balanced_Performance/Images/PCB_Render_Above.png?raw=true){ width=300px } | ![Image](https://github.com/Keith-Khadar/Gh05t/blob/main/Balanced_Performance/Images/ADS1299_Breakout_Top_View.png?raw=true){ width=520px } |

## Setup Instructions
### 1. Wiring
The connections listed should be universal when using the ADS1299. Refer to your PCB schematic for specific leads and/or ADS1299 Datasheet. In our case, the ADS1299 Breakout Board had these direct connections:

| ADS1299 Breakout Board      | Firebeetle ESP32 | Description    |
| --------          | -------          | -------        |
| SCLK              | SCLK [GPIO 18]   | Set to 1.5MHz[^1]**    |
| MISO [DOUT]       | MISO [GPIO 19]   | Data channel output (ADS1299 → ESP32)[^1]  |
| MOSI [DIN]        | MOSI [GPIO 23]   | Data channel input (ESP32 → ADS1299)[^1]   |
| CS or SS          | SS [GPIO 5]      | Chip select (low during communication)[^1] |
| DRDY              | GPIO 4           | Data ready (low when new data available)[^1] |
| RST               | GPIO 2           | Reset (active low)[^2]     |
| START             | GPIO 10          | START (active high)[^3]     |
| AVDD**            | 5V [VCC]         | Analog Nominal 5V[^4]      |
| AVSS**            | GND              | Analog Referenced to GND   |
| DVDD              | 3.3V             | Digital Nominal 1.8V[^4]   |
| AGND and DGND     | GND              | Tied ground                |

** The SCLK can vary in speed. Most documentation online uses 2MHz or 4MHz, but we found when using these values, we had inconsistencies with the data reading or data corruption. 1.5MHz is the minimum spec for the external clock in the ADS1299 and works best for our system. 
** The ADS1299 can be powered using unipolar power supplies (5V on AVDD and referenced to GND on VSS) and with bipolar supplies (2.5V on AVDD and -2.5V on AVSS).

For the Balanced Backpack Board, since it sits directly ontop of the microcontroller there is no need to wire anything. Only unsure the orientation is correct with the headers (the curved end of the pcb goes towards the power end of the microcontroller)

[^1]: https://www.ti.com/lit/ds/symlink/ads1299.pdf#page=38
[^2]: https://www.ti.com/lit/ds/symlink/ads1299.pdf#page=35
[^3]: https://www.ti.com/lit/ds/symlink/ads1299.pdf#page=34
[^4]: https://www.ti.com/lit/ds/symlink/ads1299.pdf#page=8

### 2. Clone the Repository
If not already done so, clone the respository

```bash
git clone https://github.com/Keith-Khadar/Gh05t
```

## 3. Upload the Sketch
Copy the esp32\ADS1299 library and place it under your libraries directory of your Arduino IDE. You can usually find this under  ```"C:\Users\"USER"\Documents\Arduino\libraries"```. By adding the library, you can reference to it when flashing the sketch.
 - ***SKETCH***: Depending on the microcontroller that is used, the user may need to change the sketch to configure it to their device. The only line that needs to be changed is ```ADS.initialize(16,2,13,1.5,0);``` This line controls the pinout for the DRDY, RST, and CS. 

 - ***ADS12999 LIBRARY***: The library folder was retrieved from OpenBCI[^5] which used the ADS1299 library that was created by Conor Russomanno[^6] initially. The only changes that we made were for ESP32 adapation instead of the Arduino Uno.
   - Adaption includes:
     - Changing the SPI interface to fit ESP32 instead of Arduino Uno. This is changing how it is setup and how data is sent/received.
     - The only line that will need to change according to the users setup is ```SPI.begin(18, 19, 23, CS); SPI.beginTransaction(SPISettings(Freq * 1000000, MSBFIRST, SPI_MODE1));``` 
    These lines control the SPI clock and pinouts for the DOUT and DIN. If a different esp32 is being used, the pinouts with be different (refer to wiring table for our pinout setup).

[^5]: https://github.com/chipaudette/OpenBCI
[^6]: https://github.com/conorrussomanno/ADS1299

Flash the ```esp32\esp32_ble_eeg\ADS1299_SPI_ESP.ino``` program to the ESP32 microcontroller using either Arduino IDE or PlatformIO. Ensure the output of the ESP32 reports the BLE server broadcasting.

### 4. Confirm Connections and Broadcasting
In order to confirm proper connections with the PCB, there is debugging points in the sketch. Open the Serial Monitor and connect to 115200 baud rate in order to read the outputs of the device. 

The device should output the ID of the ADS1299 that is being used. In our case the ID register should output 0x3E (0b00111110)[^7]. If it outputs 0x00 there is something wrong with the wiring or the ADS1299 is not being supplied enough power (most likely the analog (AVDD or AVSS)).
  - We encountered an issue where we were able to read from the registers but was not able to read from the channels properly. Make sure to triple check wiring and the analog power is being supplied properly with minimal noise. 

[^7]: https://www.ti.com/lit/ds/symlink/ads1299.pdf#page=45

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