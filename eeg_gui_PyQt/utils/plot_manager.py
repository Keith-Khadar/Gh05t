from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QSizePolicy
import numpy as np
import time
from matplotlib.collections import LineCollection
import matplotlib.animation as animation

class PlotManager:
    def __init__(self, window):
        """Initialize the PlotManager with the given window

        :param window: The parent window for the plot. 
        """
        self.window = window
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ax = self.figure.add_subplot(111)
        self.plot_type = "Time Series"

        self.x_window = []
        self.data = []
        self.data_rt = np.empty((8, 0)) 
        self.time = 0.0
        self.time_buffer = np.empty((0,))
        self.last_update_time = time.time()
        self.channel_names = ["Ch1", "Ch2", "Ch3", "Ch4", "Ch5", "Ch6", "Ch7", "Ch8"]
        self.current_index = 0

        self.animt = None
        self.animf = None
        self.animf_show = False
        self.offset = 0
        self.dt = 0
        self.n_plot = 2000
        self.sigbufs_plot = None
        self.buffer_filled = False

        self.figure.patch.set_alpha(0)
        self.canvas.setStyleSheet("background:#85a0bb;")
        self.ax.set_facecolor((0, 0, 0, 0))

        self.vertical_line = None
        self.annotations = []
        self.dragging = False

        self.current_marray = None
        self.current_t = None
        self.current_ticklocs = None

        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def stackplot(self, marray, seconds=None, start_time=None, ylabels=None, ax=None):
        """ Plot a stack of traces, where marray.shape = (numRows, numSamples).
        Each trace is offset vertically to avoid overlap. Used for file uploaded data.

        :param marray: 2D array of shape (numRows, numSamples) containing the data to plot.
        :param seconds: float representing the total duration of the data in seconds.
        :param start_time: float for the starting time of the plot.
        :param ylabels: list of labels for the y-axis.
        :param ax: matplotlib Axes object to plot on. If None, uses the default axis.
        """
        numRows, numSamples = marray.shape

        if seconds:
            t = seconds * np.arange(numSamples, dtype=float) / numSamples
            if start_time:
                t += start_time
            xlm = (start_time if start_time else 0, (start_time or 0) + seconds)
        else:
            t = np.arange(numSamples, dtype=float)
            xlm = (0, numSamples)

        offset_amount = 1.5 * np.max(np.abs(marray))
        ticklocs = np.arange(numRows) * offset_amount

        segs = [np.column_stack((t, marray[i, :] + ticklocs[i])) for i in range(numRows)]
        offsets = np.zeros((numRows, 2), dtype=float)

        if ax is None:
            ax = self.ax
        ax.clear()
        lines = LineCollection(segs, offsets=offsets, transOffset=None, colors='black')
        ax.add_collection(lines)

        self.vertical_line = ax.axvline(
            x=10, 
            color='r', 
            linestyle='--', 
            linewidth=1, 
            picker=10
        )

        self.current_marray = marray
        self.current_t = t
        self.current_ticklocs = ticklocs

        self.update_annotations(xlm[0], marray, t, ticklocs)

        ax.set_xlim(*xlm)
        ax.set_ylim(ticklocs[0] - offset_amount, ticklocs[-1] + offset_amount)

        ax.set_yticks(ticklocs)
        ax.set_yticklabels(ylabels or [f"Channel {i+1}" for i in range(numRows)])

        self.figure.patch.set_alpha(0)
        self.canvas.setStyleSheet("background:#85a0bb;")
        ax.set_facecolor((0, 0, 0, 0))

        ax.set_xlabel('Time (s)')
        if self.vertical_line is None:
            self.vertical_line = ax.axvline(x=10, color='r', linestyle='--', linewidth=1, picker=True)
            self.update_annotations(10, marray, t, ticklocs)

        self.canvas.draw()

    def real_time_stackplot(self, marray, seconds=None, ylabels=None, ax=None):
        """Plot a stack of traces in real-time with ADC values converted to a 200mV range.
        
        :param marray: 2D array of shape (numRows, numSamples) containing the data to plot.
        :param seconds: float representing the total duration of the data in seconds.
        :param ylabels: list of labels for the y-axis.
        :param ax: matplotlib Axes object to plot on. If None, uses the default axis.
        """
        numRows, numSamples = marray.shape
        max_window_size = 10

        if numSamples == 1:
            t = np.array([0, 1]) 
            marray = np.hstack((marray, marray))
        else:
            t = np.linspace(0, seconds, numSamples, dtype=float) if seconds else np.arange(numSamples, dtype=float)

        if not hasattr(self, 'x_window'):
            self.x_window = list(t)
        else:
            self.x_window.append(t[-1]) 

        window_start = self.x_window[0]
        window_end = self.x_window[-1]

        if window_end - window_start > max_window_size:
            window_start = window_end - max_window_size

        if window_end == window_start:
            window_end += 1

        adc_max_value = 16777215 # 5V
        adc_min_value = 0 # 0V
        marray_volt = (marray / adc_max_value) * 0.2

        offset_amount = 3 * 0.5
        ticklocs = np.arange(numRows) * offset_amount

        segs = [np.column_stack((t, marray_volt[i, :] + ticklocs[i])) for i in range(numRows)]
        offsets = np.zeros((numRows, 2), dtype=float)

        if ax is None:
            ax = self.ax

        ax.clear()
        lines = LineCollection(segs, offsets=offsets, transOffset=None, colors='black')
        ax.add_collection(lines)

        self.vertical_line = ax.axvline(
            x=1, 
            color='r', 
            linestyle='--', 
            linewidth=1, 
            picker=10
        )

        self.current_marray = marray_volt
        self.current_t = t
        self.current_ticklocs = ticklocs

        self.update_annotations(window_start, marray_volt, t, ticklocs)

        ax.set_xlim(window_start, window_end)
        ax.set_ylim(-offset_amount, ticklocs[-1] + offset_amount)

        ax.set_yticks(ticklocs)
        ax.set_yticklabels(ylabels or [f"Channel {i+1}" for i in range(numRows)])

        self.figure.patch.set_alpha(0)
        self.canvas.setStyleSheet("background:#85a0bb;")
        ax.set_facecolor((0, 0, 0, 0))

        ax.set_xlabel('Time (s)')

        if self.vertical_line is None:
            self.vertical_line = ax.axvline(x=window_start, color='r', linestyle='--', linewidth=1, picker=True)
            self.update_annotations(window_start, marray_volt, t, ticklocs)

        self.canvas.draw()

    def update_annotations(self, x, marray, t, ticklocs):
        """Update annotations for the vertical line.

        :param x: The x position for the vertical line.
        :param marray: 2D array of shape (numRows, numSamples) containing the data for annotations.
        :param t: 1D array of time values corresponding to the data.
        :param ticklocs: 1D array of y-axis tick locations.
        """
        for ann in self.annotations:
            ann.remove()
        self.annotations.clear()

        for i in range(marray.shape[0]):
            y_values = marray[i, :]
            idx = np.argmin(np.abs(t - x))
            signal_value = y_values[idx]
            
            y_annotation = signal_value + ticklocs[i]

            ann = self.ax.annotate(
                f"{signal_value:.2f}",
                xy=(x, y_annotation),
                xytext=(10, 0),
                textcoords='offset points',
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=1),
                fontsize=8
            )
            self.annotations.append(ann)

    def on_press(self, event):
        """Handle mouse press events."""
        if event.inaxes != self.ax or self.vertical_line is None:
            return
        if self.vertical_line.contains(event)[0]:
            self.dragging = True

    def on_release(self, event):
        """Handle mouse release events."""
        self.dragging = False

    def on_motion(self, event):
        """Handle mouse motion events."""
        if not self.dragging or event.inaxes != self.ax or self.vertical_line is None:
            return
        x = event.xdata
        self.vertical_line.set_xdata([x, x])
        self.update_annotations(x, self.current_marray, self.current_t, self.current_ticklocs)
        self.canvas.draw()

    def real_time_fft(self, marray, sampling_rate, ax=None):
        """Compute and plot the FFT of only the data currently shown in the windowed real-time plot,
        displaying only the frequency range 0-80 Hz.

        :param marray: 2D array of shape (numRows, numSamples) containing the data to compute the FFT.
        :param sampling_rate: Sampling rate of the data.
        :param ax: Matplotlib Axes object to plot on. If None, uses the default axis.
        """
        numRows, numSamples = marray.shape

        if numSamples == 1:
            return

        t = np.linspace(self.x_window[0], self.x_window[-1], numSamples, dtype=float)

        mask = (t >= self.x_window[0]) & (t <= self.x_window[-1])

        marray_windowed = marray[:, mask]
        numSamples_windowed = marray_windowed.shape[1]

        if numSamples_windowed < 2:
            return

        fft_freqs = np.fft.rfftfreq(numSamples_windowed, d=1/sampling_rate)
        fft_magnitude = np.abs(np.fft.rfft(marray_windowed, axis=1))

        freq_mask = fft_freqs <= 80
        fft_freqs = fft_freqs[freq_mask]
        fft_magnitude = fft_magnitude[:, freq_mask]

        if ax is None:
            ax = self.ax_fft

        ax.clear()
        for i in range(numRows):
            ax.plot(fft_freqs, fft_magnitude[i, :], label=f'Channel {i+1}')

        ax.set_xlim(0, 80)
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Magnitude')
        ax.legend()
        ax.grid(True)

        self.canvas.draw()

    def plot_data(self, data, time, channel_names=None, plot_type="Time Series"):
        """Plot data based on the plot type.
        
        :param data: 2D array of shape (numRows, numSamples) containing the data to plot.
        :param time: 1D array of time values corresponding to the data.
        :param channel_names: Optional list of channel names for the plot.
        :param plot_type: String specifying the type of plot ("Time Series", "FFT", or "Real Time Time Plot")."""
        self.ax.clear()
        self.data = data
        self.plot_type = plot_type
        self.time = time[-1]
        self.channel_names = channel_names

        if plot_type == "Time Series":
            if data.shape[0] > data.shape[1]:
                data = data.T
            self.n_plot = min(data.shape[1], 2000)
            self.stackplot(data[:, :self.n_plot], seconds=time[-1], ylabels=self.channel_names)
        elif plot_type == "FFT":
            self.plot_fft(data[:, :self.n_plot])
            self.animf_show = True
        elif plot_type == "Real Time Time Plot":
            self.real_time_stackplot(data,seconds=time[-1], ylabels=self.channel_names)
        self.canvas.draw()

    def plot_fft(self, data):
        """Plot FFT of the signals for file uploaded data.
        
        :param data: 2D array of shape (numRows, numSamples) containing the data to compute and plot the FFT."""
        numRows, numSamples = data.shape

        window = np.hamming(numSamples)
        data_windowed = data * window

        fft_data = np.fft.rfft(data_windowed, axis=1)
        fft_freq = np.fft.rfftfreq(numSamples, d=1/44100)

        mask = (fft_freq >= 0) & (fft_freq <= 80)
        fft_freq_filtered = fft_freq[mask]
        fft_data_filtered = np.abs(fft_data[:, mask])

        self.ax.clear()
        for i in range(numRows):
            self.ax.plot(fft_freq_filtered, fft_data_filtered[i, :], label=f'Channel {i+1}')

        self.ax.set_xlim(0, 80)
        self.ax.set_xlabel("Frequency (Hz)")
        self.ax.set_ylabel("Magnitude")
        self.ax.set_title("FFT (0-80 Hz)")
        self.ax.legend()

        self.ax.figure.canvas.draw()
        self.ax.figure.canvas.flush_events()

    def animate_time(self, frame):
        """Update the plot for each frame of the animation and display the current time for file uploaded data."""
        end_offset = self.offset + self.n_plot

        if end_offset > self.data.shape[1]:
            self.offset = 0
            end_offset = self.n_plot

        self.sigbufs_plot = self.data[:, self.offset:end_offset]
        self.offset += self.dt

        if self.vertical_line is None:
            self.vertical_line = self.ax.axvline(
                x=10,
                color='r', 
                linestyle='--', 
                linewidth=1, 
                picker=10
            )
        else:
            self.vertical_line.set_xdata([10, 10])

        self.stackplot(self.sigbufs_plot, ylabels=self.channel_names)

        self.canvas.draw()

    def animate_fft(self, frame):
        """Update the plot for each frame of the animation and display the current time for file uploaded data."""
        end_offset = self.offset + self.n_plot

        if end_offset > self.data.shape[1]:
            self.offset = 0
            end_offset = self.n_plot

        self.sigbufs_plot = self.data[:, self.offset:end_offset]
        self.offset += self.dt

        self.plot_fft(self.sigbufs_plot)

        self.canvas.draw()

    def play_time(self, data, channel_names, interval=200):
        """Start the animation with looping enabled.
        
        :param data: 2D array of shape (numRows, numSamples) containing the data to plot.
        :param channel_names: Optional list of channel names for the plot.
        :param itnerval: Integer specifying the interval between frames in milliseconds.
        """
        self.data = data
        self.channel_names = channel_names
        self.dt = int(data.shape[1] / 5)
        self.n_plot = min(data.shape[1], 2000)
        self.sigbufs_plot = np.zeros((data.shape[0], self.n_plot))
        self.offset = 0

        self.animt = animation.FuncAnimation(
            self.figure, self.animate_time, frames=range(0, data.shape[1], self.dt),
            interval=interval, repeat=True, cache_frame_data=False
        )
        self.canvas.draw()

    def play_fft(self, data, interval=200):
        """Start the animation with looping enabled.
        
        :param data: 2D array of shape (numRows, numSamples) containing the data to plot.
        :param itnerval: Integer specifying the interval between frames in milliseconds."""
        self.data = data
        self.dt = int(data.shape[1] / 5)
        self.n_plot = min(data.shape[1], 2000)
        self.sigbufs_plot = np.zeros((data.shape[0], self.n_plot))
        self.offset = 0

        self.animf = animation.FuncAnimation(
            self.figure, self.animate_fft, frames=range(0, data.shape[1], self.dt),
            interval=interval, repeat=True, cache_frame_data=False
        )
        self.canvas.draw()

    def stop_animation(self):
        """Stop the animation."""
        if self.animt is not None:
            self.animt.event_source.stop()
            self.animt = None

        if self.animf is not None and self.animf_show:
            self.animf.event_source.stop()
            self.animf = None

    def start_rt_animation(self):
        """Start the real-time animation for the fft and time series plots"""
        if self.animt is None:
            self.animt = animation.FuncAnimation(
                self.figure, 
                self.real_time_animate, 
                interval=100,
                blit=True,
                cache_frame_data=False
            )

        elif self.animf is None and self.animf_show:
            self.animf = animation.FuncAnimation(
                self.figure, 
                self.real_time_fft, 
                interval=100,
                blit=True,
                cache_frame_data=False
            )

    def real_time_animate(self, frame):
        """Update the plot for each frame of the animation."""
        if self.data_rt.size == 0:
            return []
        
        if self.data_rt.size > 0 and self.time_buffer.size > 0:
            if self.vertical_line is None:
                self.vertical_line = self.ax.axvline(
                    x=10,
                    color='r', 
                    linestyle='--', 
                    linewidth=1, 
                    picker=5
                )
            else:
                self.vertical_line.set_xdata([10, 10])

            self.real_time_stackplot(
                self.data_rt, 
                seconds=self.time_buffer[-1] - self.time_buffer[0],  
                ylabels=[f'Ch{i+1}' for i in range(self.data_rt.shape[0])],  
                ax=self.ax  
            )

        return self.ax.collections
    
    def handle_real_time_data(self, new_data, timestamp):
        """Handle incoming real-time data and update the data buffers.
        
        :param new_data: 1D array of shape (8,) containing the new data.
        :param timestamp: Integer representing the timestamp of the new data."""
        new_data = np.array(new_data).reshape((8, 1))

        adc_max_value = 16777215
        marray_volt = (new_data / adc_max_value) * 0.2
        print(marray_volt)

        timestamp = timestamp / 1000.0

        if self.data_rt.size == 0:
            self.data_rt = new_data
        else:
            self.data_rt = np.hstack((self.data_rt, new_data))

        if self.time_buffer.size == 0:
            self.time_buffer = np.array([timestamp])
        else:
            self.time_buffer = np.hstack((self.time_buffer, [timestamp]))

        if not self.buffer_filled and self.data_rt.shape[1] >= self.n_plot:
            self.buffer_filled = True
            print("Buffer filled!")

        if self.data_rt.shape[1] > self.n_plot:
            self.data_rt = self.data_rt[:, -self.n_plot:]
            self.time_buffer = self.time_buffer[-self.n_plot:]

        # self.canvas.draw_idle()
 
    def return_rt_data(self):
        """Return the real-time data and time buffer."""
        return self.data_rt, self.time_buffer