import tkinter as tk
from tkinter import ttk
import numpy as np
import mne
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # backend
from scipy.fft import fft, fftfreq

class Ratio:
    def __init__(self, main_frame, eeg_data, sampling_rate, start_datetime):
        self.main_frame = main_frame

        self.focus_frame = ttk.LabelFrame(self.main_frame, text="EEG Topomap", padding=(10, 10))
        self.focus_frame.grid(row=2, column=1, sticky='nsew', padx=5, pady=5)
        self.focus_fig, self.topomap_ax = plt.subplots(figsize=(5, 3))
        self.focus_canvas = FigureCanvasTkAgg(self.focus_fig, master=self.focus_frame)
        self.focus_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.eeg_data = eeg_data
        self.sampling_rate = sampling_rate
        self.start_datetime = start_datetime

        self.update_head_plot()

    def update_head_plot(self):
        info = mne.create_info(ch_names=['Fp1', 'Fp2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2'],
                               sfreq=self.sampling_rate, ch_types='eeg')
        fake_eeg_values = np.random.randn(len(info['ch_names']))
        montage = mne.channels.make_standard_montage('standard_1020')

        info.set_montage(montage)
        self.topomap_ax.cla()

        mne.viz.plot_topomap(fake_eeg_values, info, axes=self.topomap_ax, show=False, contours=0)
        self.topomap_ax.set_title('EEG Topomap')
        self.focus_canvas.draw()

    def clear_plot(self):
        self.topomap_ax.cla() # Clear the plot
        self.focus_canvas.draw()