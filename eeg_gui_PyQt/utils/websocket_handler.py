import socket
import time
import asyncio
import json
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
import struct
import logging

HOST = "224.1.1.1"  # Replace with your Pico's IP address
PORT = 5005
WINDOW_SIZE = 200  # Number of samples to show
SAMPLES_PER_PACKET = 8

logging.basicConfig(level=logging.INFO)
web_logger = logging.getLogger(__name__)

class EEGWebSocket(QThread):
    status_update_signal = pyqtSignal(str)
    data_received = pyqtSignal(int, list)
    connection_failed_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.data_buffer = bytearray()
        self.timestamp = 0
        self.channel_data = []

        web_logger.info("Scanning for WiFi...")
        self.status_update_signal.emit("Scanning for WiFi...")

    async def connect(self):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
        print(f"Connecting to {HOST}:{PORT}")
        self.socket.bind(("", PORT))
        mreq = struct.pack("4sl", socket.inet_aton(HOST), socket.INADDR_ANY)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


        # self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # print(f"Connecting to {HOST}:{PORT}")
        # self.status_update_signal.emit(f"Connecting to {HOST}:{PORT}")
        # self.socket.connect((HOST, PORT))
        # self.socket.settimeout(1.0)
        print("Connected!")
        self.status_update_signal.emit("Connected!")

        while True:
            self.handle_packets()
            await asyncio.sleep(0.1)

    async def disconnect_client(self):
        await self.socket.close()

    def handle_packets(self):
        # print("entered")
        # try:
        #     raw_data, addr = self.socket.recvfrom(1024)
        #     print(f"Received data from {addr}: {raw_data}")
        #     decoded_data = raw_data.decode("utf-8")
        #     print(f"Decoded Data: {decoded_data}")
        # except Exception as e:
        #     print(f"Error receiving data: {e}")
        
        # try:
            # raw_data = b""

            # while len(self.data_buffer) < 4:  # Keep receiving until we have enough data
            #     raw_data, addr = self.socket.recvfrom(4)
            #     # raw_data = self.socket.recv(18)
            #     if not raw_data:
            #         print("Connection closed by the server")
            #         return

            #     self.data_buffer.extend(raw_data)

            # if len(self.data_buffer) >= 32:
            #     packet = self.data_buffer[:32]  # Take first 36 bytes
            #     self.data_buffer = self.data_buffer[32:]  # Remove processed bytes

            #     if len(packet) >= 36:  # Ensure we have enough bytes to unpack
            #         self.timestamp = int(time.time() * 1000) # milliseconds
            #         self.channel_data = list(struct.unpack('<8i', packet[4:36]))
            #         print(packet)
            #         self.data_received.emit(self.timestamp, self.channel_data)
            
        # while len(self.data_buffer) < 36:  # Keep receiving until we have enough data
        #     raw_data, addr = self.socket.recvfrom(1024)
        #     sensor_data = json.loads(raw_data.decode())
        #     # print(type(sensor_data["CH1"]))
        #     # raw_data = self.socket.recv(18)
        #     if not raw_data:
        #         print("Connection closed by the server")
        #         return

        #     self.data_buffer.extend(sensor_data)
        raw_data, addr = self.socket.recvfrom(1024)
        sensor_data = json.loads(raw_data.decode())

        if len(self.sensor_data) >= 34:
            # sorted_data = [sensor_data[key] for key in sorted(sensor_data.keys(), key=lambda x: int(x[2:]) if x[2:].isdigit() else float('inf'))]
            
            channel_data = np.zeros(8)  # Initialize a list with 8 elements

            for i in range(8):  
                channel_key = f"CH{i}" 
                channel_data[i] = sensor_data[channel_key] 

            # packet = self.data_buffer[:36]  # Take first 36 bytes
            # self.data_buffer = self.data_buffer[36:]  # Remove processed bytes

            self.timestamp = time.time()
            # self.channel_data = list(struct.unpack('<8i', packet[4:36]))
            # print(packet)
            self.data_received.emit(self.timestamp, channel_data)

            # if len(packet) >= 36:  # Ensure we have enough bytes to unpack
            #     self.timestamp = struct.unpack('<I', packet[:4])[0]
            #     self.channel_data = list(struct.unpack('<8i', packet[4:36]))
            #     print(packet)
            #     self.data_received.emit(self.timestamp, self.channel_data)

        # except socket.timeout:
        #     print("timeout")
        #     pass
        # except Exception as e:
        #     print(f"Error: {e}")
        #     self.connection_failed_signal.emit(f"An error occurred: {e}")

    def run(self):
        """The main loop for the QThread, sets up a new asyncio event loop
        and starts the websocket connection process."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.connect())