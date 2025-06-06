<p align="center"><img src="https://github.com/user-attachments/assets/effad896-a6b1-4835-b015-8e855c72339e" alt="drawing" width="400" style/></p>

# Project Overview

This project aims to design and develop a wearable EEG headset with an integrated data acquisition system. Using OpenBCI Ultracortex Mark IV as a template, the headset is designed to map the electrodes according to the 10-20 system. We expand on this design by integrating our own 3D printed or button-snap electrodes for enhanced modularity. Additionally, we investigate various EEG data acquistion hardware options, varying in cost, precision, and usability, to enhance accessibility and modularity in EEG systems - ranging from off-the-shelf hardware to custom-designed PCBs and circuit designs. The hardware will communicate with a computer for analysis by a machine learning (ML) model to detect gestures or possible speech, with the possibility of integration into Virtual-Reality (VR) applications. Lastly, the system will feature a custom GUI, enabling users to visualize EEG data in real-time from the various custom hardware configurations we explore.

We provide various levels to users depending on cost, precision, and usability:

| Feature                     | High Performance Development Board[^1]    | Balanced Performance Board[^2]                | Low Cost EEG Filtering Circuit[^3]            |
| --------------------------- | ----------------------------------------- | --------------------------------------------- | --------------------------------------------- |
| **Number of Channels**      | 8\*                                       | 8\*                                           | 8                                             |
| **Resolution**              | 24-bit                                    | 24-bit                                        | 12-bit                                        |
| **Typical Sampling Rate**   | 250 Hz                                    | 250 Hz                                        | <33 Hz                                        |
| **ADC Chip**                | ADS1299-IPAG                              | ADS1299-IPAG                                  | Internal RPi Pico ADC                         |
| **Board**                   | EEG Development Board with ESP32-S3       | Custom PCB                                    | Custom breadboard/featherboard circuit        |
| **Microcontroller**         | XIAO ESP32-C6                             | DFRobot Firebeetle ESP32 32D                  | Raspberry Pi Pico W                           |
| **Connectivity**            | USB-C/Bluetooth/WiFi                      | Micro-USB/Bluetooth/WiFi                      | Micro-USB/WiFi                                |
| **Power Source**            | Battery/USB                               | Battery/USB                                   | Battery/USB                                   |
| **Battery Life**            | 8 hours                                   | -                                             | <1 hour                                       |
| **GUI Support**             | OpenBCI GUI                               | Custom GUI                                    | Custom GUI                                    |
| **Form Factor**             | Button Snap Electrodes w/ OpenBCI Headset | 3D printed Claw Electrodes w/ OpenBCI Headset | 3D printed Claw Electrodes w/ Custom Headband |
| **Communication Protocols** | SPI, ESPNOW, UART                         | SPI, BLE                                      | UDP WebSocket                                 |
| **Price**                   | ~$375                                     | ~$100                                         | ~$50                                          |

\* The ADS1299 has the capabilities to daisy chain, therefore expanding the channel number from 8 to 16 but it is not fully implemented on the custom PCB. Refer to the ADS1299 PCB folder for additional information.

