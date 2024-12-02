import tkinter as tk
from tkinter import ttk
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class Waveform:
    def __init__(self, main_frame, eeg_data, sampling_rate, start_datetime):
        
        self.start_index = 1
        self.time_window = 5

        self.main_frame = main_frame

        self.eeg_frame = ttk.LabelFrame(self.main_frame, text="EEG Waveforms", padding=(10, 10))
        self.eeg_frame.grid(row=1, column=0, rowspan=2, sticky='nsew', padx=5, pady=5)
        self.eeg_fig, self.eeg_ax = plt.subplots(figsize=(8, 6))
        self.eeg_canvas = FigureCanvasTkAgg(self.eeg_fig, master=self.eeg_frame)
        self.eeg_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.eeg_data = eeg_data
        self.sampling_rate = sampling_rate
        self.start_datetime = start_datetime

        self.dragging = False
        self.vline = None
        self.annotations = []
        self.num_samples_per_window = int(self.sampling_rate * self.time_window)

        self.eeg_fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.eeg_fig.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.eeg_fig.canvas.mpl_connect('button_release_event', self.on_release)

        self.update_eeg_plot()

    def update_eeg_plot(self, event=None):
        if isinstance(self.eeg_data, list) and len(self.eeg_data) > 0:
            self.eeg_data = np.array(self.eeg_data)
        
        if event is not None:
            new_start_index = int(event * self.sampling_rate)
            new_start_index = max(0, min(new_start_index, len(self.eeg_data[0]) - self.num_samples_per_window))
            self.shift_window(new_start_index - self.start_index)

        end_index = self.start_index + self.num_samples_per_window

        time_axis = np.linspace(0, self.time_window, self.num_samples_per_window)

        self.eeg_ax.cla()

        for i, channel in enumerate(self.eeg_data):
            channel_data = channel[self.start_index:end_index]
            self.eeg_ax.plot(time_axis, channel_data + i * 100, label=f'Channel {i + 1}', color=f'C{i}')

        start_time_seconds = float(self.start_index) / self.sampling_rate
        if not hasattr(self, 'start_datetime'):
            self.start_datetime = datetime.now()
        
        if isinstance(self.start_datetime, int):
            self.start_datetime = datetime.fromtimestamp(self.start_datetime)


        current_datetime = self.start_datetime + timedelta(seconds=start_time_seconds)
        self.eeg_ax.set_title(f"EEG Data from {current_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        self.eeg_ax.set_ylabel("Channels")
        self.eeg_ax.set_xlabel("Time (s)")
        self.eeg_ax.grid(True)

        y_ticks = [i * 100 for i in range(len(self.eeg_data))]
        y_labels = [f'CH {i + 1}' for i in range(len(self.eeg_data))]
        self.eeg_ax.set_yticks(y_ticks)
        self.eeg_ax.set_yticklabels(y_labels)

        if (self.sampling_rate != 1): # if not bluetooth
            if not hasattr(self, 'time_slider'):
                slider_ax = self.eeg_fig.add_axes([0.25, 0.02, 0.5, 0.03], facecolor='lightgoldenrodyellow')

                max_time = (len(self.eeg_data[0]) / self.sampling_rate) - self.time_window
                self.time_slider = Slider(slider_ax, '', 0, max_time, valinit=0, valstep=self.time_window / 2)
                self.time_slider.on_changed(self.update_eeg_plot)

            if hasattr(self, 'time_slider'):
                max_time = (len(self.eeg_data[0]) / self.sampling_rate) - self.time_window
                self.time_slider.valmax = max_time

        self.eeg_canvas.draw()

    def on_click(self, event):
        if self.eeg_data is None or len(self.eeg_data) == 0:
            return

        if event.inaxes != self.eeg_ax:
            return

        click_x = event.xdata
        if click_x is None:
            return

        self.dragging = True

        if self.vline:
            self.vline.remove()

        self.vline = self.eeg_ax.axvline(x=click_x, color='r', linestyle='--')

        for annotation in self.annotations:
            annotation.remove()
        self.annotations.clear()

        for i, channel in enumerate(self.eeg_data):
            time_axis = np.linspace(0, self.time_window, self.num_samples_per_window)
            closest_index = np.argmin(np.abs(time_axis - click_x))
            amplitude = channel[self.start_index:self.start_index + self.num_samples_per_window][closest_index]
            y_pos = i * 100

            annotation = self.eeg_ax.annotate(f'{amplitude:.2f} μV', 
                                                    xy=(click_x, y_pos + amplitude), 
                                                    xytext=(self.eeg_ax.get_xlim()[1] * 1.015, y_pos + amplitude),  # Horizontal offset to the right of the line
                                                    textcoords='data',
                                                    fontsize=8,
                                                    color='black', 
                                                    ha='left',
                                                    va='center')
            self.annotations.append(annotation)

        self.eeg_canvas.draw()

    def on_mouse_move(self, event):
        if self.eeg_data is None or len(self.eeg_data) == 0:
            return

        if self.dragging and event.inaxes == self.eeg_ax:
            click_x = event.xdata
            if click_x is None:
                return

            if self.vline:
                self.vline.set_xdata([click_x, click_x])

                for annotation in self.annotations:
                    annotation.remove()
                self.annotations.clear()

                for i, channel in enumerate(self.eeg_data):
                    time_axis = np.linspace(0, self.time_window, self.num_samples_per_window)
                    closest_index = np.argmin(np.abs(time_axis - click_x))
                    amplitude = channel[self.start_index:self.start_index + self.num_samples_per_window][closest_index]
                    y_pos = i * 100

                    annotation = self.eeg_ax.annotate(f'{amplitude:.2f} μV', 
                                                     xy=(click_x, y_pos + amplitude), 
                                                     xytext=(self.eeg_ax.get_xlim()[1] * 1.015, y_pos + amplitude),  # Horizontal offset to the right of the line
                                                     textcoords='data',
                                                     fontsize=8,
                                                     color='black', 
                                                     ha='left',
                                                     va='center')
                    self.annotations.append(annotation)

                self.eeg_canvas.draw()

    def on_release(self, event):
        if self.eeg_data is None or len(self.eeg_data) == 0:
            return 

        if self.dragging:
            self.dragging = False
            self.eeg_canvas.draw()

    def shift_window(self, shift_seconds):
        self.start_index += shift_seconds
        self.start_index = max(0, min(self.start_index, len(self.eeg_data[0]) - self.num_samples_per_window))

        self.update_eeg_plot()

    def clear_plot(self):
        self.eeg_ax.cla() # Clear the plot
        self.eeg_canvas.draw()