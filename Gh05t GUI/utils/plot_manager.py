from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QSizePolicy
import pyfftw
import numpy as np
import time
import mne
from mne.channels import make_dig_montage
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
        self.electrode_placements = ["Fp1", "Fp2", "O1", "O2", "F7", "F8", "T5", "T6"]

        self.current_index = 0

        self.animt = None
        self.animf = None
        self.animf_show = False
        self.anim_topography = None
        self.topo = False
        self.offset = 0
        self.dt = 0
        self.n_plot = 2000  # max data in data buffer
        self.sigbufs_plot = None

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
        self.sampling_rate = 250
        self.labeling_mode = False

        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def stackplot(self, marray, seconds=None, start_time=None, ylabels=None, ax=None, sampling_rate=250):
        """ Plot a stack of traces with dynamic scaling similar to real_time_stackplot. 
            marray is a complete dataset, converted and scaled into fixed lanes.
        """
        marray_mv = marray  # Assume data is already in mV or uV

        numRows, numSamples = marray_mv.shape

        if numSamples == 1:
            marray_mv = np.hstack((marray_mv, marray_mv))
            numSamples = 2
            if seconds:
                t = np.array([0.0, seconds], dtype=float)
                if start_time is not None:
                    t += start_time
                xlm = (0, numSamples / sampling_rate)
            else:
                t = (np.arange(numSamples, dtype=float) + self.offset) / sampling_rate
                xlm = (t[0], t[-1])
        else:
            if seconds:
                t = np.linspace(0, seconds, numSamples, dtype=float)
                if start_time is not None:
                    t += start_time
                xlm = (t[0], t[-1])
            else:
                t = (np.arange(numSamples, dtype=float) + self.offset) / sampling_rate
                xlm = (t[0], t[-1])

        data_range = np.max(marray_mv) - np.min(marray_mv)
        base_offset = data_range * 1.2
        lane_height = data_range
        ylim_padding = data_range * 0.1

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

        segs = [np.column_stack((t, scaled_data[i])) for i in range(numRows)]

        if ax is None:
            ax = self.ax
        ax.clear()

        lines = LineCollection(segs, colors='black')
        ax.add_collection(lines)

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

        if self.vertical_line is None:
            initial_x = np.mean(xlm)
            self.vertical_line = ax.axvline(x=initial_x, color='r', 
                                        linestyle='--', linewidth=0.5, picker=10)
        else:
            initial_x = self.vertical_line.get_xdata()[0]
            self.vertical_line.set_xdata([initial_x])

        y_min = -lane_height/2 - ylim_padding
        y_max = (numRows-1)*base_offset + lane_height/2 + ylim_padding
        ax.set_xlim(*xlm)
        ax.set_ylim(y_min, y_max)
        ax.set_yticks(ticklocs)
        ax.set_yticklabels(ylabels or [f"Channel {i+1}" for i in range(numRows)])
        ax.set_xlabel('Seconds')

        self.current_marray = marray_mv
        self.current_t = t
        self.current_ticklocs = ticklocs
        self.channel_scales = channel_scales
        self.channel_centers = channel_centers

        self.update_annotations(initial_x, marray_mv, t, ticklocs)

        self.figure.patch.set_alpha(0)
        self.canvas.setStyleSheet("background:#85a0bb;")
        ax.set_facecolor((0, 0, 0, 0))

        if self.web_socket:
            self.sampling_rate = 33
        else:
            self.sampling_rate = 250

        self.canvas.draw()

    def real_time_stackplot(self, marray, seconds=None, ylabels=None, ax=None):
        """Plot stacked traces with dynamic per-channel scaling in fixed lanes."""
        numRows, numSamples = marray.shape
        max_window_size = 1
        if numSamples == 1:
            t = np.array([0, 1])
            marray = np.hstack((marray, marray))
        else:
            t = np.array(self.time_buffer[-numSamples:])

        if not hasattr(self, 'x_window'):
            self.x_window = list(t)
        else:
            self.x_window.append(t[-1])

        if len(self.x_window) > max_window_size * self.sampling_rate:
            self.x_window = self.x_window[-int(max_window_size * self.sampling_rate):]

        window_start = self.x_window[0]
        window_end = self.x_window[-1]

        if window_end - window_start > max_window_size:
            window_start = window_end - max_window_size
        if window_end == window_start:
            window_end += 1

        # ADC to voltage conversion
        # if self.ble_reading:
        #     adc_max_value = 8388607  # 2^23 - 1 for signed 24-bit
        #     marray_volt = (marray / adc_max_value) * 5  # Convert to volts
        #     marray_mv = marray_volt * 1000  # Convert to millivolts
        # elif self.web_socket:
        #     adc_max_value = 4095  # 2^12 - 1 for unsigned 12-bit
        #     marray_volt = (marray / adc_max_value) * 5  # Convert to volts
        #     marray_mv = marray_volt * 1000  # Convert to millivolts
        marray_mv = marray

        # Auto-scaling parameters
        data_range = np.max(marray_mv) - np.min(marray_mv)
        base_offset = data_range * 1.2
        lane_height = data_range
        ylim_padding = data_range * 0.1
        
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
            ch_data = marray_mv[i]
            
            data_min = np.min(ch_data)
            data_max = np.max(ch_data)
            data_center = (data_max + data_min) / 2
            data_range = data_max - data_min

            if data_range == 0:
                data_range = 1
                    
            self.channel_scales[i] = lane_height / data_range
            self.channel_offsets[i] = i * base_offset
            self.channel_centers[i] = data_center
            
            scaled_data[i] = (ch_data - data_center) * self.channel_scales[i] + self.channel_offsets[i]
            
            ticklocs.append(i * base_offset)

        segs = [np.column_stack((t, scaled_data[i])) for i in range(numRows)]
        
        if ax is None:
            ax = self.ax
        ax.clear()

        # Plot the channel data
        lines = LineCollection(segs, colors='black')
        ax.add_collection(lines)

        if hasattr(self, 'label_buffer') and len(self.label_buffer) > 0 and self.labeling_mode:
            if len(self.label_buffer) != len(t):
                zeros_needed = len(t) - len(self.label_buffer)
                if zeros_needed > 0:
                    self.label_buffer = np.concatenate([
                        np.zeros(zeros_needed),
                        self.label_buffer
                    ])

            mask = (self.label_buffer == 1)
            label_row = numRows * base_offset
            ax.scatter(
                t[mask],
                np.full_like(t[mask], label_row),
                c='blue',
                marker='o',
                label='Labels'
            )

        for i in range(numRows):
            y_center = i * base_offset
            ax.axhspan(y_center - lane_height/2, 
                    y_center + lane_height/2, 
                    facecolor='#f0f0f0', alpha=0.2)
            
            range_half = lane_height/(2*self.channel_scales[i])
            ax.text(window_start + 0.1, y_center, 
                    f'±{range_half:.0f}',
                    va='center', ha='left', 
                    fontsize=7, color='#666666')

        if self.vertical_line is None:
            self.vertical_line = ax.axvline(x=new_x, color='r', 
                                        linestyle='--', linewidth=0.5, picker=10)
        else:
            self.vertical_line.set_xdata([new_x])

        self.vertical_line_x = new_x

        y_min = -lane_height/2 - ylim_padding
        if hasattr(self, 'label_buffer') and len(self.label_buffer) > 0 and self.labeling_mode:
            y_max = (numRows) * base_offset + lane_height/2 + ylim_padding
        else:
            y_max = (numRows-1)*base_offset + lane_height/2 + ylim_padding
        ax.set_xlim(window_start, window_end)
        ax.set_ylim(y_min, y_max)
        ax.set_yticks(ticklocs)

        if hasattr(self, 'label_buffer') and len(self.label_buffer) > 0 and self.labeling_mode:
            label_row = numRows * base_offset
            ax.axhspan(label_row - lane_height/2,
                    label_row + lane_height/2,
                    facecolor='#f0f0f0', alpha=0.2)
            ticklocs.append(label_row)
            yticklabels = [f"Channel {i+1}" for i in range(numRows)] + ["Labels"]
        else:
            yticklabels = [f"Channel {i+1}" for i in range(numRows)]

        ax.set_yticks(ticklocs)
        ax.set_yticklabels(yticklabels)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Scaled Voltage')

        self.current_marray = marray_mv
        self.current_t = t
        self.current_ticklocs = ticklocs
        self.channel_scales = self.channel_scales
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
        marray = marray[:8, :]
        if isinstance(marray, list):
            marray = np.array(marray)
        
        num_channels, num_samples = marray.shape

        # if self.ble_reading:
        #     adc_max_value = 8388607  # 2^23 - 1 for signed 24-bit
        #     marray_volt = (marray / adc_max_value) * 5  # Convert to volts
        #     marray = marray_volt * 1000  # Convert to millivolts
        # elif self.web_socket:
        #     adc_max_value = 4095  # 2^12 - 1 for unsigned 12-bit
        #     marray_volt = (marray / adc_max_value) * 5  # Convert to volts
        #     marray = marray_volt * 1000  # Convert to millivolts
        
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
            ax.set_ylim(0, 20)
        else:
            for i in range(magnitudes.shape[0]):
                ax.plot(freqs, magnitudes[i], label=self.channel_names[i])
            
            ax.set_xlim(0.1, 80)
            max_mag = np.max(magnitudes) if magnitudes.size > 0 else 1
            ax.set_ylim(0, 100)
            ax.grid(True)
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Magnitude (µV²/Hz)')
            ax.legend(loc='upper right')
            ax.set_title(f'Real-Time Spectrum ({num_samples/sampling_rate:.1f}s window)')

        self.canvas.draw()

    def initialize_topography(self, channel_names):
        """Initialize topography settings based on actual channel names"""
        clean_names = [name.replace('EEG ', '') for name in channel_names]
        
        available_electrodes = []
        available_indices = []
        standard_electrodes = ["Fp1", "Fp2", "O1", "O2", "F7", "F8", "T5", "T6", "T3", "T4", "F3", "F4", "P3", "P4", "Pz", "Fz", "Cz", "C3", "C4", "A1", "A2"]
        
        for i, name in enumerate(clean_names):
            if name in standard_electrodes:
                available_electrodes.append(name)
                available_indices.append(i)
    
        if not available_electrodes:
            print("Warning: No standard electrodes found for topography")
            return False
        
        self.info = mne.create_info(
            ch_names=available_electrodes,
            sfreq=self.sampling_rate,
            ch_types='eeg'
        )
        
        montage = mne.channels.make_standard_montage('standard_1020')
        
        self.info.set_montage(montage)
        
        self.topography_channels = {
            'indices': available_indices,
            'names': available_electrodes
        }
        
        return True
    
    def plot_topography(self, data, time):
        """Plot scalp topography using available channels"""
        if not hasattr(self, 'topography_channels'):
            print("Topography not initialized - call initialize_topography() first")
            return
        
        if data.size == 0 or data.shape[0] == 0:
            return

        self.ax.clear()
        
        if len(data.shape) != 2:
            print(f"Data must be 2D array, got shape {data.shape}")
            return
        
        if data.shape[0] > data.shape[1]:
            data = data.T
        
        try:
            # Verify channel indices are valid
            valid_indices = [i for i in self.topography_channels['indices'] if i < data.shape[0]]
            if not valid_indices:
                print(f"No valid channel indices in {self.topography_channels['indices']} for data shape {data.shape}")
                return
                
            data_subset = data[valid_indices, :]
        except IndexError as e:
            print(f"Channel index error: {e}")
            print(f"Data has {data.shape[0]} channels, trying to access {self.topography_channels['indices']}")
            return
        
        window_size = int(self.sampling_rate)
        
        if self.ble_reading or self.web_socket:
            # For real-time data, use most recent samples
            if data_subset.shape[1] == 0:
                print("No data available in real-time buffer")
                return
                
            window_start = max(0, data_subset.shape[1] - window_size)
            data_window = data_subset[:, window_start:]
        else:
            if self.vertical_line is not None and time is not None:
                current_time = self.vertical_line.get_xdata()[0]
                time_idx = np.argmin(np.abs(time - current_time))
                window_start = max(0, time_idx - window_size//2)
                window_end = min(data_subset.shape[1], time_idx + window_size//2)
                data_window = data_subset[:, window_start:window_end]
            else:
                data_window = data_subset[:, :min(window_size, data_subset.shape[1])]
        
        if data_window.size == 0:
            print("No data in selected window")
            return
        
        data_avg = np.mean(data_window, axis=1)
        
        try:
            if not hasattr(self, 'cbar'):
                im, _ = mne.viz.plot_topomap(
                    data_avg,
                    self.info,
                    axes=self.ax,
                    show=False,
                    contours=6,
                    res=64,
                    extrapolate='head',
                    sphere=(0, 0, 0, 0.095),
                    outlines='head'
                )
                self.cbar = self.figure.colorbar(im, ax=self.ax)
                self.cbar.set_label('µV')
                self.cbar_initialized = True
            else:
                mne.viz.plot_topomap(
                    data_avg,
                    self.info,
                    axes=self.ax,
                    show=False,
                    contours=6,
                    res=64,
                    extrapolate='head',
                    sphere=(0, 0, 0, 0.095),
                    outlines='head'
                )
            
            for collection in self.ax.collections:
                if hasattr(collection, '_sizes'):
                    collection._sizes = [10]
                    collection.set_color('k')
                    collection.set_linewidth(1)
            
            title = 'Real-Time Topography' if (self.ble_reading or self.web_socket) else 'Scalp Topography'
            self.ax.set_title(title)
            
            self.canvas.draw()
        except Exception as e:
            print(f"Topography plotting failed: {str(e)}")
            import traceback
            traceback.print_exc()

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
            self.electrode_placements = channel_names

        if plot_type == "Time Series":
            if data.shape[0] > data.shape[1]:
                data = data.T
            self.n_plot = min(data.shape[1], 2000)
            self.stackplot(data[:, :self.n_plot], seconds=time[-1], ylabels=self.channel_names, sampling_rate=self.sampling_rate)
        elif plot_type == "Polar FFT":
            if self.ble_reading or self.web_socket:
                self.real_time_fft(self.data_rt, sampling_rate=self.sampling_rate, polar=True)
                self.start_fft_animation()
            else:
                self.plot_fft(data[:, :self.n_plot], polar=True)
            self.animf_show = True
        elif plot_type == "FFT":
            if self.ble_reading or self.web_socket:
                self.real_time_fft(self.data_rt, sampling_rate=self.sampling_rate, polar=False)
                self.start_fft_animation()
            else:
                self.plot_fft(data[:, :self.n_plot], polar=False)
            self.animf_show = True
        elif plot_type == "Real Time Time Plot":
            self.real_time_stackplot(data,seconds=time[-1], ylabels=self.channel_names)
        elif plot_type == "Head Topography":
            if self.ble_reading or self.web_socket:
                self.initialize_topography(self.electrode_placements)
                self.plot_topography(self.data_rt, self.time_buffer)
                self.start_topo_animation()
            else:
                self.initialize_topography(channel_names)
                self.plot_topography(data, time)
            self.topo = True
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
        end_offset = self.offset + self.sampling_rate

        if end_offset > (self.data.shape[1]):
            self.offset = 0
            end_offset = self.n_plot

        self.sigbufs_plot = self.data[:, int(self.offset):int(end_offset)]
        self.offset += self.sampling_rate / 5

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

        self.stackplot(self.sigbufs_plot, ylabels=self.channel_names, start_time=self.offset / self.sampling_rate)

        self.canvas.draw()

    def animate_fft(self, frame):
        """Update the plot for each frame of the animation and display the current time for file uploaded data."""
        end_offset = self.offset + self.sampling_rate

        if end_offset > self.data.shape[1]:
            self.offset = 0
            end_offset = self.n_plot

        self.sigbufs_plot = self.data[:,int(self.offset):int(end_offset)]
        self.offset += self.sampling_rate / 5

        if self.plot_type == "Polar FFT":
            self.plot_fft(self.sigbufs_plot, polar=True)
        else: # Regular FFT
            self.plot_fft(self.sigbufs_plot, polar=False)

        self.canvas.draw()

    def animate_topography(self, frame):
        """Update the topography plot for each animation frame"""
        try:
            if not hasattr(self, 'data') or self.data.size == 0:
                return
            
            if not hasattr(self, 'animate_topography_frames'):
                return
                
            window_size = getattr(self, 'topography_window_size', int(self.sampling_rate))
            
            progress = min(frame / self.animate_topography_frames, 1.0)
            pos = int(progress * (self.data.shape[1] - window_size))
            window_start = pos
            window_end = min(pos + window_size, self.data.shape[1])
            
            time_window = None
            if hasattr(self, 'time_data') and isinstance(self.time_data, (np.ndarray, list)):
                if len(self.time_data) == self.data.shape[1]:
                    time_window = self.time_data[window_start:window_end]
            
            self.plot_topography(self.data[:, window_start:window_end], time_window)
            
            if hasattr(self, 'vertical_line') and self.vertical_line is not None:
                if time_window is not None and len(time_window) > 0:
                    center_time = (time_window[0] + time_window[-1]) / 2
                else:
                    center_time = (window_start + window_size/2)/self.sampling_rate
                self.vertical_line.set_xdata([center_time, center_time])
            
            self.canvas.draw_idle()
        except Exception as e:
            print(f"Error in topography animation frame {frame}: {str(e)}")

    def play_time(self, data, channel_names, interval=5):
        """Start the animation with looping enabled.
        
        :param data: 2D array of shape (numRows, numSamples) containing the data to plot.
        :param channel_names: Optional list of channel names for the plot.
        :param itnerval: Integer specifying the interval between frames in milliseconds.
        """
        self.data = data
        self.channel_names = channel_names
        self.dt = int(data.shape[1] / self.sampling_rate)
        self.n_plot = min(data.shape[1], 2000)
        self.sigbufs_plot = np.zeros((data.shape[0], self.n_plot))
        # self.offset = 0

        self.animt = animation.FuncAnimation(
            self.figure, self.animate_time, frames=range(0, data.shape[1], self.dt),
            interval=interval, repeat=True, cache_frame_data=False
        )
        self.canvas.draw()

    def play_fft(self, data, interval=5):
        """Start the animation with looping enabled.
        
        :param data: 2D array of shape (numRows, numSamples) containing the data to plot.
        :param itnerval: Integer specifying the interval between frames in milliseconds."""
        self.data = data
        self.dt = int(data.shape[1] / self.sampling_rate)
        self.n_plot = min(data.shape[1], 2000)
        self.sigbufs_plot = np.zeros((data.shape[0], self.n_plot))
        # self.offset = 0

        self.animf = animation.FuncAnimation(
            self.figure, self.animate_fft, frames=range(0, data.shape[1], self.dt),
            interval=interval, repeat=True, cache_frame_data=False
        )
        self.canvas.draw()

    def play_topography(self, data, interval=5):
        """Start the topography animation with proper time handling"""
        if not isinstance(data, np.ndarray) or data.size == 0:
            print("Error: Invalid data input for topography animation")
            return

        self.data = data
        
        window_size = int(self.sampling_rate)
        if data.shape[1] <= window_size:
            print("Error: Not enough data points for animation")
            return

        total_frames = data.shape[1] - window_size
        step_size = max(1, int(total_frames / 100))
        
        self.animate_topography_frames = total_frames
        self.topography_window_size = window_size

        try:
            interval = int(interval) if isinstance(interval, (int, float)) else 50
            interval = max(interval, 10)
        except (TypeError, ValueError):
            interval = 50

        try:
            self.anim_topography = animation.FuncAnimation(
                self.figure,
                self.animate_topography,
                frames=range(0, total_frames, step_size),
                interval=interval,
                repeat=True,
                blit=False,
                cache_frame_data=False
            )
            self.canvas.draw()
        except Exception as e:
            print(f"Error creating topography animation: {str(e)}")

    def stop_animation(self):
        """Stop the animation."""
        if self.animt is not None:
            self.animt.event_source.stop()
            self.animt = None

        if self.animf is not None and self.animf_show:
            self.animf.event_source.stop()
            self.animf = None

        if self.anim_topography is not None and self.topo:
            self.anim_topography.event_source.stop()
            self.anim_topography = None

    def start_rt_animation(self):
        """Start the real-time animation for the fft and time series plots"""
        if self.animt is None:
            self.animt = animation.FuncAnimation(
                self.figure, 
                self.real_time_animate, 
                interval=1,
                blit=True,
                cache_frame_data=False
            )

    def start_fft_animation(self):
        if self.animf is None:
            self.animf = animation.FuncAnimation(
                self.figure, 
                self.real_fft_animate, 
                interval=1,
                blit=True,
                cache_frame_data=False
            )

    def start_topo_animation(self):
        if self.anim_topography is None:
            self.anim_topography = animation.FuncAnimation(
                self.figure, 
                self.real_topo_animate, 
                interval=1,
                blit=False,
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
                seconds=self.time_buffer[-1],  
                ylabels=[f'Ch{i+1}' for i in range(self.data_rt.shape[0])],  
                ax=self.ax  
            )
        return self.ax.collections
    
    def real_fft_animate(self, frame):
        """Update the plot for each frame of the animation."""
        if self.data_rt.size == 0:
            return []
        
        window_samples = int(1 * self.sampling_rate)
        if self.data_rt.shape[1] > window_samples:
            fft_data = self.data_rt[:, -window_samples:]
        else:
            fft_data = self.data_rt

        if self.plot_type == "Polar FFT":
            if not hasattr(self, 'fft_ax'):
                self.setup_fft_plot(polar=True)
            self.real_time_fft(fft_data, sampling_rate=self.sampling_rate, polar=True, ax=self.fft_ax)
        else:
            if not hasattr(self, 'fft_ax'):
                self.setup_fft_plot(polar=False)
            self.real_time_fft(fft_data, sampling_rate=self.sampling_rate, polar=False, ax=self.fft_ax)

        return self.fft_ax.lines + self.fft_ax.collections
    
    def real_topo_animate(self, frame):
        """Update the plot for each frame of the animation."""
        if self.data_rt.size == 0:
            return []
        
        self.plot_topography(self.data_rt, self.time_buffer)

        return self.ax.collections
    
    def handle_real_time_data(self, new_data, timestamp):
        """Handle incoming real-time data and update the data buffers.
        
        :param new_data: 1D array of shape (8,) containing the new data.
        :param timestamp: Integer representing the timestamp of the new data."""
        new_data = np.array(new_data).reshape((-1, 1))

        has_label = new_data.shape[0] == 9
        if has_label:
            label = new_data[-1, 0]
            channel_data = new_data[:-1, :]
        else:
            label = None
            channel_data = new_data 

        timestamp_s = timestamp / 1000.0

        if self.data_rt.size == 0:
            self.data_rt = channel_data
        else:
            self.data_rt = np.hstack((self.data_rt, channel_data))[:, -self.n_plot:]

        if has_label:
            if not hasattr(self, 'label_buffer'):
                self.label_buffer = np.array([label])
            else:
                self.label_buffer = np.append(self.label_buffer, label)[-self.n_plot:]

        if self.time_buffer.size == 0:
            self.time_buffer = np.array([timestamp_s])
        else:
            self.time_buffer = np.append(self.time_buffer[-self.n_plot:], timestamp_s)

    def _frequency_to_theta(self, frequencies):
        """Convert frequencies to polar angles"""
        return (2 * np.pi * frequencies) / self.max_frequency

    def _theta_to_frequency(self, theta):
        """Convert polar angles to frequencies"""
        return (theta * self.max_frequency) / (2 * np.pi)
 
    def return_rt_data(self):
        """Return the real-time data and time buffer."""
        return self.data_rt, self.time_buffer