[^1]: Refer to [High_Performance\README.md](https://github.com/Keith-Khadar/Gh05t/tree/main/High_Performance) for more information on the setup and specifics for the system.
[^2]: Refer to [Balanced_Performance\README.md](https://github.com/Keith-Khadar/Gh05t/tree/main/Balanced_Performance) for more information on the setup and specifics for the system.
[^3]: Refer to [Low_Cost\README.md](https://github.com/Keith-Khadar/Gh05t/tree/main/Low_Cost) for more information on the setup and specifics for the system.

## Completed Work/In Progress for Milestone Production Release

-   **Working Balanced Performance Pipeline (ADS1299 Breakout PCB)**: Eye blinks were detected successfully in the FFT and Time Series plots but was unable to receive consistent and robust results after each trial.
    -   Work in progress of doing trial and error to reproduce results.
-   **Housing Design for Balanced Performance Board (Breakout PCB)**: A CAD design of a housing unit for the ADS1299 Breakout PCB was completed.
-   **Receiver code optimization for the High Performance board**: The receiver code was optimized for better efficiency on the high-performance board by restructuring logic, minimizing redundant operations, and improving resource utilization.
-   **Optimizing Real Time Reading on the GUI**: Since eye blinks were successfully shown in the time series, the SDED, with the calibration of the delta and alpha variables, was able to successfully label with minimal latency the sample positions where the blinking occurred.
-   **EEG Game Application**: In order to expand the application of using the EEG data and detecting events like eye blinking, a VR and simple blinking game was created. A WebSocket host was created in the GUI and successfully broadcasts the SDED labels to any client to act as a controller for a game.
-   **Signal Preprocessing** : The EEG signal preprocessing pipeline is fully implemented, ensuring artifact removal, filtering, and independent component extraction before further processing. FastICA, InfoMax, NLMS and VSS-APA are implemented to extract information components from raw EEG signals in real-time.
-   **Event Detection/Prediction Model**: The EEG-based event detection pipeline and machine learning models have been developed to analyze real-time brain activity and infer motor function. NLMS, Batch-Wiener Filter and VSS-APA have been implemeted for predictions - Statistical Deviation Event Detection Model and Information Theoretic Learning Point Process Detection Models have been implemented for more sophisticed event flagging.

# Project Architecture

### <p align="center">**High Performance Development Board**[^1]</p>

| <div style="width:400px">Hardware Architecture & Wiring</div>  | Components  | Communication Protocols  |
| ----------------------- | ----------------------- | ----------------------- |
| ![High Performance Board](https://github.com/user-attachments/assets/ce3bbd09-0870-42f1-9bc7-f2d55ca7b32b) | - OpenBCI 3D Headset Design<br> - Depth-adjustable spring loaded 3D printed assembly with metal snap electrodes provides good signal strength for EEG signals <br> - EEG ESP Development Board with ESP32-S3 <br> - XIAO ESP32-C6<br> - Protective case for the development board<br> | - SPI communication between ADS1299 chip and ESP32-S3<br> - ESP-NOW WiFi data transmission between Development Board and ESP32-C6<br> - UART serialized data transmission through USB-C connection between ESP32-C6 and computer receiver <br> |

-   **Software**
    -   Once the ESP32-C6 captures the incoming EEG data from the ESP32-S3, the UART data is captured through a python script and written to a file. The captured EEG data in this file can be viewed using OpenBCI GUI. The EEG data in this file will be feed to the machine learning model to draw inferences after analysis of the data.
    -   A python script is employed to label and timestamp the 8-channel EEG blinking data. This script facilitates the real-time processing and organization of the data, ensuring that each blink event is accurately marked with its corresponding timestamp for subsequent analysis.
    -   An end-to-end high-performance EEG pipeline leverages an ESP32 EEG board and ESP32-C6 to wirelessly transmit 8-channel, ultra-low-noise data at 250 samples/sec via ESP-NOW, enabling real-time processing in Python and visualization through OpenBCI GUI or a custom interface.
    <p align="center">
    <img src="https://github.com/user-attachments/assets/1e4aa29c-b1bf-421d-8bab-5dd617b7926b" alt="data collection stages" width="500" />
    <img src="https://github.com/user-attachments/assets/d988fad5-ef7a-4597-9178-4c8908839831" alt="fft plot" width="500" />
    </p>

### <p align="center">**Balanced Performance Board**[^2]</p>

| <div style="width:450px">Hardware Architecture & Wiring</div>  | Components  | Communication |
| ----------------------- | ----------------------- | ----------------------- |
| <img src="https://github.com/user-attachments/assets/90f90b59-3fc4-4933-9542-4793f8f74661" alt="drawing" width="1000" style/> <img src="https://github.com/Keith-Khadar/Gh05t/blob/main/Balanced_Performance/Images/PCB.PNG?raw=true" alt="drawing" width="190" style/> <img src="https://github.com/Keith-Khadar/Gh05t/blob/main/Balanced_Performance/Images/PCB_Render_Above.png?raw=true" alt="drawing" width="190" style/> | - OpenBCI 3D Headset Design<br> - 3D Printed Claw Electrodes<br> - Custom ADS1299 PCB<br> - DFRobot Firebeetle ESP32 32D <br> | - SPI communication between the ADS1299 PCB and Firebeetle ESP32 <br> - BLE data transmission between the Firebeetle ESP32 and computer receiver <br> |

-   **Software**
    -   Once the Firebeetle ESP32 is supplied power, the BLE server is turned on and ready to transmit data to any device that connects to the server. The **GH05T GUI** is used to connect to the BLE server and read incoming real-time data.

### <p align="center">**Low Cost Filtering Circuit**[^3]</p>

| <div style="width:500px">Hardware Architecture & Wiring</div>   | Components | Communication Protocols |
| ----------------------- | ----------------------- | ----------------------- |
| <img src="https://github.com/user-attachments/assets/0a12550a-8cac-404f-81ee-4bf6df63b5ae" alt="drawing" width="600" style/> | - Custom Filtering and Component Circuit on breadboard/featherboard <br> - Raspberry Pi Pico W <br> | - TCP WebSocket data transmission between Raspberry Pi Pico W and computer receiver |

-   **Software**
    -   Once the Raspberry Pi Pico W is supplied power,UDP WebSocket is opened and transmits data to any device that connects to the server. The **GH05T GUI** is used to connect to the WebSocket server and read incoming real-time data.

### <p align="center">**GH05T Graphic User Interface**[^4]</p>

| <div style="width:300px">Function and Feature Architecture</div> | Visuals/GUI  |
| ----------------| ---------------------- |
| ![GUI Flow](https://github.com/user-attachments/assets/a9a500f8-1eae-45d4-b21f-32e67913ea0e) | ![GUI Flow](https://github.com/user-attachments/assets/ed05217e-f655-4535-b095-f2ec6a256eff) [PyQt](https://doc.qt.io/qtforpython-6/) & [Matplotlib](https://matplotlib.org/): Widget and EEG Data Visualization |

[^4]: Refer to [Gh05t GUI\README.md](https://github.com/Keith-Khadar/Gh05t/tree/main/Gh05t%20GUI) for more information on the setup and specifics on the GUI.

### <p align="center">**Signal Processing and Machine Learning**[^5]</p>

-   **EEG Signal Pre-processing**:

    -   Format:
        -   Input: Raw 4 channel electrode data
        -   Output: K-Independent Signals (Components)
    -   Processing Options:
        -   FastICA , NLMS: Fast Inference
        -   InfoMax or VSS-APA: Versatility & Robustness

-   **EEG Signal Machine Learning**:
    -   Format:
        -   Input: K-Independent Signals (Components)
        -   Output: User Defined Target Output
    -   Target:
        -   User Defined Target Desired Output, i.e. eye activity or motion.
    -   Model:
        -   Structure: Artifical Neural Network (Regressor)
        -   Pre-Training: PCA-Pretraining for optimal features
        -   Training: Network Tuning based on Target Data

[^5]: Refer to [Machine_Learning\README.md](https://github.com/Keith-Khadar/Gh05t/tree/main/Machine_Learning) for more information on the setup and specifics.

## Known Bugs

- The Balanced Performance Board ADS1299 completely stopped working after trying to fit the casing to the hardware. This was an unexpected issue that is not able to be understood. Possible issues that could have occurred for the chip to completely stop working is somehow the chip received a surge of power that could have damaged it. 

## Difficulties/Challenges

-   **3D Printing Fail**: Weak legs on 3D electrodes
    -   The initial model found and used for the electrodes has spindly legs. In combination with two snaps of the filament during printing, the legs were incredibly weak and many snapped during removal from the print bed.
    -   Fix: Load filament onto spool to eliminate snapping during print. Custom design electrodes with filleted legs to enhance their strength. Increase the number of walls when slicing model for printing.
    -   Above fix solved combined with printing on a higher quality printer and in a different orientation fixed the issues.
-   **Snap Plating**: Purchased snaps are covered in non-conductive coating
    -   Prevented soldering, but can be scrapped off with a knife.
    -   Reduces signal integritty of electrodes.
    -   Fix: Looking into alternative unplated snap connectors.
    -   Above fix solves the issue in initial testing. Will continue to monitor as further testing is conducted.
-   **Inaccurate EEG Data**: Data recorded during initial testing is inaccurate.
    -   The poor quality electrodes(see snap plating challenge & 3d printing fail) as well as the ADC optimized for Electromyography (EMG) data recording instead of the use case of Electroencephalography (EEG), resulted in poor quality data.
    -   Fix: Custom designed PCB breakout board for the ADS1299 which is designed for EEG data acquisition.
-   **GUI Real Time Data**: Optimizing the timing between data conversion from the ADS1299 to the GUI has introduced latency.
    -   Fix: Utilizing threading and precise timing between frame updating and loading.
-   **ADS1299 Electrode Setup**: Setting up the registers for specific BIAS, SRB1/2, and Electrode connections proved difficult with our system. This was causing reading alpha waves to be difficult.
    -   Fix: Using the SRB1, connected to the earlobe/mastoid, routed to all the negative parts of the electrode channels for reference. Using the BIAS, also connected to the earlobe/mastoid, routed to the postive electrode channels for signal derivation.

## License

## Contact

## Acknowledgements

We would like to extend our gratitude to OpenBCI for having open source repositories with headset designs, ADS1299 libraries, and user interface code. These repositories played a significant role in the success of the project!
