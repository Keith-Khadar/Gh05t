import serial
import struct
import csv
import os

FRAME_SIZE = 10 * 4  # 10 uint32_t values per frame (marker + timestamp + 8 channels)
FRAME_MARKER = 0xFEEDFACE

ser = serial.Serial('COM4', 115200, timeout=0.001)

buffer = b''
csv_file = 'output.csv'

# Create CSV and write header
if not os.path.exists(csv_file):
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp'] + [f'Channel_{i+1}' for i in range(8)])

# Start reading and writing to CSV
with open(csv_file, 'a', newline='') as f:
    writer = csv.writer(f)

    while True:
        buffer += ser.read(FRAME_SIZE)

        while len(buffer) >= FRAME_SIZE:
            marker = struct.unpack('<I', buffer[0:4])[0]

            if marker == FRAME_MARKER:
                frame = buffer[:FRAME_SIZE]
                values = struct.unpack('<10I', frame)
                timestamp = values[1]
                channels = values[2:]
                writer.writerow([timestamp] + list(channels))
                buffer = buffer[FRAME_SIZE:]
            else:
                buffer = buffer[1:]
