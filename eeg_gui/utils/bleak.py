import asyncio # https://docs.python.org/3/library/asyncio.html
from bleak import BleakClient, BleakScanner # https://github.com/hbldh/bleak
import struct
import numpy as np
import logging # debugging tools; ref : https://github.com/hbldh/bleak/blob/develop/examples/service_explorer.py
# Reference : https://www.aranacorp.com/en/ble-communication-with-esp32/

# Replace with your ESP32's characteristic UUID
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
DEVICE_NAME = "XIAO_ESP32C6"

logging.basicConfig(level=logging.INFO)
bleak_logger = logging.getLogger(__name__) # 

class EEGBLE:
    def __init__(self, callback=None):
        self.client = None
        self.data_callback = callback

    async def connect(self):
        bleak_logger.info("Scanning for devices...")

        device = await BleakScanner.discover()
        esp32_address = None

        esp32_address = None
        if device.name and "XIAO_ESP32C6" in device.name:
            esp32_address = device.address

        if device is None:
            print("XIAO_ESP32C6 not found.")
            return
        
        bleak_logger.info("Connecting to XIAO_ESP32C6 ({esp32_address})...")

        self.client = BleakClient(esp32_address)
        await self.client.connect()
        bleak_logger.info("Connected successfully!")

        await self.client.start_notify(self.characteristic_uuid, self.on_eeg_data_received)

    async def disconnect(self):
        if self.client and self.client.is_connected:
            bleak_logger.info("Disconnecting...")
            await self.client.disconnect()
            bleak_logger.info("Fully Disconnected.")

    async def stop_notifications(self):
        if self.client and self.client.is_connected:
            bleak_logger.info("Unsubscribing from notifications...")
            await self.client.stop_notify(CHARACTERISTIC_UUID)
            bleak_logger.info("Unsubscribed successfully!")

    def on_eeg_data_received(self, sender, data):
        """This method is called when data is received from the ESP32."""
        self.eeg_data = np.frombuffer(data, dtype=np.uint8)

        # Print the received EEG data for debugging
        print(f"Received EEG data: {self.eeg_data}")

        if self.data_callback:
            self.data_callback(self.eeg_data)
