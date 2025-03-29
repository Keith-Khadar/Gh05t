import serial
from datetime import datetime
import csv
from pynput import keyboard

# Setting the serial port and baud rate
SERIAL_PORT = 'COM4'
BAUD_RATE = 115200

eyes_closed = 0  # Default value for "Eyes closed"

def on_press(key):
    # Callback function to detect key presses
    global eyes_closed
    try:
        if key == keyboard.Key.tab:  # Detecting Tab key press
            eyes_closed = 1  # Setting "Eyes closed" to 1 when Tab is pressed
    except AttributeError:
        pass  # Ignoring non-character keys

def on_release(key):
    # Callback function to detect key releases
    global eyes_closed
    if key == keyboard.Key.tab:  # Detecting Tab key release
        eyes_closed = 0  # Resetting "Eyes closed" to 0 when Tab key is released
    if key == keyboard.Key.esc:  # Stopping listener on Escape key press
        return False

# Setting the listener for key events
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

def print_to_terminal(data):
    # Printing decoded data to the terminal
    print(f"{data}", end='')

def save_to_file(file, data):
    # Saving data to a CSV file
    writer = csv.writer(file)
    writer.writerow(data)

def hex_to_decimal(hex_value, scale_factor=1000):
    # Converting hex string to decimal
    try:
        decimal_value = int(hex_value, 16)
        return scale_value(decimal_value, scale_factor)
    except ValueError:
        return 0

def scale_value(value, scale_factor=1000):
    # Scaling down the decimal value to fit the expected range
    return value / scale_factor

# Opening the serial port
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.001)
    print(f"Successfully opened serial port {SERIAL_PORT}")
except Exception as e:
    print(f"Error opening serial port: {e}")
    exit()

# Opening a CSV file to save the received data
with open('received_data.csv', 'w', newline='') as file:
    # Creating a CSV writer object
    writer = csv.writer(file)

    # Writing header to the CSV file
    header = ["Sample index", "Fp1", "Fp2", "C3", "C4", "P7", "P8", "O1", "O2", "Timestamp", "Eyes closed"] # Electrode positions based on 102-0 system
    writer.writerow(header)

    print("Start receiving data from ESP32...")
    index = 0
    while True:
        if ser.in_waiting > 0:  # Checking if data is available
            data = ser.readline()  # Reading a line of data
            if data:  # Ensuring data is not empty
                try:
                    decoded_data = data.decode('utf-8', errors='ignore')  # Decoding bytes to string
                    hex_values = decoded_data.split()  # Splitting the hex values

                    if len(hex_values) >= 8:
                        decimal_values = [hex_to_decimal(val) for val in hex_values[:8]]
                        # Generating timestamp
                        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3] # Formatting to include milliseconds
                        # Formatting the output as requested
                        formatted_data = [index] + decimal_values + [timestamp] + [eyes_closed]

                        # Printing to terminal and saving to file
                        print_to_terminal(formatted_data)  # Printing to terminal
                        save_to_file(file, formatted_data)  # Writing to the CSV file
                        index += 1

                except Exception as decode_error:
                    print(f"Error decoding data: {decode_error}")