from PyQt5.QtWidgets import QVBoxLayout, QGridLayout, QWidget, QProgressBar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from matplotlib.collections import LineCollection
import matplotlib.animation as animation
from utils.grid_manager import GridManager

class PlotManager:
    def __init__(self, window):
        self.window = window

        self.grid_layout = QGridLayout()
        self.window.setLayout(self.grid_layout)

        self.plots = {}

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        self.data = None
        self.plot_type = "time"
        self.title = self.ax.set_title("")
        self.anim = None
        self.offset = 0
        self.dt = 0
        self.n_plot = 0
        self.sigbufs_plot = None
        self.channel_names = []

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.window.setLayout(layout)

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
        self.window.addWidget(self.canvas)
        self.window.setCurrentWidget(self.canvas)

    def update_progress_bar(self):
        """Update the progress bar based on the animation frame."""
        progress = int((self.offset / self.data.shape[1]) * 100)
        self.progress_bar.setValue(progress)

    def plot_data(self, data, time, channel_names=None, plot_type="Time Series"):
        """Handles different types of plots."""
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
            self.plot_fft(data)
        elif plot_type == "Topography":
            self.plot_topography(data)

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

    def update_grid_layout(self):
        """Rearrange plots in grid layout."""
        row, col = 1, 0
        for plot_type, (_, canvas, _) in self.plots.items():
            self.grid_layout.addWidget(canvas, row, col)
            col += 1
            if col >= 2:
                row += 1
                col = 0

        self.window.setLayout(self.grid_layout)

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
