import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # backend
from scipy.fft import fft, fftfreq

class Frequency:
    def __init__(self, main_frame, eeg_data, sampling_rate, start_datetime):
        self.main_frame = main_frame

        self.freq_frame = ttk.LabelFrame(self.main_frame, text="Frequency Domain", padding=(10, 10))
        self.freq_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)

        self.freq_fig, self.freq_ax = plt.subplots(figsize=(5, 6))
        self.freq_canvas = FigureCanvasTkAgg(self.freq_fig, master=self.freq_frame)
        self.freq_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.channel_label = ttk.Label(self.freq_frame, text="Select Channel:")
        self.channel_label.place(x=10, y=10)
        self.channel_combobox = ttk.Combobox(self.freq_frame, state="readonly", values=[])
        self.channel_combobox.place(x=100, y=10)
        self.channel_combobox.bind("<<ComboboxSelected>>", self.update_frequency_plot)

        self.eeg_data = eeg_data
        self.sampling_rate = sampling_rate
        self.start_datetime = start_datetime

        self.update_channel_dropdown()

    def update_frequency_plot(self, event=None):
        selected_channel = self.channel_combobox.get()
        if not selected_channel or self.eeg_data is None:
            return
        
        # Extract channel index from the selection (e.g., "Channel 1" -> index 0)
        channel_index = int(selected_channel.split()[-1]) - 1
        
        # Get the data for the selected channel
        data = self.eeg_data[channel_index]
        N = len(data)
        T = 1.0 / self.sampling_rate
        x = np.linspace(0.0, N*T, N, endpoint=False)

        # Perform FFT
        yf = fft(data)
        xf = fftfreq(N, T)[:N//2]

        # Update the frequency plot
        self.freq_ax.clear()
        self.freq_ax.plot(xf, 2.0/N * np.abs(yf[0:N//2]))
        self.freq_ax.set_title(f"Frequency Spectrum - {selected_channel}")
        self.freq_ax.set_xlabel("Frequency (Hz)")
        self.freq_ax.set_ylabel("Amplitude")
        self.freq_fig.tight_layout()
        self.freq_fig.subplots_adjust(top=0.8)
        self.freq_ax.set_xlim(0,80)
        self.freq_ax.grid(True)

        # Redraw the canvas
        self.freq_canvas.draw()

    def update_channel_dropdown(self):
        if self.eeg_data:
            channel_names = [f"Channel {i+1}" for i in range(len(self.eeg_data))]
            self.channel_combobox.config(values=channel_names)
            if channel_names:
                self.channel_combobox.set(channel_names[0])  # Set the default selected channel

    def set_eeg_data(self, eeg_data):
        self.eeg_data = eeg_data
        self.update_channel_dropdown()

    def clear_plot(self):
        self.freq_ax.cla() # Clear the plot
        self.freq_canvas.draw()