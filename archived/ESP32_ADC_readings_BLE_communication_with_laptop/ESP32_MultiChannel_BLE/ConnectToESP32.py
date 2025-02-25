# References:
# https://bleak.readthedocs.io/en/latest/index.html
# https://bleak.readthedocs.io/en/latest/api/index.html
# https://pypi.org/project/bleak/
# https://numpy.org/doc/stable/reference/generated/numpy.savez.html
# https://numpy.org/doc/stable/reference/generated/numpy.load.html

import asyncio
import numpy as np
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

    # Save the data buffer to an npz file
    print("Saving data to input_data.npz...")
    np.savez("input_data.npz", data=data_buffer)
    print("Data saved successfully.")

def read_data_from_npz(file_path):
    # Read and print the data from an npz file.
    try:
        # Load the npz file
        data = np.load(file_path, allow_pickle=True)['data']
        print("Data read from file:")
        print(data)
    except Exception as e:
        print(f"An error occurred while reading the NPZ file: {e}")

# Run the async function
asyncio.run(connect_and_communicate())

# Read data from the NPZ file
read_data_from_npz("input_data.npz")