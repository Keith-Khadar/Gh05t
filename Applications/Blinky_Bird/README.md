# Simple Unity Flappy Bird Clone

This is a simple 2D Unity game similar to Flappy Bird. The user can use their keyboard or they can connect the game to the Gh05t GUI over WIFI and control the character through eye blinks.

## Requirements

- Unity 2022.3.61f1 or newer
- Gh05t GUI and Headset
- Local network that supports communication between devices

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Keith-Khadar/Gh05t.git
```
### 2. Add the Unity Project from Disk
In Unity Hub add a project and select from disk. Navigate to our repo and locate Blinky_Bird.

### 3. Change the IP address
Edit this file `Gh05t/Applications/Blinky_Bird/Blinky_Bird/Assets/Scripts
/player_controller.cs` and change the address (`ws://10.78.4.19:4242`) to match the computer that is running the GUI. You can find the address of the computer runing the GUI by running `ifconfig` or `ipconfig`.

### 4. Set up the GUI
Connect the headset to the GUI and click on the option to send the labels out over websockets. Then press play in Unity.
