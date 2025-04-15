import serial
import struct
import csv
import os
import threading

FRAME_SIZE = 10 * 4  # 10 uint32_t values per frame
FRAME_MARKER = 0xFEEDFACE
csv_file = 'output.csv'

eye_closed = 0
eye_lock = threading.Lock()

def input_thread():
    global eye_closed
    while True:
        user_input = input("Enter 'c' to mark eyes CLOSED, 'o' to mark eyes OPEN: ").strip().lower()
        with eye_lock:
            if user_input == 'c':
                eye_closed = 1
                print("Marked: Eyes Closed")
            elif user_input == 'o':
                eye_closed = 0
                print("Marked: Eyes Open")
            else:
                print("Invalid input. Use 'c' or 'o'.")

# Starting input listener in a separate thread
threading.Thread(target=input_thread, daemon=True).start()

ser = serial.Serial('COM4', 115200, timeout=0.001)
buffer = b''

# Creating CSV and writing header if not exists
if not os.path.exists(csv_file):
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp'] + [f'Channel_{i+1}' for i in range(8)] + ['eye_closed'])

# Starting reading and writing to CSV
with open(csv_file, 'a', newline='') as f:
    writer = csv.writer(f)
    print("Now collecting data... Type 'c' or 'o' anytime to change eye status. Press Ctrl+C to stop.")

    try:
        while True:
            buffer += ser.read(FRAME_SIZE)

            while len(buffer) >= FRAME_SIZE:
                marker = struct.unpack('<I', buffer[0:4])[0]

                if marker == FRAME_MARKER:
                    frame = buffer[:FRAME_SIZE]
                    values = struct.unpack('<10I', frame)
                    timestamp = values[1]
                    channels = values[2:]
                    with eye_lock:
                        current_eye = eye_closed
                    writer.writerow([timestamp] + list(channels) + [current_eye])
                    buffer = buffer[FRAME_SIZE:]
                else:
                    buffer = buffer[1:]

    except KeyboardInterrupt:
        print("\nData collection stopped.")
