import asyncio
import csv
import matplotlib.pyplot as plt
from bleak import BleakClient, BleakScanner

# Define the UUIDs
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

async def connect_and_communicate():
    # Scan for devices
    devices = await BleakScanner.discover()
    esp32_address = None

    # Find ESP32 by name
    for device in devices:
        if device.name and "XIAO_ESP32C6" in device.name:
            esp32_address = device.address
            print(f"Found ESP32 BLE device with address: {esp32_address}")
            break

    if esp32_address is None:
        print("ESP32 BLE device not found.")
        return

    # Create a list to store received data
    data_buffer = []

    # Connect to the ESP32 device
    async with BleakClient(esp32_address) as client:
        if not await client.is_connected():
            print("Failed to connect to ESP32.")
            return
        print("Connected to ESP32.")

        # Continuously read the characteristic in a loop
        for i in range(20):  # Reads 20 times
            response = await client.read_gatt_char(CHARACTERISTIC_UUID)
            # Decode and clean response
            decoded_response = response.decode("utf-8").strip()
            print(f"Reading {i + 1}: Received response from ESP32: {decoded_response}")

            # Add the decoded response to the data buffer
            try:
                # Attempt to convert response to a float or integer
                numeric_value = float(decoded_response) if '.' in decoded_response else int(decoded_response)
                data_buffer.append(numeric_value)
            except ValueError:
                # If conversion fails, save as string
                data_buffer.append(decoded_response)
            # Wait 1 second between reads
            await asyncio.sleep(1)

    # Save the data buffer to a CSV file
    print("Saving data to input_data.csv...")
    with open("input_data.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Write header
        writer.writerow(["Value"])
        for value in data_buffer:
            # Write each value as a row
            writer.writerow([value])
    print("Data saved successfully.")

def read_and_plot_data_from_csv(file_path):
    # Lists to store data for each column
    data_columns = []

    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            header = next(reader)  # Read header
            print("Header:", header)

            # Parse rows
            for row in reader:
                # Split values in each cell by commas
                split_values = row[0].split(",")
                for i, value in enumerate(split_values):
                    if len(data_columns) <= i:
                        # Create a new list for each column
                        data_columns.append([])
                    try:
                        # Append numeric value to the respective column
                        data_columns[i].append(float(value))
                    except ValueError:
                        print(f"Skipping non-numeric value: {value}")

        # Plot each column as a separate line
        plt.figure(figsize=(10, 6))
        for i, column in enumerate(data_columns):
            plt.plot(range(len(column)), column, marker='o', linestyle='-', label=f"Channel {i + 1}")

        plt.title("Multi-Dimensional Data from BLE Device")
        plt.xlabel("Reading Index")
        plt.ylabel("Values")
        plt.grid(True)
        plt.legend()
        plt.show()

    except Exception as e:
        print(f"An error occurred while reading or plotting the data: {e}")

# Run the async function
asyncio.run(connect_and_communicate())

# Call the plot function
read_and_plot_data_from_csv("input_data.csv")
