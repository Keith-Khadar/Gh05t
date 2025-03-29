# Raspberry Pi Pico Project
## Overview
This is for the low cost version of the EEG project. It is written in C for the Raspberry Pi Pico. After flashing the firmware onto the Pico, it will output its IP address over serial communication at a baud rate of 115200. From there you can connect using a TCP websocket on port 4242.

## Prerequisites
Raspberry Pi Pico board
C/C++ SDK for the Pico (Raspberry Pi Pico SDK Setup Guide)
CMake (version 3.13 or later)
Make
Serial monitor (e.g., minicom, PuTTY, or Arduino Serial Monitor)
Setup Instructions
## Clone or Download the Code
Download or clone this repository to your local machine.

## Build the Project
Open a terminal and navigate to the project’s root directory:

```bash
cd Gh0st/rpi_low_cost/Gh0st/build
make
```
This will generate a .uf2 file in the build directory.

## Flash the Pico

Hold down the BOOTSEL button on the Pico.
While holding the button, plug the Pico into your computer via USB.
A new mass storage device named RPI-RP2 should appear.
Drag and drop the generated .uf2 file into the RPI-RP2 drive.
Once the file transfer is complete, the Pico will reboot automatically.
View Serial Output
To read the IP address output from the Pico:

Unplug and reconnect the Pico (without holding the BOOTSEL button).
Open your preferred serial monitor and connect to the appropriate port at a baud rate of 115200.
Example using minicom:

```bash
minicom -b 115200 -D /dev/ttyUSB0
(Replace /dev/ttyUSB0 with your actual serial port.)
```
The Pico should display its assigned IP address upon startup.

## Troubleshooting
If the RPI-RP2 drive doesn’t appear, ensure you’re holding the BOOTSEL button while plugging in the Pico.
If no serial output appears, double-check your serial port and baud rate settings.
