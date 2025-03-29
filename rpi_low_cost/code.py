import os
import wifi
import time
import socketpool
import board
import analogio
import digitalio
import json

class AnalogDataTransmitter:

    def __init__(self):
        # Get Info from settings.toml
        try:
            self.ssid = os.getenv('CIRCUITPY_WIFI_SSID')
            self.password = os.getenv('CIRCUITPY_WIFI_PASSWORD')
            self.MULTICAST_GROUP = os.getenv('CIRCUITPY_MULTICAST_GROUP')
            self.PORT = int(os.getenv('CIRCUITPY_PORT'))
            self.RATE = float(os.getenv('CIRCUITPY_RATE'))

        except TypeError:
            print("Could not find WiFi info. Check your settings.toml file!")
            raise

        # Create an analog input pin
        self.sensor = analogio.AnalogIn(board.A0)

        # Initialize GPIO as outputs for Analog MUX
        select_pins = [board.GP18, board.GP19, board.GP20]

        self.select_lines = [digitalio.DigitalInOut(pin) for pin in select_pins]
        for line in self.select_lines:
            line.direction = digitalio.Direction.OUTPUT

        # Configure access point
        wifi.radio.start_ap(ssid=self.ssid, password=self.password)

        # Print access point settings
        print(f"Access point created with SSID: {self.ssid}, password: {self.password}")
        print("My IP address is", str(wifi.radio.ipv4_address_ap))

        # Get access to A pool of socket resources available
        pool = socketpool.SocketPool(wifi.radio)

        # Create a UDP socket
        ## AF_INET specifies the address family (IP v4)
        ## SOCK_DGRAM is a datagram-based protocol (UDP)
        self.udp_socket = pool.socket(pool.AF_INET, pool.SOCK_DGRAM)

        # Start Transmitting
        self.transmit()

    def setSelectLines(self, value):
        # Convert the value to binary and remove the 0b prefix
        binary_value = bin(value)[2:]

        # Pad the value with 0s and make sure that the size is 3
        binary_value = ("000" + binary_value)[-3:]

        # Output the true where you have a 1 and false where you have a 0
        # On the appropriate lines.
        for i, bit in enumerate(reversed(binary_value)):
            self.select_lines[i].value = bool(int(bit))

    def getData(self):
        channels = {}
        for i in range(8):
            channels[f"CH{i}"] = self.sensor.value
            self.setSelectLines(i)
            time.sleep(self.RATE / 8)
        return json.dumps(channels)

    def transmit(self):
        while True:
            data = self.getData()
            self.udp_socket.sendto(data.encode(), (self.MULTICAST_GROUP, self.PORT))
            print(f"Published: {data}")

if __name__ == '__main__':
    AnalogDataTransmitter()

