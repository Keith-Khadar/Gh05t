import serial
import csv

# Open serial port
ser = serial.Serial('COM6', 115200, timeout=1)

# Open CSV file
with open('channel_data.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Channel 1 Data"])  # CSV Header

    try:
        while True:
            line = ser.readline().decode('ascii', errors='ignore').strip()  # Read & decode
            if line:  # Check if the line is not empty
                try:
                    channel_data = int(line)  # Convert to integer
                    print(f"Saving: {channel_data}")  # Print for debugging
                    writer.writerow([channel_data])  # Write to CSV
                except ValueError:
                    print(f"Invalid data received: {line}")  # Handle invalid lines
    except KeyboardInterrupt:
        print("\nData logging stopped. File saved.")
        ser.close()
