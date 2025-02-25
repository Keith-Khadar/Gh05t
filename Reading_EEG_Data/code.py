import serial
import time

# Setting the serial port and baud rate
SERIAL_PORT = 'COM4'
BAUD_RATE = 115200

def print_to_terminal(data):
    """Printing decoded data to the terminal"""
    print(f"{data}", end='')

def save_to_file(file, data):
    """Saving data to the file"""
    file.write(data)

def hex_to_decimal(hex_value, scale_factor=1):
    """Converting hexadecimal to decimal"""
    try:
        decimal_value = int(hex_value, 16)
        return scale_value(decimal_value, scale_factor)
    except ValueError:
        return 0  # Return 0 if conversion fails

def scale_value(value, scale_factor=1):
    """Scaling down the decimal value to fit the expected range"""
    return value / scale_factor

def generate_timestamp():
    """Generate a timestamp in the format HH:MM:SS.mmm (EST)"""
    # Subtracting 5 hours (in seconds) to convert to EST
    est_time = time.gmtime(time.time() - 5 * 3600)
    # Formatting the EST time
    formatted_time = time.strftime('%H:%M:%S.', est_time) + f"{int((time.time() % 1) * 1000):03}"
    return formatted_time
    # Opening the serial port
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Successfully opened serial port {SERIAL_PORT}")
except Exception as e:
    print(f"Error opening serial port: {e}")
    exit()

# Opening a file to save the received data (in write mode to clear the file)
with open('received_data.txt', 'w') as file:
    # Writing header to the file
    header = "%OpenBCI Raw EXG Data\n"
    header += "%Number of channels = 8\n"
    header += "%Sample Rate = 250 Hz\n"
    header += "%Board = OpenBCI_GUI$BoardCytonSerial\n"
    header += "Sample Index, EXG Channel 0, EXG Channel 1, EXG Channel 2, EXG Channel 3, EXG Channel 4, EXG Channel 5, EXG Channel 6, EXG Channel 7, Accel Channel 0, Accel Channel 1, Accel Channel 2, Not Used, Digital Channel 0 (D11), Digital Channel 1 (D12), Digital Channel 2 (D13), Digital Channel 3 (D17), Not Used, Digital Channel 4 (D18), Analog Channel 0, Analog Channel 1, Analog Channel 2, Timestamp, Marker Channel, Timestamp (Formatted)\n"
    file.write(header)

    print("Start receiving data from ESP32...")
    index = 0
    while True:
        if ser.in_waiting > 0:  # Checking if data is available
            data = ser.readline()  # Reading a line of data
            if data:  # Ensuring data is not empty
                try:
                    decoded_data = data.decode('utf-8', errors='ignore')  # Decoding bytes to string
                    hex_values = decoded_data.split()  # Splitting the hex values

                    # Ensuring there are enough hex values in the line
                    if len(hex_values) >= 8:
                        # Converting hex to decimal
                        decimal_values = [hex_to_decimal(val) for val in hex_values[:8]]

                        # Formatting the output as requested
                        timestamp = generate_timestamp()
                        formatted_data = f"{index}, {decimal_values[0]}, {decimal_values[1]}, {decimal_values[2]}, {decimal_values[3]}, {decimal_values[4]}, {decimal_values[5]}, {decimal_values[6]}, {decimal_values[7]}, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, {timestamp}\n"

                        # Printing to terminal and saving to file
                        print_to_terminal(formatted_data)
                        save_to_file(file, formatted_data)
                        index += 1

                except Exception as decode_error:
                    print(f"Error decoding data: {decode_error}")