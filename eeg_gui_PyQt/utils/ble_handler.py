import asyncio
from bleak import BleakClient, BleakScanner
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QStatusBar
import traceback
import logging
import time
import struct

# Replace with your ESP32's characteristic UUID
# XIAO ESP32-C6 OR FIREBEETLE ESP32 DEV
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
DEVICE_NAME = "ADS1299_BLE"

logging.basicConfig(level=logging.INFO)
bleak_logger = logging.getLogger(__name__)

class EEGBLE(QThread):
    update_status = pyqtSignal(str)
    failure = pyqtSignal()

    def __init__(self, notification_callback):
        super().__init__()
        self.client = None
        self.notification_callback = notification_callback

    async def connect(self):
        bleak_logger.info("Scanning for devices...")
        self.update_status.emit("Scanning for devices...")
        devices = await BleakScanner.discover(timeout=10.0)
        esp32_address = None

        for device in devices:
            print(f"Found device: {device.name} - {device.address}")
            if device.name and DEVICE_NAME in device.name:
                esp32_address = device.address
                break

        if esp32_address is None:
            print("Device not found.")
            self.update_status.emit("Device not found.")
            self.failure.emit()
            return

        try:
            bleak_logger.info(f"Connecting to device ({esp32_address})...")
            self.update_status.emit(f"Connecting to device ({device.name})...")
            self.client = BleakClient(esp32_address, disconnected_callback=self.disconnect)

            await self.client.connect()
            if not self.client.is_connected:
                print("Failed to connect to device.")
                self.update_status.emit("Failed to connect to device.")
                self.failure.emit()
                return

            bleak_logger.info("Connected successfully!")
            self.update_status.emit(f"Connected to device successfully!: {device.name} - {esp32_address}")

            await self.client.start_notify(CHARACTERISTIC_UUID, self.notification_callback)

            print("Notifications enabled.")

        except Exception as e:
            print(f"An error occurred during connection: {e}")
            self.update_status.emit(f"An error occurred during connection: {e}")
            self.failure.emit()
            traceback.print_exc()
            if self.client and self.client.is_connected:
                await self.client.disconnect()

    async def disconnect_client(self):
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
    status_update_signal = pyqtSignal(str)
    data_received = pyqtSignal(int, list)
    connection_failed_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.ble_device = EEGBLE(self.handle_notification)
        self.ble_device.update_status.connect(self.update)
        self.ble_device.failure.connect(self.error)
        self.data_buffer = []

    async def run_ble(self):
        await self.ble_device.connect()

    async def disconnect(self):
        await self.ble_device.disconnect_client()

    def handle_notification(self, sender, data):
        """Callback function for BLE notifications."""
        self.data_buffer.extend(data)

        while len(self.data_buffer) >= 36:
            full_packet = self.data_buffer[:36]
            self.data_buffer = self.data_buffer[36:]

            result = self.process_ble_data(full_packet)
            if result:
                timestamp, channel_data = result
                self.data_received.emit(timestamp, channel_data)

    def process_ble_data(self, raw_data):
        """Process incoming raw BLE data into numerical values."""
        try:
            # Unpack the first 4 bytes as the timestamp (unsigned long) and the next 8 * 4 bytes as the channel data
            if len(raw_data) >= 36:
                timestamp, *channel_data = struct.unpack('<I 8i', raw_data)
                channel_data = list(channel_data)
                return timestamp, channel_data
            else:
                print(f"Unexpected data length: {len(raw_data)} bytes")
                self.status_update_signal.emit(f"Unexpected data length: {len(raw_data)} bytes")
                return None
        except Exception as e:
            print(f"Error processing BLE data: {e}")
            self.status_update_signal.emit(f"Error processing BLE data: {e}")
            traceback.print_exc()
            return None

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_ble())

    def update(self, message):
        self.status_update_signal.emit(f"{message}")

    def error(self):
        self.connection_failed_signal.emit()