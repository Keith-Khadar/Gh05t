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
        """Plot stacked traces with dynamic per-channel scaling in fixed lanes"""
        numRows, numSamples = marray.shape
        max_window_size = 10  # Seconds

        # Time axis setup
        if numSamples == 1:
            t = np.array([0, 1])
            marray = np.hstack((marray, marray))
        else:
            t = np.linspace(0, seconds, numSamples, dtype=float) if seconds else np.arange(numSamples, dtype=float)

        # Window management
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

        # ADC to voltage conversion
        adc_max_value = 8388607  # 2^23 - 1 for signed 24-bit
        marray_volt = (marray / adc_max_value) * 5  # Convert to volts
        marray_mv = marray_volt * 1000  # Convert to millivolts

        # Auto-scaling parameters
        base_offset = 1000  # mV between channel baselines
        lane_height = 800   # mV vertical range per channel
        ylim_padding = 200  # mV padding at top/bottom
        
        # Initialize scaling parameters if not exists
        if not hasattr(self, 'channel_scales'):
            self.channel_scales = [1.0] * numRows
            self.channel_offsets = [0.0] * numRows
            self.channel_centers = [0.0] * numRows

        if hasattr(self, 'vertical_line_x'):
            time_offset = self.vertical_line_x - window_end
            new_x = window_end + time_offset
        else:
            new_x = window_start

        scaled_data = np.zeros_like(marray_mv)
        ticklocs = []
        
        for i in range(numRows):
            # Get current channel data
            ch_data = marray_mv[i]
            
            # Calculate dynamic scaling parameters
            data_min = np.min(ch_data)
            data_max = np.max(ch_data)
            data_center = (data_max + data_min) / 2
            data_range = data_max - data_min
            
            # Prevent division by zero (initial case)
            if data_range == 0:
                data_range = 1
                
            # Calculate scaling parameters
            self.channel_scales[i] = lane_height / data_range
            self.channel_offsets[i] = i * base_offset
            self.channel_centers[i] = data_center
            
            # Scale and center data
            scaled_data[i] = (ch_data - data_center) * self.channel_scales[i] + self.channel_offsets[i]
            
            ticklocs.append(i * base_offset)

        # Create line segments
        segs = [np.column_stack((t, scaled_data[i])) for i in range(numRows)]
        
        if ax is None:
            ax = self.ax
        ax.clear()

        # Plot data
        lines = LineCollection(segs, colors='black')
        ax.add_collection(lines)

        # Draw lane boundaries
        for i in range(numRows):
            y_center = i * base_offset
            ax.axhspan(y_center - lane_height/2, 
                    y_center + lane_height/2, 
                    facecolor='#f0f0f0', alpha=0.2)
            
            # Add compact range label
            range_half = lane_height/(2*self.channel_scales[i])
            ax.text(window_start + 0.1, y_center, 
                    f'±{range_half:.0f}',
                    va='center', ha='left', 
                    fontsize=7, color='#666666')

        # Vertical line initialization
        if self.vertical_line is None:
            self.vertical_line = ax.axvline(x=new_x, color='r', 
                                        linestyle='--', linewidth=0.5, picker=10)
        else:
            self.vertical_line.set_xdata([new_x])

        # Store current position for next update
        self.vertical_line_x = new_x

        # Axis configuration
        y_min = -lane_height/2 - ylim_padding
        y_max = (numRows-1)*base_offset + lane_height/2 + ylim_padding
        ax.set_xlim(window_start, window_end)
        ax.set_ylim(y_min, y_max)
        ax.set_yticks(ticklocs)
        ax.set_yticklabels([f"Channel {i+1}" for i in range(numRows)])
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Scaled Voltage')

        # Store current data state
        self.current_marray = marray_mv  # Store original data for annotations
        self.current_t = t
        self.current_ticklocs = ticklocs
        self.channel_scales = self.channel_scales  # Make available for annotations
        self.channel_centers = self.channel_centers

        self.update_annotations(new_x, marray_mv, t, ticklocs)
        self.canvas.draw()

    def update_annotations(self, x, marray, t, ticklocs):
        """Update annotations while maintaining vertical line position"""
        # Remove old annotations
        for ann in self.annotations:
            ann.remove()
        self.annotations.clear()

        # Create new annotations
        for i in range(marray.shape[0]):
            # Find nearest time index
            idx = np.argmin(np.abs(t - x))
            
            # Get original voltage value
            raw_value = marray[i, idx]
            
            # Calculate position
            scaled_y = ((raw_value - self.channel_centers[i]) * self.channel_scales[i]) + ticklocs[i]
            
            # Create annotation
            ann = self.ax.annotate(
                f"{raw_value:.1f}",
                xy=(x, scaled_y),
                xytext=(8, 0),  # Reduced text offset
                textcoords='offset points',
                fontsize=8,
                color='red',
                bbox=dict(
                    boxstyle="round,pad=0.2",
                    fc="white",
                    ec="none",
                    alpha=0.9
                )
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
        """Handle mouse motion with persistent position tracking"""
        if not self.dragging or event.inaxes != self.ax or self.vertical_line is None:
            return
        
        # Store absolute position relative to window end
        x = event.xdata
        self.vertical_line_x = x
        self.vertical_line.set_xdata([x, x])
        
        # Update annotations with current data
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

        adc_max_value = 8388607
        marray_volt = (new_data / adc_max_value) * 5
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