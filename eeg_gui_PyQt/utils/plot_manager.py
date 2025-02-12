from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QProgressBar, QSizePolicy
import numpy as np
from matplotlib.collections import LineCollection
import matplotlib.animation as animation

class PlotManager:
    def __init__(self, window):
        self.window = window
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ax = self.figure.add_subplot(111)
        self.plot_type = "Time Series"

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)

        self.data = np.zeros((8, 0))  # Initialize with 8 channels and no data
        self.time = 0.0
        self.channel_names = ["Ch1", "Ch2", "Ch3", "Ch4", "Ch5", "Ch6", "Ch7", "Ch8"]

        self.anim = None
        self.offset = 0
        self.dt = 0
        self.n_plot = 2000  # Number of samples to display at a time
        self.sigbufs_plot = None

    def stackplot(self, marray, seconds=None, start_time=None, ylabels=None, ax=None):
        """
        Plot a stack of traces, where marray.shape = (numRows, numSamples).
        Each trace is offset vertically to avoid overlap.
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

        ax.set_xlim(*xlm)
        ax.set_ylim(ticklocs[0] - offset_amount, ticklocs[-1] + offset_amount)

        ax.set_yticks(ticklocs)
        ax.set_yticklabels(ylabels or [f"Channel {i+1}" for i in range(numRows)])

        self.figure.patch.set_alpha(0)
        self.canvas.setStyleSheet("background:#85a0bb;")
        ax.set_facecolor((0, 0, 0, 0))

        ax.set_xlabel('Time (s)')
        self.canvas.draw()

    def update_progress_bar(self):
        """Update the progress bar based on the animation frame."""
        progress = int((self.offset / self.data.shape[1]) * 100)
        self.progress_bar.setValue(progress)

    def plot_data(self, data, time, channel_names=None, plot_type="Time Series"):
        """Plot data based on the plot type."""
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
            freqs = np.fft.fftfreq(data.shape[1], d=1/250)
            fft_data = np.abs(np.fft.fft(data, axis=1))
            for i, channel in enumerate(fft_data):
                self.ax.plot(freqs, channel + i * 0.1, label=channel_names[i])
            self.ax.set_xlabel("Frequency (Hz)")
            self.ax.set_ylabel("Magnitude")
            self.ax.legend()
        self.canvas.draw()

    def plot_fft(self, data):
        """Plot FFT of the signals."""
        self.ax.clear()
        freq = np.fft.fftfreq(data.shape[1])
        fft_vals = np.fft.fft(data, axis=1)
        self.ax.plot(freq, np.abs(fft_vals.T))
        self.ax.set_title("FFT Plot")
        self.ax.set_xlabel("Frequency (Hz)")
        self.ax.set_ylabel("Magnitude")
        self.canvas.draw()

    def plot_topography(self, data):
        """Plot topographic map (Example, assuming 2D data)."""
        self.ax.clear()
        self.ax.imshow(data, aspect='auto', cmap='jet')
        self.ax.set_title("Topography")
        self.canvas.draw()

    def animate(self, frame):
        """Update the plot for each frame of the animation and display the current time."""
        end_offset = self.offset + self.n_plot

        if end_offset > self.data.shape[1]:
            self.offset = 0
            end_offset = self.n_plot

        self.sigbufs_plot = self.data[:, self.offset:end_offset]
        self.offset += self.dt

        self.stackplot(self.sigbufs_plot, ylabels=self.channel_names)

        current_time = (self.offset / self.data.shape[1]) * self.time
        total_time = self.time

        self.ax.set_title(f"Time: {current_time:.2f} s / {total_time:.2f} s")

        self.update_progress_bar()
        self.canvas.draw()

    def play_data(self, data, channel_names, interval=200):
        """Start the animation with looping enabled."""
        self.data = data
        self.channel_names = channel_names
        self.dt = int(data.shape[1] / 5)
        self.n_plot = min(data.shape[1], 2000)
        self.sigbufs_plot = np.zeros((data.shape[0], self.n_plot))
        self.offset = 0

        self.anim = animation.FuncAnimation(
            self.figure, self.animate, frames=range(0, data.shape[1], self.dt),
            interval=interval, repeat=True, cache_frame_data=False
        )
        self.canvas.draw()

    def stop_animation(self):
        """Stop the animation."""
        if self.anim:
            self.anim.event_source.stop()
            self.anim = None
            print("Animation stopped.")

    def handle_real_time_data(self, new_data, timestamp):
        """Handle incoming real-time data and update the plot dynamically."""
        print(f"New data shape: {new_data.shape}")
        if self.data.size == 0:
            self.data = new_data
        else:
            self.data = np.hstack((self.data, new_data))

        if self.data.shape[1] > self.n_plot:
            self.data = self.data[:, -self.n_plot:]

        if self.time_buffer.size == 0:
            self.time_buffer = np.array([timestamp])
        else:
            self.time_buffer = np.hstack((self.time_buffer, timestamp))

        if self.time_buffer.size > self.n_plot:
            self.time_buffer = self.time_buffer[-self.n_plot:]

        time_window = self.time_buffer[-1] - self.time_buffer[0] if self.time_buffer.size > 1 else 0

        self.stackplot(self.data, seconds=time_window, ylabels=self.channel_names)
        self.canvas.draw()
        self.canvas.flush_events()