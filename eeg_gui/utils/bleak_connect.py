import asyncio # https://docs.python.org/3/library/asyncio.html
from bleak import BleakClient, BleakScanner # https://github.com/hbldh/bleak
import struct
import numpy as np
import traceback
import logging # debugging tools; ref : https://github.com/hbldh/bleak/blob/develop/examples/service_explorer.py
# Reference : https://www.aranacorp.com/en/ble-communication-with-esp32/

# Replace with your ESP32's characteristic UUID
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
DEVICE_NAME = "XIAO_ESP32C6"

logging.basicConfig(level=logging.INFO)
bleak_logger = logging.getLogger(__name__) # 

class EEGBLE:
    def __init__(self, shared_eeg, callback=None):
        self.client = None
        self.shared_eeg = shared_eeg
        self.data_callback = callback

    async def connect(self):
        bleak_logger.info("Scanning for devices...")

        devices = await BleakScanner.discover(timeout=10.0)

        for device in devices:
            print(f"Found device: {device.name} - {device.address}")
            if device.name and "XIAO_ESP32C6" in device.name:
                esp32_address = device.address
                break

        if esp32_address is None:
            print("XIAO_ESP32C6 not found.")
            return
        
        try:
            bleak_logger.info(f"Connecting to XIAO_ESP32C6 ({esp32_address})...")
            self.client = BleakClient(esp32_address, disconnected_callback=self.disconnect, winrt=dict(use_cached_services=False))
            
            await self.client.connect()
            if not self.client.is_connected:
                print("Failed to connect to XIAO_ESP32C6.")
                return

            bleak_logger.info("Connected successfully!")
            
            services = await self.client.get_services()
            for service in services:
                if service.uuid == SERVICE_UUID:
                    print(f"Found Service: {service.uuid}")
                    for char in service.characteristics:
                        print(f"  Characteristic: {char.uuid} | Properties: {char.properties}")
                        if char.uuid == CHARACTERISTIC_UUID and "notify" in char.properties:
                            break
                    else:
                        raise ValueError(f"Characteristic {CHARACTERISTIC_UUID} not found or does not support notifications.")
            
            await self.client.start_notify(CHARACTERISTIC_UUID, self.on_eeg_data_received)
            print("Notifications enabled.")

        except Exception as e:
            print(f"An error occurred during connection: {e}")
            print("Full error details:")
            traceback.print_exc()
            if self.client and self.client.is_connected:
                await self.client.disconnect()
            return

        print("BLE connection and notification setup complete.")

    async def disconnect(self):
        if self.client and self.client.is_connected:
            try:
                print("Stopping notifications...")
                await self.client.stop_notify(CHARACTERISTIC_UUID)
            except Exception as e:
                print(f"Error stopping notifications: {e}")

            try:
                print("Disconnecting from device...")
                await self.client.disconnect()
            except Exception as e:
                print(f"Error during disconnection: {e}")

        print("Disconnected successfully!")

    def on_eeg_data_received(self, sender: int, data: bytearray):
        eeg_data = np.frombuffer(data, dtype=np.uint8)
        self.shared_eeg = np.vstack([self.shared_eeg, eeg_data])
        print(f"Received EEG data: {eeg_data}")
