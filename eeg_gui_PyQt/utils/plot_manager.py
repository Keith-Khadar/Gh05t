from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QSizePolicy
import pyfftw
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

        self.ble_reading = False
        self.web_socket = False

        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def stackplot(self, marray, seconds=None, start_time=None, ylabels=None, ax=None, sampling_rate=None):
        """ Plot a stack of traces with dynamic scaling similar to real_time_stackplot. 
            marray is a complete dataset, converted and scaled into fixed lanes.
        """
        marray_mv = marray  # Assume data is already in mV or uV

        numRows, numSamples = marray_mv.shape

        # Handle single sample case by duplicating data
        if numSamples == 1:
            marray_mv = np.hstack((marray_mv, marray_mv))
            numSamples = 2
            if seconds:
                t = np.array([0.0, seconds], dtype=float)
                if start_time is not None:
                    t += start_time
                xlm = (t[0], t[-1])
            else:
                t = np.array([0.0, 1.0], dtype=float)
                xlm = (0, 1)
        else:
            # Time axis setup
            if seconds:
                t = np.linspace(0, seconds, numSamples, dtype=float)
                if start_time is not None:
                    t += start_time
                xlm = (t[0], t[-1])
            else:
                t = np.arange(numSamples, dtype=float)
                xlm = (0, numSamples - 1)

        # Auto-scaling parameters
        base_offset = 1000  # mV between channel baselines
        lane_height = 800   # mV vertical range per channel
        ylim_padding = 200  # mV padding at top/bottom

        scaled_data = np.zeros_like(marray_mv)
        ticklocs = []
        channel_scales = []
        channel_centers = []

        for i in range(numRows):
            ch_data = marray_mv[i]
            data_min = np.min(ch_data)
            data_max = np.max(ch_data)
            data_center = (data_min + data_max) / 2
            data_range = data_max - data_min

            if data_range == 0:
                data_range = 1  # Avoid division by zero

            scale = lane_height / data_range
            offset = i * base_offset

            scaled_data[i] = (ch_data - data_center) * scale + offset
            channel_scales.append(scale)
            channel_centers.append(data_center)
            ticklocs.append(offset)

        # Create line segments
        segs = [np.column_stack((t, scaled_data[i])) for i in range(numRows)]

        if ax is None:
            ax = self.ax
        ax.clear()

        # Plot data
        lines = LineCollection(segs, colors='black')
        ax.add_collection(lines)

        # Draw lane boundaries and labels
        for i in range(numRows):
            y_center = ticklocs[i]
            ax.axhspan(y_center - lane_height/2, 
                    y_center + lane_height/2, 
                    facecolor='#f0f0f0', alpha=0.2)
            
            range_half = lane_height / (2 * channel_scales[i])
            ax.text(xlm[0], y_center, 
                    f'±{range_half:.0f}',
                    va='center', ha='left', 
                    fontsize=7, color='#666666')

        # Vertical line initialization
        if self.vertical_line is None:
            initial_x = np.mean(xlm)  # Center of the time range
            self.vertical_line = ax.axvline(x=initial_x, color='r', 
                                        linestyle='--', linewidth=0.5, picker=10)
        else:
            initial_x = self.vertical_line.get_xdata()[0]
            self.vertical_line.set_xdata([initial_x])

        # Axis configuration
        y_min = -lane_height/2 - ylim_padding
        y_max = (numRows-1)*base_offset + lane_height/2 + ylim_padding
        ax.set_xlim(*xlm)
        ax.set_ylim(y_min, y_max)
        ax.set_yticks(ticklocs)
        ax.set_yticklabels(ylabels or [f"Channel {i+1}" for i in range(numRows)])
        ax.set_xlabel('Samples')

        # Store current state for annotations
        self.current_marray = marray_mv
        self.current_t = t
        self.current_ticklocs = ticklocs
        self.channel_scales = channel_scales
        self.channel_centers = channel_centers

        self.update_annotations(initial_x, marray_mv, t, ticklocs)

        # Style adjustments
        self.figure.patch.set_alpha(0)
        self.canvas.setStyleSheet("background:#85a0bb;")
        ax.set_facecolor((0, 0, 0, 0))

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
        if self.ble_reading:
            adc_max_value = 8388607  # 2^23 - 1 for signed 24-bit
            marray_volt = (marray / adc_max_value) * 5  # Convert to volts
            marray_mv = marray_volt * 1000  # Convert to millivolts
        elif self.web_socket:
            adc_max_value = 4095  # 2^12 - 1 for unsigned 12-bit
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
        for ann in self.annotations:
            ann.remove()
        self.annotations.clear()

        for i in range(marray.shape[0]):
            idx = np.argmin(np.abs(t - x))
            
            raw_value = marray[i, idx]

            scaled_y = ((raw_value - self.channel_centers[i]) * self.channel_scales[i]) + ticklocs[i]
            
            ann = self.ax.annotate(
                f"{raw_value:.1f}",
                xy=(x, scaled_y),
                xytext=(8, 0),
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

    def real_time_fft(self, marray, sampling_rate, polar=False, ax=None):
        """Compute and plot real-time FFT with proper axis handling"""
        if isinstance(marray, list):
            marray = np.array(marray)
        
        if marray.size == 0 or not isinstance(marray, np.ndarray):
            print("Invalid FFT input data.")
            return
        
        num_channels, num_samples = marray.shape
        
        if num_samples < 2:
            return
        
        try:
            data = marray.astype(np.float32)
            data -= np.mean(data, axis=1, keepdims=True)
            
            window = np.hamming(num_samples)
            windowed_data = data * window

            fft_data = np.fft.rfft(windowed_data, axis=1)
            freqs = np.fft.rfftfreq(num_samples, d=1/sampling_rate)
            
            freq_mask = (freqs >= 0.1) & (freqs <= 80)
            freqs = freqs[freq_mask]
            magnitudes = np.abs(fft_data[:, freq_mask]) / num_samples

            # Check if there are any frequencies left after masking
            if magnitudes.size == 0:
                print("No frequencies in the 0.1-80 Hz range. Adjust FFT parameters.")
                return

        except Exception as e:
            print(f"FFT error: {str(e)}")
            return

        ax = self.fft_ax if ax is None else ax
        ax.clear()
        
        if polar:
            theta = np.linspace(0, 2*np.pi, len(freqs))
            for i in range(magnitudes.shape[0]):
                ax.plot(theta, magnitudes[i], label=self.channel_names[i])
            ax.set_ylim(0, 7000)
        else:
            for i in range(magnitudes.shape[0]):
                ax.plot(freqs, magnitudes[i], label=self.channel_names[i])
            
            ax.set_xlim(0.1, 80)
            max_mag = np.max(magnitudes) if magnitudes.size > 0 else 1
            ax.set_ylim(0, 7000)
            ax.grid(True)
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Magnitude (µV²/Hz)')
            ax.legend(loc='upper right')
            ax.set_title(f'Real-Time Spectrum ({num_samples/sampling_rate:.1f}s window)')

        self.canvas.draw()

    def plot_data(self, data, time, channel_names=None, sampling_rate=0, plot_type="Time Series"):
        """Plot data based on the plot type.
        
        :param data: 2D array of shape (numRows, numSamples) containing the data to plot.
        :param time: 1D array of time values corresponding to the data or single timestamp (for real-time)
        :param channel_names: Optional list of channel names for the plot.
        :param plot_type: String specifying the type of plot ("Time Series", "FFT", or "Real Time Time Plot")."""
        self.ax.clear()
        self.data = data
        self.plot_type = plot_type
        self.sampling_rate = sampling_rate

        if not self.ble_reading:
            self.time = time
            self.channel_names = channel_names

        if plot_type == "Time Series":
            if data.shape[0] > data.shape[1]:
                data = data.T
            self.n_plot = min(data.shape[1], 2000)
            self.stackplot(data[:, :self.n_plot], seconds=time[-1], ylabels=self.channel_names, sampling_rate=self.sampling_rate)
        elif plot_type == "Polar FFT":
            if self.ble_reading or self.web_socket:
                self.real_time_fft(self.data_rt, sampling_rate=250, polar=True)
                self.start_fft_animation()
            else:
                self.plot_fft(data[:, :self.n_plot], polar=True)
            self.animf_show = True
        elif plot_type == "FFT":
            if self.ble_reading or self.web_socket:
                self.real_time_fft(self.data_rt, sampling_rate=250, polar=False)
                self.start_fft_animation()
            else:
                self.plot_fft(data[:, :self.n_plot], polar=False)
            self.animf_show = True
        elif plot_type == "Real Time Time Plot":
            self.real_time_stackplot(data,seconds=time[-1], ylabels=self.channel_names)
        self.canvas.draw()

    def setup_fft_plot(self, polar=False):
        """Initialize FFT plot"""
        self.figure.clear()
        if polar:
            self.fft_ax = self.figure.add_subplot(111, projection='polar')
            self.fft_ax.set_theta_zero_location('N')
            self.fft_ax.set_theta_direction(-1)
        else:
            self.fft_ax = self.figure.add_subplot(111)
            self.fft_ax.set_xlim(0, 80)
            self.fft_ax.grid(True)
    
    def plot_fft(self, data, polar=False):
        """Plot FFT with current settings"""
        if self.sampling_rate is None:
            raise ValueError("Sampling rate not set")
        
        # Remove DC offset and ensure float32 data type
        data = data.astype(np.float32)
        data = data - np.mean(data, axis=1, keepdims=True)

        window = np.hamming(data.shape[1])
        fft_data = np.fft.rfft(data * window, axis=1)
        freqs = np.fft.rfftfreq(data.shape[1], 1/self.sampling_rate)
        
        freq_mask = freqs <= 80
        freqs = freqs[freq_mask]
        magnitudes = np.abs(fft_data[:, freq_mask])

        self.setup_fft_plot(polar)
        
        if polar:
            theta = np.linspace(0, 2*np.pi, len(freqs))
            for i in range(magnitudes.shape[0]):
                self.fft_ax.plot(theta, magnitudes[i], label=self.channel_names[i])
            self.fft_ax.set_ylim(0, 8000)
        else:
            for i in range(magnitudes.shape[0]):
                self.fft_ax.plot(freqs, magnitudes[i], label=self.channel_names[i])
            
            # Configure axis limits
            self.fft_ax.set_xlim(0.1, 70) 
            self.fft_ax.set_ylim(0, 8000)
            self.fft_ax.grid(True)
            self.fft_ax.set_xlabel('Frequency (Hz)')
            self.fft_ax.set_ylabel('Magnitude (µV²/Hz)')
            self.fft_ax.legend()
            self.fft_ax.set_title('EEG Frequency Spectrum (0.1-70Hz)')
            
        self.canvas.draw()

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

        if self.plot_type == "Polar FFT":
            self.plot_fft(self.sigbufs_plot, polar=True)
        else: # Regular FFT
            self.plot_fft(self.sigbufs_plot, polar=False)

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

    def start_fft_animation(self):
        if self.animf is None:
            self.animf = animation.FuncAnimation(
                self.figure, 
                self.real_fft_animate, 
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
    
    def real_fft_animate(self, frame):
        """Update the plot for each frame of the animation."""
        if self.data_rt.size == 0:
            return []
        
        window_samples = int(10 * self.sampling_rate)  # 10-second window
        if self.data_rt.shape[1] > window_samples:
            fft_data = self.data_rt[:, -window_samples:]
        else:
            fft_data = self.data_rt

        if self.plot_type == "Polar FFT":
            if not hasattr(self, 'fft_ax'):
                self.setup_fft_plot(polar=True)
            self.real_time_fft(fft_data, sampling_rate=250, polar=True, ax=self.fft_ax)
        else: # Regular FFT
            if not hasattr(self, 'fft_ax'):
                self.setup_fft_plot(polar=False)
            self.real_time_fft(fft_data, sampling_rate=250, polar=False, ax=self.fft_ax)

        return self.fft_ax.lines + self.fft_ax.collections
    
    def handle_real_time_data(self, new_data, timestamp):
        """Handle incoming real-time data and update the data buffers.
        
        :param new_data: 1D array of shape (8,) containing the new data.
        :param timestamp: Integer representing the timestamp of the new data."""
        new_data = np.array(new_data).reshape((8, 1))
        if not self.ble_reading:
            self.ble_reading = True

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

    def _frequency_to_theta(self, frequencies):
        """Convert frequencies to polar angles"""
        return (2 * np.pi * frequencies) / self.max_frequency

    def _theta_to_frequency(self, theta):
        """Convert polar angles to frequencies"""
        return (theta * self.max_frequency) / (2 * np.pi)
 
    def return_rt_data(self):
        """Return the real-time data and time buffer."""
        return self.data_rt, self.time_buffer