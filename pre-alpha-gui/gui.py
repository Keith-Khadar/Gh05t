import tkinter as tk
from tkinter import filedialog, ttk
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import eeglib  # eeglib library

class EEGVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("EEG Data Visualizer")
        self.root.geometry("1200x800")

        self.main_frame = ttk.Frame(root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=0, column=0, columnspan=2, sticky='nsew')

        # --- buttons --- #
        self.load_button = ttk.Button(self.button_frame, text="Load EEG Data", command=self.load_eeg_data)
        self.load_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.dummy_button = ttk.Button(self.button_frame, text="Generate Dummy Data", command=self.generate_dummy_data)
        self.dummy_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.clear_button = ttk.Button(self.button_frame, text="Clear", command=self.clear_plots)
        self.clear_button.pack(side=tk.LEFT, padx=10, pady=10)

        # --- layout config --- # 
        self.main_frame.grid_columnconfigure(0, weight=2)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=3)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1)

        # --- plots --- #
        self.eeg_frame = ttk.LabelFrame(self.main_frame, text="EEG Waveforms", padding=(10, 10))
        self.eeg_frame.grid(row=1, column=0, rowspan=2, sticky='nsew', padx=5, pady=5)

        self.freq_frame = ttk.LabelFrame(self.main_frame, text="Frequency Domain", padding=(10, 10))
        self.freq_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)

        self.focus_frame = ttk.LabelFrame(self.main_frame, text="Alpha vs Beta", padding=(10, 10))
        self.focus_frame.grid(row=2, column=1, sticky='nsew', padx=5, pady=5)

        self.eeg_fig, self.eeg_ax = plt.subplots(nrows=8, ncols=1, sharex=True, figsize=(8, 6))
        self.freq_fig, self.freq_ax = plt.subplots(figsize=(5, 5))
        self.focus_fig, self.pie_ax = plt.subplots(figsize=(5, 5))

        self.eeg_canvas = FigureCanvasTkAgg(self.eeg_fig, master=self.eeg_frame)
        self.freq_canvas = FigureCanvasTkAgg(self.freq_fig, master=self.freq_frame)
        self.focus_canvas = FigureCanvasTkAgg(self.focus_fig, master=self.focus_frame)

        self.eeg_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.freq_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.focus_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.eeg_data = None
        self.sampling_rate = 1000

    def load_eeg_data(self):
        file_path = filedialog.askopenfilename(
            title="Select EEG File",
            filetypes=(("CSV files", "*.csv"), ("TSV files", "*.tsv"), ("All files", "*.*"))
        )
        if file_path:
            try:
                file_extension = file_path.split('.')[-1]

                if file_extension == 'tsv':
                    data = pd.read_csv(file_path, sep='\t')
                else:
                    data = pd.read_csv(file_path)

                self.sampling_rate = data.iloc[0, 0]
                self.eeg_data = data.iloc[:, 1:].values

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
        if self.eeg_data is not None:
            self.eeg_data = np.array([
                eeglib.preprocessing.bandPassFilter(channel, self.sampling_rate, highpass=1, lowpass=30)
                for channel in self.eeg_data
            ])
            self.update_eeg_plot()
            self.update_frequency_plot(self.eeg_data[0])
            self.update_focus_plot()

    def update_eeg_plot(self):
        for i, channel in enumerate(self.eeg_data):
            self.eeg_ax[i].cla()
            self.eeg_ax[i].plot(channel, label=f'Channel {i + 1}', color=f'C{i}')
            self.eeg_ax[i].legend()
            self.eeg_ax[i].grid(True)
            self.eeg_ax[i].set_ylabel('Amplitude')
        self.eeg_ax[-1].set_xlabel('Samples')

        self.eeg_canvas.draw()

    def update_frequency_plot(self, eeg_channel):
        freq = np.fft.fftfreq(len(eeg_channel), d=1 / self.sampling_rate)
        fft_values = np.fft.fft(eeg_channel)

        freq_mask = (freq >= 0) & (freq <= 60)
        self.freq_ax.cla()
        self.freq_ax.plot(freq[freq_mask], np.abs(fft_values)[freq_mask], label='Power Spectrum', color='blue')
        self.freq_ax.set_xlabel('Frequency (Hz)')
        self.freq_ax.set_ylabel('Magnitude')
        self.freq_ax.legend()
        self.freq_ax.grid(True)

        self.freq_canvas.draw()

    def update_focus_plot(self):
        total_alpha = np.random.rand()
        total_beta = np.random.rand()

        self.pie_ax.cla()
        self.pie_ax.pie([total_alpha, total_beta], labels=['Alpha', 'Beta'], autopct='%1.1f%%', startangle=90)
        self.pie_ax.set_title('Alpha vs Beta Signal Distribution')

        self.focus_canvas.draw()

    def clear_plots(self):
        self.eeg_data = None

        for ax in self.eeg_ax:
            ax.cla()
        self.freq_ax.cla()
        self.pie_ax.cla()

        self.eeg_canvas.draw()
        self.freq_canvas.draw()
        self.focus_canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = EEGVisualizer(root)
    root.mainloop()
