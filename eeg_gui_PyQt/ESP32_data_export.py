import serial
import csv
import time

SERIAL_PORT = "COM6"
BAUD_RATE = 115200
OUTPUT_FILE = "data_log.csv"

def parse_serial_data(line):
    """Extract timestamp and 8-channel data from the serial input line."""
    print(line)
    try:
        if "Timestamp:" in line and "Channel Data:" in line:
            parts = line.strip().split()
            timestamp = float(parts[1])
            channel_data = [int(parts[i]) for i in range(4, 12)]
            return [timestamp] + channel_data
    except Exception as e:
        print(f"Error parsing line: {line} | {e}")
    return None

def main():
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser, open(OUTPUT_FILE, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Timestamp", "Channel1", "Channel2", "Channel3", "Channel4", 
                             "Channel5", "Channel6", "Channel7", "Channel8"]) 
            
            print(f"Listening on {SERIAL_PORT} at {BAUD_RATE} baud...")
            while True:
                line = ser.readline().decode("utf-8").strip()
                if line:
                    parsed_data = parse_serial_data(line)
                    if parsed_data:
                        writer.writerow(parsed_data)
                        print(f"Saved: {parsed_data}")
    except serial.SerialException as e:
        print(f"Serial Error: {e}")
    except KeyboardInterrupt:
        print("\nScript stopped by user. CSV file saved.")

if __name__ == "__main__":
    main()
