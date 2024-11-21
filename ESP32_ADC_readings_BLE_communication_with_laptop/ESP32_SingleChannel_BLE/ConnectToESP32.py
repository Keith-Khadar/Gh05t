# References:
# https://bleak.readthedocs.io/en/latest/index.html
# https://bleak.readthedocs.io/en/latest/api/index.html
# https://pypi.org/project/bleak/

import asyncio
from bleak import BleakClient, BleakScanner

# Define the UUIDs used in the ESP32 code
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

    # Connect to the ESP32 device
    async with BleakClient(esp32_address) as client:
        if not await client.is_connected():
            print("Failed to connect to ESP32.")
            return
        print("Connected to ESP32.")

        # Read initial value from characteristic
        initial_value = await client.read_gatt_char(CHARACTERISTIC_UUID)
        print(f"Initial value from ESP32: {initial_value.decode('utf-8')}")

        # Write new data to the characteristic
        #message = "Hello from Python!"
        #await client.write_gatt_char(CHARACTERISTIC_UUID, message.encode())
        #print(f"Sent message to ESP32: {message}")

        # Read the response after writing
        #response = await client.read_gatt_char(CHARACTERISTIC_UUID)
        #print(f"Received response from ESP32: {response.decode('utf-8')}")

        # Continuously read the characteristic in a loop
        for i in range(20):  # Reads 20 times
            response = await client.read_gatt_char(CHARACTERISTIC_UUID)
            print(f"Reading {i + 1}: Received response from ESP32: {response.decode('utf-8')}")
            await asyncio.sleep(1)  # Wait 1 second between reads

# Run the async function
asyncio.run(connect_and_communicate())