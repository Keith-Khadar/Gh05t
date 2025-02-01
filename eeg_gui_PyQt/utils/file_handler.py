import pyedflib
import csv
import numpy as np

def load_file(file_path):
    """Load an EDF file using pyedflib and return its signal data, time, and channel names."""
    try:
        with pyedflib.EdfReader(file_path) as f:
            n_signals = f.signals_in_file
            signal_data = [f.readSignal(i) for i in range(n_signals)]
            channel_names = f.getSignalLabels()  # Extract channel names
            
            sampling_frequency = f.getSampleFrequency(0)
            n_samples = len(signal_data[0])

            # Create the time array based on the number of samples and the sampling frequency
            time = np.arange(n_samples) / sampling_frequency

        # Return signal data, time, and channel names
        return np.array(signal_data), time, channel_names
    except Exception as e:
        print(f"Error loading file with pyedflib: {e}")
        return None, None, None
    
def export_data(file_path, data, time, channel_names):
    """Export the data to a CSV file."""
    try:
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Time"] + channel_names)  # Header row
            
            # Write data row-wise
            for i in range(len(time)):
                row = [time[i]] + [data[j][i] for j in range(len(channel_names))]
                writer.writerow(row)
        
        print(f"Data successfully exported to {file_path}")
        return True
    except Exception as e:
        print(f"Error exporting data: {e}")
        return False
