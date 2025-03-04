import pyedflib
import csv
import numpy as np

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
    
def export_data(file_path, data, time, channel_names):
    """Export the data to a CSV file.
    
    :param file_path: The path to the CSV file.
    :param data: The signal data to export.
    :param time: The time array to export.
    :param channel_names: The channel names to export.
    :return: True if the data was successfully exported, False otherwise."""
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
    
def export_rt_data(file_path, data, time, channel_names):
    """Export the real-time data to a CSV file.
    
    :param file_path: The path to the CSV file.
    :param data: The signal data to export.
    :param time: The time array to export.
    :param channel_names: The channel names to export.
    :return: True if the data was successfully exported, False otherwise"""
    try:
        with open(file_path, mode='a', newline='') as file:
            writer = csv.writer(file)

            if file.tell() == 0:
                writer.writerow(["Time"] + channel_names)

            if len(data[0]) != len(time):
                raise ValueError("Data and time lengths do not match.")
            
            for i in range(len(time)):
                row = [time[i]] + [data[j][i] for j in range(data.shape[0])]
                writer.writerow(row)
        
        print(f"Data successfully exported to {file_path}")
        return True
    except Exception as e:
        print(f"Error exporting data: {e}")
        return False
