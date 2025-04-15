import socket
import time
from datetime import datetime
import asyncio
import json
import numpy as np
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from threading import Thread
import struct
import logging
import websockets
import msgpack

HOST = "224.1.1.1"  # Replace with your Pico's IP address
PORT = 5005
WINDOW_SIZE = 200  # Number of samples to show
SAMPLES_PER_PACKET = 8

logging.basicConfig(level=logging.INFO)
web_logger = logging.getLogger(__name__)

data_buffer = {
    "timestamps": [],
    "values": {f"CH{i}": [] for i in range(8)}
}

max_points = 2000
start_timestamp = time.perf_counter_ns()

# HANDLE INCOMING EEG DATA FROM RPI PICO DEVICE
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
            # await asyncio.sleep(0.00001)

    async def disconnect_client(self):
        await self.socket.close()

    def get_time_elapsed(self):
        return int((time.perf_counter_ns() - start_timestamp)/1000000)

    def handle_packets(self):
        raw_data, addr = self.socket.recvfrom(1024)
        sensor_data = json.loads(raw_data.decode())

        self.timestamp = self.get_time_elapsed()
        channel_data = []
        for i in range(8):
            channel_key = f"CH{i}"
            # data_buffer["timestamps"].append(self.timestamp)
            if channel_key in sensor_data:
                value = sensor_data[channel_key]

                # data_buffer["values"][channel_key].append(value)

                # if len(data_buffer["timestamps"]) > max_points:
                #     data_buffer["timestamps"].pop(0)
                #     for key in data_buffer["values"]:
                #         data_buffer["values"][key].pop(0)
            channel_data.append(value)
        self.data_received.emit(self.timestamp, channel_data)

    def run(self):
        """The main loop for the QThread, sets up a new asyncio event loop
        and starts the websocket connection process."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.connect())


# API TO HANDLE SENDING LABELED INFORMATION
class WebSocketServer(QObject):
    def __init__(self, port=4242):
        super().__init__()
        self.port = port
        self.clients = set()
        self.server = None
        self.loop = None
        self.thread = None
        self.running = False
        self.start_server()

    def start_server(self):
        """Start WebSocket server with proper event loop handling"""
        def run_server():
            # Create new event loop for this thread
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Define async main server task
            async def server_main():
                self.server = await websockets.serve(
                    self.handle_connection,
                    "0.0.0.0",
                    self.port
                )
                self.running = True
                await self.server.start_serving()

            # Run the server until stopped
            try:
                self.loop.run_until_complete(server_main())
                self.loop.run_forever()
            finally:
                self.running = False

        # Start the server in a dedicated daemon thread
        self.thread = Thread(target=run_server, daemon=True)
        self.thread.start()

    async def handle_connection(self, websocket):
        """Handle client connections"""
        self.clients.add(websocket)
        try:
            async for message in websocket:
                print(f"Received message: {message}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)

    def send_data(self, data):
        """Thread-safe data broadcast"""
        # if not self.running or not self.clients:
        #     return

        async def _send():
            try:
                message = json.dumps(data)
                await asyncio.gather(
                    *[client.send(message) for client in self.clients.copy()]
                )
            except Exception as e:
                print(f"WebSocket send error: {e}")

        asyncio.run_coroutine_threadsafe(_send(), self.loop)

    def stop_server(self):
        """Clean shutdown procedure"""
        if self.loop and self.running:
            # Close server and clients
            self.loop.call_soon_threadsafe(self.server.close)
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join(timeout=1)
            self.running = False