import asyncio
import sys
from bleak import BleakClient, BleakScanner
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
import logging
import struct
import time

SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
DEVICE_NAME = "ADS1299_BLE"

logging.basicConfig(level=logging.INFO)
bleak_logger = logging.getLogger(__name__)

class EEGBLE(QThread):
    """A class for managing BLE connections to an EEG device.
    
    Inherits from Qthreads and handlings scanning for, connecting, and receiving notifications from the device."""
    update_status = pyqtSignal(str)
    failure = pyqtSignal()

    def __init__(self, notification_callback):
        """Initializes the EEGBLE instance.

        :param notification_callback (callable): Function to handle incoming notifications."""
        super().__init__()
        self.client = None
        self.notification_callback = notification_callback

    async def connect(self):
        """Scans for BLE devices, connects to the specified device, and starts
        notifications."""
        bleak_logger.info("Scanning for devices...")
        self.update_status.emit("Scanning for devices...")
        devices = await BleakScanner.discover(timeout=10.0)
        esp32_address = None

        for device in devices:
            if device.name and DEVICE_NAME in device.name:
                esp32_address = device.address
                break

        if esp32_address is None:
            self.update_status.emit("Device not found.")
            self.failure.emit()
            return

        try:
            bleak_logger.info(f"Connecting to device ({esp32_address})...")
            self.update_status.emit(f"Connecting to device...")
            self.client = BleakClient(esp32_address, disconnected_callback=self.disconnect, 
                                       winrt=dict(
                                            use_cached_services=False,
                                            scanning_mode="active"
                                        ))
            await self.client.connect()
            if not self.client.is_connected:
                self.update_status.emit("Failed to connect to device.")
                self.failure.emit()
                return

            bleak_logger.info("Connected successfully!")
            self.update_status.emit("Connected successfully!")

            await self.client.start_notify(CHARACTERISTIC_UUID, self.notification_callback)
            print("Notifications enabled.")

            while self.client.is_connected:
                await asyncio.sleep(0.2)

        except Exception as e:
            self.update_status.emit(f"An error occurred during connection: {e}")
            self.failure.emit()
            logging.exception(e)
            if self.client and self.client.is_connected:
                await self.client.disconnect()

    async def disconnect_client(self):
        """Disconnects the BLE client and stops notifications."""
        if self.client:
            try:
                await self.client.stop_notify(CHARACTERISTIC_UUID)
                await self.client.disconnect()
            except Exception as e:
                print(f"Error during disconnection: {e}")
            print("Disconnected successfully!")

class BLEWorker(QThread):
    """A class for managing the BLE worker thread that communicates with the EEG device.
    
    This class inherits from QThread and handles notifications and data processing."""
    status_update_signal = pyqtSignal(str)
    data_received = pyqtSignal(int, list)
    connection_failed_signal = pyqtSignal()

    def __init__(self):
        """Initializes the BLEWorker instance and sets up the BLE device."""
        super().__init__()
        self.ble_device = EEGBLE(self.handle_notification)
        self.ble_device.update_status.connect(self.update)
        self.ble_device.failure.connect(self.error)
        self.data_buffer = bytearray()

    async def run_ble(self):
        """Initiates the BLE connection process by calling the connect method
        on the EEGBLE instance."""
        await self.ble_device.connect()

    async def disconnect(self):
        """Disconnects the BLE device by calling the disconnect_client method
        on the EEGBLE instance."""
        await self.ble_device.disconnect_client()

    def handle_notification(self, sender, data):
        """Handles incoming BLE notifications by processing the received data.

        :param sender: The sender of the notification.
        :param data (bytes): The raw data received from the BLE device. 
            Received in the format [timestamp/milliseconds (1 byte), channels 1-8 (3 bytes each)]"""
        self.data_buffer.extend(data)

        while len(self.data_buffer) >= 36:
            full_packet = self.data_buffer[:36]
            self.data_buffer = self.data_buffer[36:]

            result = self.process_ble_data(full_packet)
            if result:
                timestamp, channel_data = result
                self.data_received.emit(timestamp, channel_data)

    def process_ble_data(self, raw_data):
        """Processes the raw BLE data and extracts the timestamp and channel data.

        :param raw_data (bytes): The raw data received from the BLE device.

        :return tuple: A tuple containing the timestamp (int) and channel data (list of int)
                   if processing is successful, otherwise None."""
        try:
            if len(raw_data) == 36:
                timestamp = struct.unpack('<I', raw_data[:4])[0]
                channel_data = list(struct.unpack('<8i', raw_data[4:36]))
                # print(channel_data)
                return timestamp, channel_data
            else:
                print(f"Unexpected data length: {len(raw_data)} bytes")
                return None
        except Exception as e:
            print(f"Error processing BLE data: {e}")
            self.status_update_signal.emit(f"Error processing BLE data: {e}")
            return None

    def run(self):
        """The main loop for the QThread, sets up a new asyncio event loop
        and starts the BLE connection process."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_ble())

    def update(self, message):
        """Emits a status update signal with the given message.

        :param message (str): The status message to emit."""
        self.status_update_signal.emit(message)

    def error(self):
        """Emits a connection failed signal when an error occurs."""
        self.connection_failed_signal.emit()