import asyncio
from bleak import BleakClient, BleakScanner
from PyQt5.QtCore import QThread, pyqtSignal
import traceback
import logging
import time

# Replace with your ESP32's characteristic UUID
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
DEVICE_NAME = "XIAO_ESP32C6"

logging.basicConfig(level=logging.INFO)
bleak_logger = logging.getLogger(__name__)

class EEGBLE:
    def __init__(self, notification_callback):
        self.client = None
        self.notification_callback = notification_callback

    async def connect(self):
        bleak_logger.info("Scanning for devices...")

        devices = await BleakScanner.discover(timeout=10.0)
        esp32_address = None

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
            self.client = BleakClient(esp32_address, disconnected_callback=self.disconnect)

            await self.client.connect()
            if not self.client.is_connected:
                print("Failed to connect to XIAO_ESP32C6.")
                return

            bleak_logger.info("Connected successfully!")

            await self.client.start_notify(CHARACTERISTIC_UUID, self.notification_callback)
            print("Notifications enabled.")

        except Exception as e:
            print(f"An error occurred during connection: {e}")
            traceback.print_exc()
            if self.client and self.client.is_connected:
                await self.client.disconnect()

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

class BLEWorker(QThread):
    data_received = pyqtSignal(bytes)  # Signal to send data to UI

    def __init__(self):
        super().__init__()
        self.ble_device = EEGBLE(self.handle_notification)

    async def run_ble(self):
        await self.ble_device.connect()

    def handle_notification(self, sender, data):
        """Callback function for BLE notifications."""
        parsed_data = self.process_ble_data(data)  # Convert raw bytes to usable data
        self.data_received.emit(parsed_data)  # Emit signal with processed data

    def process_ble_data(self, raw_data):
        """Process incoming raw BLE data into numerical values."""
        try:
            data_values = list(raw_data)
            timestamp = time.time()
            return (data_values, timestamp)
        except Exception as e:
            print(f"Error processing BLE data: {e}")
            return None

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_ble())