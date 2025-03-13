import pyedflib
import csv
import numpy as np
import struct
from threading import Thread, Lock
from queue import Queue, Empty

class FileHandler:
    def __init__(self):
        """Initialize the file handler with a background writer.
        
        :param raw_file_path: Path to the binary file for storing raw data."""
        self.raw_file_path = "data/raw_data.bin"  
        self.data_queue = Queue()
        self.running = True
        self.lock = Lock()
        self.worker_thread = Thread(target=self._write_worker, daemon=True)
        self.worker_thread.start()

    def _write_worker(self):
        """Background thread for writing data to disk."""
        with open(self.raw_file_path, 'ab') as f:
            while self.running:
                try:
                    data_batch = []
                    while len(data_batch) < 100:
                        data = self.data_queue.get(timeout=0.1)
                        data_batch.append(data)
                except Empty:
                    data_batch = []
                
                if data_batch:
                    packed = b''
                    for timestamp, channels in data_batch:
                        if channels.size != 8:
                            print(f"Invalid channel data length: {channels.size} (expected 8)")
                            continue
                        packed += struct.pack('<I8f', timestamp, *channels)
                    f.write(packed)
                    f.flush()

    def add_data(self, timestamp, channels):
        """Add new data to the write queue (non-blocking).
        
        :param timestamp: Integer representing the timestamp of the new data.
        :param channels: NumPy array of shape (8,) containing the channel data."""
        if channels.size != 8:
            print(f"Invalid channel data length: {channels.size} (expected 8)")
            return
        self.data_queue.put((timestamp, channels))

    def stop(self):
        """Stop the background writer and clean up."""
        self.running = False
        self.worker_thread.join()

    def export_data(self, file_path, channel_names, mode='full'):
        """Export data to a CSV file.
        
        :param file_path: The path to the CSV file.
        :param channel_names: The channel names to export.
        :param mode: 'full' to export all data or 'append' to append real-time data.
        :return: True if the data was successfully exported, False otherwise."""
        try:
            if mode == 'full':
                with open(self.raw_file_path, 'rb') as f:
                    content = f.read()
                
                n_samples = len(content) // 36
                timestamps = []
                data = np.zeros((8, n_samples), dtype=float)
                
                for i in range(n_samples):
                    chunk = content[i*36 : (i+1)*36]
                    ts = struct.unpack('<I', chunk[:4])[0]
                    channels = struct.unpack('<8f', chunk[4:36])
                    timestamps.append(ts / 1000.0)
                    data[:, i] = channels
                
                with open(file_path, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    print(channel_names)
                    writer.writerow(["Time"] + channel_names)
                    
                    for i in range(len(timestamps)):
                        row = [timestamps[i]] + [data[j][i] for j in range(len(channel_names))]
                        writer.writerow(row)
            
            elif mode == 'append':
                with open(file_path, mode='a', newline='') as file:
                    writer = csv.writer(file)

                    if file.tell() == 0:
                        writer.writerow(["Time"] + channel_names)

                    with open(self.raw_file_path, 'rb') as f:
                        f.seek(-36, 2)
                        chunk = f.read(36)
                        ts = struct.unpack('<I', chunk[:4])[0]
                        channels = struct.unpack('<8f', chunk[4:36])
                    
                    writer.writerow([ts / 1000.0] + list(channels))
            
            print(f"Data successfully exported to {file_path}")
            return True
        except Exception as e:
            print(f"Error exporting data: {e}")
            return False

def load_file(file_path):
    """Load an EDF file using pyedflib and return its signal data, time, and channel names.
    
    :param file_path: The path to the EDF file.
    :return: A tuple containing the signal data, time array, and channel names."""
    try:
        with pyedflib.EdfReader(file_path) as f:
            n_signals = f.signals_in_file
            signal_data = [f.readSignal(i) for i in range(n_signals)]
            channel_names = f.getSignalLabels()
            
            sampling_frequency = f.getSampleFrequency(0)
            n_samples = len(signal_data[0])

            time = np.arange(n_samples) / sampling_frequency

        return np.array(signal_data), time, channel_names, sampling_frequency
    except Exception as e:
        print(f"Error loading file with pyedflib: {e}")
        return None, None, None