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
        with open(self.raw_file_path, 'ab') as f:
            while self.running:
                try:
                    data_batch = []
                    while len(data_batch) < 100:
                        # Modified to accept (timestamp, channels, label)
                        data = self.data_queue.get(timeout=0.1)
                        data_batch.append(data)
                except Empty:
                    data_batch = []
                
                if data_batch:
                    packed = b''
                    for timestamp, channels, label in data_batch:
                        # Pack with label flag (1=has label, 0=no label)
                        has_label = 1 if label is not None else 0
                        label_value = label if has_label else 0.0
                        packed += struct.pack(
                            '<I8fBf',  # New format: timestamp, 8 channels, flag, label
                            timestamp,
                            *channels,
                            has_label,
                            label_value
                        )
                    f.write(packed)
                    f.flush()

    def add_data(self, timestamp, channels, label=None):
        """Add new data to the write queue (non-blocking)."""
        self.data_queue.put((timestamp, channels, label))

    def stop(self):
        """Stop the background writer and clean up."""
        self.running = False
        self.worker_thread.join()

    def export_data(self, file_path, channel_names, mode='full'):
        try:
            if mode == 'full':
                with open(self.raw_file_path, 'rb') as f:
                    content = f.read()
                
                entry_size = 41
                n_samples = len(content) // entry_size
                
                timestamps = []
                data = np.zeros((8, n_samples), dtype=float)
                labels = np.full(n_samples, np.nan, dtype=float)
                
                for i in range(n_samples):
                    chunk = content[i*entry_size : (i+1)*entry_size]
                    unpacked = struct.unpack('<I8fBf', chunk)
                    ts = unpacked[0]
                    ch_data = unpacked[1:9]
                    has_label = unpacked[9]
                    label_val = unpacked[10]
                    
                    timestamps.append(ts / 1000.0)
                    data[:, i] = ch_data
                    if has_label:
                        labels[i] = label_val
                
                has_labels = not np.isnan(labels).all()
                
                with open(file_path, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    
                    headers = ["Time"] + channel_names
                    if has_labels:
                        headers += ["Label"]
                    writer.writerow(headers)
                    
                    for i in range(len(timestamps)):
                        row = [timestamps[i]] + [data[j][i] for j in range(len(channel_names))]
                        if has_labels:
                            label_str = labels[i] if not np.isnan(labels[i]) else ''
                            row.append(label_str)
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
    
def export_data_from_import(file_path, data, time, channel_names):
    """Export data to a CSV file after importing from an EDF file."""
    try:
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Time"] + channel_names)
            
            for i in range(len(time)):
                row = [time[i]] + [data[j][i] for j in range(len(channel_names))]
                writer.writerow(row)
        
        print(f"Data successfully exported to {file_path}")
        return True
    except Exception as e:
        print(f"Error exporting data: {e}")
        return False