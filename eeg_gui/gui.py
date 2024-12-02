import tkinter as tk
from tkinter import filedialog, ttk
import numpy as np
import pandas as pd
import asyncio
import threading
from utils import Waveform, Frequency, Ratio, EEGBLE
from bleak import BleakClient, logging
import pyedflib # edf support
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # backend

class EEGVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("EEG Data Visualizer")
        self.root.geometry("1200x800")

        self.main_frame = ttk.Frame(root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=0, column=0, columnspan=2, sticky='nsew')

        self.load_button = ttk.Button(self.button_frame, text="Load EEG Data", command=self.load_eeg_data)
        self.load_button.grid(row=0, column=0, padx=10, pady=10)

        self.dummy_button = ttk.Button(self.button_frame, text="Generate Dummy Data", command=self.generate_dummy_data)
        self.dummy_button.grid(row=0, column=1, padx=10, pady=10)

        self.clear_button = ttk.Button(self.button_frame, text="Clear", command=self.clear_plots)
        self.clear_button.grid(row=0, column=2, padx=10, pady=10)

        self.toggle_button = ttk.Button(self.button_frame, text="Use Bluetooth", command=self.toggle_data_source)
        self.toggle_button.grid(row=0, column=3, padx=10, pady=10)

        self.main_frame.grid_columnconfigure(0, weight=2)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=3)

        self.eeg_data = None
        self.ble_eeg_data = np.empty((0, 8), dtype=np.uint8)
        self.sampling_rate = 1000
        self.start_datetime = 0

        self.is_connected = False
        self.is_bluetooth = False

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after_id = None

        self.loop = asyncio.new_event_loop()
        self.root.after(100, self.run_asyncio_event_loop)
        threading.Thread(target=self.start_event_loop, daemon=True).start()

    def start_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        
    def load_eeg_data(self):
        file_path = filedialog.askopenfilename(
            title="Select EEG File",
            filetypes=(("All supported files", "*.csv *.tsv *.txt *.dat *.edf"), ("CSV files", "*.csv"), 
                    ("TSV files", "*.tsv"), ("Text files", "*.txt"), ("DAT files", "*.dat"), 
                    ("EDF files", "*.edf"), ("All files", "*.*"))
        )
        if file_path:
            try:
                file_extension = file_path.split('.')[-1]

                if file_extension in ['csv', 'tsv', 'txt']:
                    sep = '\t' if file_extension == 'tsv' else ','
                    data = pd.read_csv(file_path, sep=sep)
                    self.sampling_rate = data.iloc[0, 0] 
                    self.eeg_data = data.iloc[:, 1:].values

                elif file_extension == 'dat':
                    data = np.loadtxt(file_path)
                    self.sampling_rate = 1000  
                    self.eeg_data = data.T

                elif file_extension == 'edf':
                    edf = pyedflib.EdfReader(file_path)
                    num_signals = edf.signals_in_file
                    signal_labels = edf.getSignalLabels()
                    self.sampling_rate = edf.getSampleFrequency(0)

                    self.start_datetime = edf.getStartdatetime()
                    self.duration = edf.file_duration

                    self.eeg_data = [edf.readSignal(i) for i in range(num_signals)]
                    edf.close()

                self.process_and_visualize_eeg_data()
            except Exception as e:
                tk.messagebox.showerror("Error", f"Failed to load EEG data: {str(e)}")

    def generate_dummy_data(self):
        self.sampling_rate = 1000
        num_samples = 1000
        num_channels = 8
        self.eeg_data = np.random.randn(num_channels, num_samples)
        self.process_and_visualize_eeg_data()

    def process_and_visualize_eeg_data(self):
        def create_waveform_frequency_ratio():
            if self.is_bluetooth:
                self.eeg_data = []
                self.waveform = Waveform(self.main_frame, self.ble_eeg_data, 1, self.start_datetime)
                self.frequency = Frequency(self.main_frame, self.ble_eeg_data, 1, self.start_datetime)
                self.ratio = Ratio(self.main_frame, self.ble_eeg_data, 1, self.start_datetime)
            else:
                if self.eeg_data is not None:
                    self.waveform = Waveform(self.main_frame, self.eeg_data, self.sampling_rate, self.start_datetime)
                    self.frequency = Frequency(self.main_frame, self.eeg_data, self.sampling_rate, self.start_datetime)
                    self.ratio = Ratio(self.main_frame, self.eeg_data, self.sampling_rate, self.start_datetime)
        
        self.root.after(0, create_waveform_frequency_ratio)
        
    def clear_plots(self):
        self.eeg_data = None

        self.waveform.clear_plot()
        self.frequency.clear_plot()
        self.ratio.clear_plot()

    def toggle_data_source(self):
        self.is_bluetooth = not self.is_bluetooth
        if self.is_bluetooth:
            self.toggle_button.config(text="Use File Mode")
            asyncio.run_coroutine_threadsafe(self.start_ble_connection(), self.loop)
        else:
            self.toggle_button.config(text="Use Bluetooth")
            asyncio.run_coroutine_threadsafe(self.stop_ble_connection(), self.loop)
            self.clear_plots()

    async def start_ble_connection(self):
        self.eeg_ble = EEGBLE(self, self.ble_eeg_data)
        await self.eeg_ble.connect()
        self.process_and_visualize_eeg_data()
        self.is_connected = True

    async def stop_ble_connection(self):
        if self.is_connected:
            await self.eeg_ble.disconnect()
            self.is_connected = False

    def on_close(self):
        if self.is_bluetooth:
            asyncio.run(self.stop_ble_connection())
        self.root.quit()

    def run_asyncio_event_loop(self):
        self.loop.create_task(self.asyncio_event_loop())

        self.root.after(100, self.run_asyncio_event_loop)

    async def asyncio_event_loop(self):
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    root = tk.Tk()
    app = EEGVisualizer(root)
    root.mainloop()
