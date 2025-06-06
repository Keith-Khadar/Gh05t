from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QCheckBox, QPushButton, QLabel, QComboBox, QHBoxLayout, QFileDialog, QMessageBox, QGroupBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import pyqtSignal, Qt, QSettings
import joblib
from scipy.signal import butter, filtfilt, sosfiltfilt, iirnotch, tf2sos, lfilter_zi, lfilter
import numpy as np
import time

class SignalProcessingWindow(QDialog):
    update_status_signal = pyqtSignal(str)
    apply_filter_signal = pyqtSignal(str, list, int)
    apply_model_signal = pyqtSignal(int)
    label_signal = pyqtSignal()

    def __init__(self, parent=None, rt=False):
        super().__init__(parent)
        self.setWindowTitle("Signal Processing")
        self.setGeometry(200, 200, 400, 350)

        layout = QVBoxLayout()

        filter_group = QGroupBox("Filter Settings")
        filter_group.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        filter_layout = QVBoxLayout()

        self.filter_label = QLabel("Select Filter Type and Frequency Range:")
        filter_layout.addWidget(self.filter_label)

        filter_row_layout = QHBoxLayout()

        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems(["None", "Low Pass", "High Pass", "Band Pass", "Notch"])
        self.filter_type_combo.setCursor(Qt.PointingHandCursor)
        self.filter_type_combo.setFixedWidth(150)
        self.filter_type_combo.setFixedHeight(25)
        self.filter_type_combo.setStyleSheet("background-color: #3498DB; selection-background-color: #2e88c5; selection-color: white; color: white;")
        filter_row_layout.addWidget(self.filter_type_combo)
        self.filter_type_combo.currentIndexChanged.connect(self.toggle_frequency_inputs)

        self.freq_label = QLabel("Threshold (Hz):")
        filter_row_layout.addWidget(self.freq_label)

        self.freq_min_input = QComboBox()
        self.freq_min_input.addItems([str(i) for i in range(5, 101, 5)])  
        self.freq_min_input.setFixedWidth(60)
        self.freq_min_input.setCursor(Qt.PointingHandCursor)
        self.freq_min_input.setStyleSheet("background-color: #3498DB; selection-background-color: #2e88c5; selection-color: white; color: white;")
        filter_row_layout.addWidget(self.freq_min_input)

        self.freq_max_input = QComboBox()
        self.freq_max_input.addItems([str(i) for i in range(5, 101, 5)])
        self.freq_max_input.setCursor(Qt.PointingHandCursor)  
        self.freq_max_input.setFixedWidth(60)
        self.freq_max_input.setStyleSheet("background-color: #3498DB; selection-background-color: #2e88c5; selection-color: white; color: white;")
        filter_row_layout.addWidget(self.freq_max_input)

        filter_layout.addLayout(filter_row_layout)

        spacer_1_layout = QHBoxLayout()
        spacer_1_layout.addSpacerItem(QSpacerItem(30, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.clear_filter_button = QPushButton("Clear Filter")
        self.clear_filter_button.setCursor(Qt.PointingHandCursor)
        self.clear_filter_button.setFixedWidth(150)
        self.clear_filter_button.setStyleSheet("background-color: #2C3E50; color: white;")
        self.clear_filter_button.clicked.connect(self.clear_filter)
        self.clear_filter_button.clicked.connect(self.save_settings)
        spacer_1_layout.addWidget(self.clear_filter_button)
        self.clear_filter_button.setVisible(False)

        self.apply_filter_button = QPushButton("Apply Filter")
        self.apply_filter_button.setCursor(Qt.PointingHandCursor)
        self.apply_filter_button.setFixedWidth(150)
        self.apply_filter_button.setStyleSheet("background-color: #2C3E50; color: white;")
        self.apply_filter_button.clicked.connect(self.apply_filter)
        self.apply_filter_button.clicked.connect(self.save_settings)
        spacer_1_layout.addWidget(self.apply_filter_button)

        filter_layout.addLayout(spacer_1_layout)
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        model_group = QGroupBox("Model Options")
        model_group.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        model_layout = QVBoxLayout()
        model_row_layout = QHBoxLayout()

        self.import_model_button = QPushButton("Import Pre-trained Model")
        self.import_model_button.setCursor(Qt.PointingHandCursor)
        self.import_model_button.setStyleSheet("background-color: #3498DB; selection-background-color: #2e88c5; selection-color: white; color: white;")
        self.import_model_button.clicked.connect(self.import_model)
        model_row_layout.addWidget(self.import_model_button)

        self.apply_ml_button = QPushButton("Apply Model")
        self.apply_ml_button.setCursor(Qt.PointingHandCursor)
        self.apply_ml_button.setFixedWidth(150)
        self.apply_ml_button.setStyleSheet("background-color: #2C3E50; color: white;")
        self.apply_ml_button.clicked.connect(self.apply_model)
        self.apply_ml_button.clicked.connect(self.save_settings)
        model_row_layout.addWidget(self.apply_ml_button)

        self.clear_model_button = QPushButton("Clear Model")
        self.clear_model_button.setCursor(Qt.PointingHandCursor)
        self.clear_model_button.setFixedWidth(150)
        self.clear_model_button.setStyleSheet("background-color: #2C3E50; color: white;")
        self.clear_model_button.clicked.connect(self.clear_model)
        self.clear_model_button.clicked.connect(self.save_settings)
        model_row_layout.addWidget(self.clear_model_button)
        self.clear_model_button.setVisible(False)

        self.use_default_model_checkbox = QCheckBox("Use Default Eye-Blink Model")
        self.use_default_model_checkbox.setChecked(False)
        self.use_default_model_checkbox.clicked.connect(self.save_settings)
        model_layout.addWidget(self.use_default_model_checkbox)

        self.no_model_label = QLabel("When labeling mode is enabled, cannot use a ML model.")
        self.no_model_label.setAlignment(Qt.AlignHCenter)
        self.no_model_label.setVisible(False)
        model_layout.addWidget(self.no_model_label)

        self.no_model_filein_label = QLabel("When using file input, cannot use a ML model.")
        self.no_model_filein_label.setAlignment(Qt.AlignHCenter)
        self.no_model_filein_label.setVisible(False)
        model_layout.addWidget(self.no_model_filein_label)

        model_layout.addLayout(model_row_layout)
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        labeling_group = QGroupBox("Labeling Mode")
        labeling_group.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        labeling_layout = QVBoxLayout()

        self.labeling_mode_checkbox = QCheckBox("Enable Labeling Mode")
        self.labeling_mode_checkbox.setChecked(False)
        self.labeling_mode_checkbox.stateChanged.connect(self.toggle_labeling_mode)
        self.labeling_mode_checkbox.clicked.connect(self.save_settings)
        labeling_layout.addWidget(self.labeling_mode_checkbox)

        self.status_label = QLabel("Status: Labeling Mode Disabled")
        self.status_label.setAlignment(Qt.AlignHCenter)
        labeling_layout.addWidget(self.status_label)

        self.label_instruc = QLabel("Press L to label with 1. Press T to toggle 1.")
        self.label_instruc.setAlignment(Qt.AlignHCenter)
        labeling_layout.addWidget(self.label_instruc)
        self.label_instruc.setVisible(False)

        labeling_group.setLayout(labeling_layout)
        layout.addWidget(labeling_group)

        self.setLayout(layout)

        self.filter_type = None
        self.freq_range = []
        self.model = "None"
        self.model_path = None
        self.labeling_mode = False
        self.original_data = None
        self.filtered_data = None
        self.butter_states = {}
        self.notch_states = {}

        self.model_buffer = []
        self.buffer_size = 500
        self.max_raw = 0

        self.alpha = 0.1
        self.alpha_delta = 0.1 # adaptive change
        self.delta_init = 1000 # threshold
        self.use_adaptive = False 

        self.weights = np.zeros(64)  # buffer weights

        self.t = 0
        self.eff_mean = [0.0] * 8
        self.eff_dc = [0.0] * 8
        self.delta_min = [self.delta_init] * 8
        self.delta_max = [self.delta_init] * 8

        # lms weight history
        self.w_lms_k = []

        self.load_settings()

        self.rt = rt
        if self.rt == False:
            self.labeling_mode_checkbox.setVisible(False)
            self.no_model_filein_label.setVisible(True)
            self.apply_ml_button.setVisible(False)
            self.import_model_button.setVisible(False)
            self.use_default_model_checkbox.setVisible(False)
            self.status_label.setText("Cannot enable labeling or import model in file input mode")

    def apply_filter(self):
        """Apply the selected filter to the data."""
        self.filter_type = self.filter_type_combo.currentText()
        freq_min = int(self.freq_min_input.currentText())
        freq_max = int(self.freq_max_input.currentText())
        self.freq_range = [freq_min, freq_max]

        self.clear_filter_button.setVisible(True)
        self.apply_filter_button.setVisible(False)

        if self.filter_type == "None":
            self.update_status_signal.emit("No filter applied.")
        elif self.filter_type == "Low Pass" or self.filter_type == "High Pass":
            self.apply_filter_signal.emit(self.filter_type, self.freq_range, 0)
            self.update_status_signal.emit(f"Applying {self.filter_type} filter with threshold {freq_min} Hz")
        elif self.filter_type == "Band Pass":
            self.apply_filter_signal.emit(self.filter_type, self.freq_range, 0)
            self.update_status_signal.emit(f"Applying {self.filter_type} filter with range {freq_min}-{freq_max} Hz")
        elif self.filter_type == "Notch":
            self.apply_filter_signal.emit(self.filter_type, self.freq_range, 0)
            self.update_status_signal.emit(f"Applying {self.filter_type} filter at {freq_min} Hz")

    def clear_filter(self):
        """Clear the applied filter."""
        self.filter_type = "None"
        self.freq_range = []
        self.filter_type_combo.setCurrentIndex(0)
        self.freq_min_input.setCurrentIndex(0)
        self.freq_max_input.setCurrentIndex(0)
        self.clear_filter_button.setVisible(False)
        self.apply_filter_signal.emit(self.filter_type, self.freq_range, 1)
        if hasattr(self, 'butter_states'):
            self.butter_states.clear()
        if hasattr(self, 'notch_states'):
            self.notch_states.clear()
        self.update_status_signal.emit("Filter cleared.")

    def butter_filter(self, data, fs, cutoff, btype, order=5, rt=0, channel=0):
        """Create a Butterworth filter and apply it to the data."""
        nyquist = 0.5 * fs
        if btype == "band":
            normal_cutoff = [c / nyquist for c in cutoff]
        else:
            normal_cutoff = cutoff[0] / nyquist
        if rt == 0:
            if btype == "band":
                normal_cutoff = [c / nyquist for c in cutoff]
                sos = butter(order, normal_cutoff, btype=btype, output='sos')
                y = sosfiltfilt(sos, data)
            else:
                b, a = butter(order, normal_cutoff, btype=btype, analog=False)
                y = filtfilt(b, a, data)
            self.filtered_data = y
        else:
            key = (tuple(cutoff), btype, order, channel)
            if key not in self.butter_states:
                b, a = butter(order, normal_cutoff, btype=btype)
                zi = lfilter_zi(b, a)
                self.butter_states[key] = {'b': b, 'a': a, 'zi': zi}

            b = self.butter_states[key]['b']
            a = self.butter_states[key]['a']
            zi = self.butter_states[key]['zi']

            # Remove scaling by data[0] (zi is already correct)
            y, zo = lfilter(b, a, data, zi=zi)
            self.butter_states[key]['zi'] = zo
        return y
    
    def notch_filter(self, data, freq, fs, Q=30, rt=0, channel=0):
        if rt == 0:
            notch_freq_hz = freq
            quality_factor = Q
            b_notch, a_notch = iirnotch(notch_freq_hz, quality_factor, fs)
            sos_notch = tf2sos(b_notch, a_notch)
            y = sosfiltfilt(sos_notch, data)
            self.filtered_data = y
        else:
            key = (freq, Q, channel)
            if key not in self.notch_states:
                b, a = iirnotch(freq, Q, fs)
                zi = lfilter_zi(b, a)
                self.notch_states[key] = {'b': b, 'a': a, 'zi': zi}

            b = self.notch_states[key]['b']
            a = self.notch_states[key]['a']
            zi = self.notch_states[key]['zi']
            y, zo = lfilter(b, a, data, zi=zi)
            self.notch_states[key]['zi'] = zo
        return y

    def toggle_frequency_inputs(self):
        filter_type = self.filter_type_combo.currentText()

        if filter_type in ["Low Pass", "High Pass", "Notch"]:
            self.freq_max_input.setVisible(False)
            self.freq_max_input.setCurrentIndex(0)
            if filter_type == "Notch":
                self.freq_label.setText("Frequency (Hz):")
        elif filter_type in ["Band Pass"]:
            self.freq_max_input.setVisible(True)
        else:
            self.freq_max_input.setVisible(False)
            self.freq_max_input.setCurrentIndex(0)

    def import_model(self):
        """Import a pre-trained model."""
        options = QFileDialog.Options()
        self.model_path, _ = QFileDialog.getOpenFileName(
            self, "Select Model File", "", "Model Files (*.pkl *.tflite *.onnx)", options=options
        )
        if self.model_path:
            try:
                self.update_status_signal.emit("Model imported successfully!")
            except Exception as e:
                self.update_status_signal.emit(f"Failed to load model: {str(e)}")

    def apply_model(self):
        self.apply_ml_button.setVisible(False)
        self.clear_model_button.setVisible(True)

        if self.model_path is None and not self.use_default_model_checkbox.isChecked():
            self.update_status_signal.emit("No model selected. Please import a model first.")
        elif self.use_default_model_checkbox.isChecked() and self.model_path is None:
            self.model = "default"
            self.apply_model_signal.emit(1)
            self.update_status_signal.emit("Default model applied successfully!")
        elif not self.use_default_model_checkbox.isChecked() and self.model_path:
            self.model ="import"
            try:
                self.model = joblib.load(self.model_path)
                self.update_status_signal.emit("Imported Model applied successfully!")
            except Exception as e:
                self.update_status_signal.emit(f"Failed to apply model: {str(e)}")
        elif self.model_path and self.use_default_model_checkbox.isChecked():
            self.model = "default"
            self.apply_model_signal.emit(1)
            self.update_status_signal.emit("Default model applied successfully!")

    def clear_model(self):
        self.model = None
        self.model_path = None
        self.apply_model_signal.emit(0)
        self.clear_model_button.setVisible(False)
        self.use_default_model_checkbox.setChecked(False)

        self.start_time_label = time.time()
        self.update_status_signal.emit("Model cleared.")

    def toggle_labeling_mode(self, state):
        """Enable or disable Labeling mode."""
        self.labeling_mode = state == Qt.Checked
        self.status_label.setText("Status: Labeling Mode Enabled" if self.labeling_mode else "Status: Labeling Mode Disabled")
        self.label_instruc.setVisible(self.labeling_mode)

        # self.no_model_label.setVisible(self.labeling_mode)
        # self.import_model_button.setVisible(not self.labeling_mode)
        # self.apply_ml_button.setVisible(not self.labeling_mode)
        # self.use_default_model_checkbox.setVisible(not self.labeling_mode)

        self.label_signal.emit()

    def load_settings(self):
        """Load saved settings using QSettings."""
        settings = QSettings("GH05T", "SignalProcessing")

        self.filter_type = settings.value("filter_type", "None")
        self.filter_type_combo.setCurrentText(self.filter_type)
        if self.filter_type != "None":
            self.clear_filter_button.setVisible(True)
            self.apply_filter_button.setVisible(False)

        min_freq = settings.value("freq_min", "0")
        self.freq_min_input.setCurrentText(min_freq)
        max_freq = settings.value("freq_max", "0")
        self.freq_max_input.setCurrentText(max_freq)
        self.freq_range = [int(min_freq), int(max_freq)]

        self.model = settings.value("model", "None")
        if self.model != "None":
            self.clear_model_button.setVisible(True)
            self.apply_ml_button.setVisible(False)
        self.model_path = settings.value("model_path", None)
        self.model_buffer = settings.value("model_buffer", [])

        self.labeling_mode = settings.value("labeling_mode", "False") == "True"
        self.labeling_mode_checkbox.setChecked(self.labeling_mode)
        self.no_model_label.setVisible(self.labeling_mode)
        self.label_instruc.setVisible(self.labeling_mode)
        
        self.import_model_button.setVisible(not self.labeling_mode)
        self.apply_ml_button.setVisible(not self.labeling_mode)
        self.use_default_model_checkbox.setVisible(not self.labeling_mode)

        self.filtered_data = settings.value("filtered_data", None)
        self.original_data = settings.value("original_data", None)
        self.max_raw = settings.value("max_raw", 0)

        # self.eff_dc = settings.value("eff_dc", [])
        # self.delta = settings.value("delta", [])

        self.butter_states = settings.value("butter_states", {})
        self.notch_states = settings.value("notch_states", {})

        self.rt = settings.value("rt", False)

        if self.filtered_data is not None:
            self.clear_filter_button.setVisible(True)
            self.apply_filter_button.setVisible(False)

    def save_settings(self):
        """Save current settings using QSettings."""
        settings = QSettings("GH05T", "SignalProcessing")

        settings.setValue("filter_type", self.filter_type_combo.currentText())
        settings.setValue("freq_min", self.freq_min_input.currentText())
        settings.setValue("freq_max", self.freq_max_input.currentText())
        settings.setValue("freq_range", self.freq_range)
        settings.setValue("model", self.model)
        settings.setValue("model_buffer", self.model_buffer)
        settings.setValue("model_path", self.model_path)
        settings.setValue("labeling_mode", str(self.labeling_mode_checkbox.isChecked()))
        settings.setValue("original_data", self.original_data)
        settings.setValue("filtered_data", self.filtered_data)
        settings.setValue("rt", self.rt)
        settings.setValue("butter_states", self.butter_states)
        settings.setValue("notch_states", self.notch_states)
        settings.setValue("max_raw", self.max_raw)
        
        # settings.setValue("eff_dc", self.eff_dc)
        # settings.setValue("delta", self.delta)

    # model for emg
    def detect_emg(self, raw_data, buffer, label=None, mode=None):
        """
        Process data through EMG detection pipeline with moving average
        Returns: (spikes, filtered_data)
        """
        spikes = [0] * 8
        measurements = [0] * 8

        # NLMS Implementation -- Second Stage of Training
        elapsed_time = time.time() - self.start_time_label
        # print(elapsed_time)
        if elapsed_time > 5:
            # tolerance to reset t to zero
            if 5.01 > elapsed_time > 5:
                self.t = 0
            #LMS implementation
            x_ref = np.random.normal(self.eff_mean, self.eff_std, 64)
            self.weights, x = self.apply_nlms_filter(x_ref, self.weights, buffer[-1], mu=0.99, eps=1e-6)

        for ch in range(8):
            x_sample = x[ch, 0]
            
            if self.use_adaptive:
                (self.eff_mean[ch], self.eff_dc[ch], self.delta_min[ch], self.delta_max[ch], self.t, measurements[ch], spikes[ch]) = self.apply_sded_dual(
                    x_sample, self.eff_mean[ch], self.eff_dc[ch], self.alpha[ch], self.delta_min[ch], self.delta_max[ch], self.t, 0, 1, 1, label, mode, 2, 19000)
            else:
                (self.eff_dc[ch], measurements[ch], 
                spikes[ch]) = self._apply_sded_fixed(
                    x_sample, self.eff_dc[ch], self.alpha, self.delta[ch]
                )

        return np.array(spikes), raw_data

    @staticmethod
    def _apply_sded_fixed(x, eff_dc, alpha, delta):
        """Fixed threshold version with moving average compensation"""
        meas = np.abs(x - eff_dc)
        alpha_red = alpha/2
        
        if meas > delta:
            new_eff_dc = alpha_red * (x + eff_dc) / 2 + (1 - alpha_red) * eff_dc
            if x > 5000:
                spike = 1
            else: spike = 0
        else:
            new_eff_dc = alpha * x + (1 - alpha) * eff_dc
            spike = 0
            
        return new_eff_dc, meas, spike

    @staticmethod
    def _apply_sded_adaptive(x, eff_dc, alpha_dc, alpha_delta, delta):
        """Adaptive threshold version with moving average compensation"""
        meas = np.abs(x - eff_dc)
        alpha_dc_red = alpha_dc/2
        alpha_delta_red = alpha_delta/2
        
        if meas > delta:
            new_delta = (alpha_delta_red * meas**2 + (1 - alpha_delta_red) * delta**2)**(1/2)
            if x > 5000:
                spike = 1
            else: spike = 0
            new_eff_dc = alpha_dc_red * (x + eff_dc)/2 + (1 - alpha_dc_red) * eff_dc
        else:
            new_delta = (alpha_delta * meas**2 + (1 - alpha_delta) * delta**2)**(1/2)
            spike = 0
            new_eff_dc = alpha_dc * x + (1 - alpha_dc) * eff_dc
            
        return new_eff_dc, new_delta, meas, spike

    def apply_nlms_filter(self, x_ref, w_lms_k, x_dsr, mu=None, eps=None):
        """
        Applies the NLMS filter to the input signal x_in.

        x_in: input signal (M x 1)
        w_lms_k: filter weights at time k (M x 1)
        y_noisy: noisy output signal (scalar)
        mu: learning rate
        eps: regularization parameter
        """
        if mu is None:
            raise ValueError("mu must be specified.")
        if eps is None:
            raise ValueError("eps must be specified.")
            
        y_hat = np.dot(w_lms_k, x_ref)
        e = x_dsr - y_hat
        x_pow  = np.dot(x_ref, x_ref)
        mu_eff = mu / (x_pow + eps)
        w_lms_k1 = w_lms_k + mu_eff * e * x_ref

        return w_lms_k1, e

    def apply_sded_dual(self,
        x,
        eff_mean,
        eff_std,
        alpha,
        delta_min,
        delta_max,
        t=0,
        gamma0_min=1,
        gamma0_max=1,
        desired=None,
        mode='adaptive',
        q=2,
        max_cap=19000
    ):
        """
        Single‐sample SDED with dual thresholds (min/max) and optional adaptation.

        Parameters
        ----------
        x : float
            Current signal sample.
        eff_mean : float
            Current mean estimate.
        eff_std : float
            Current standard deviation estimate.
        alpha : float
            Mean and standard deviation adaptation rate (0 < alpha_dc < 1).
        delta_min : float
            Current minimum deviation threshold.
        delta_max : float
            Current maximum deviation threshold.
        t : int
            Count of delta bound changes.
        gamma0_min : float
            Initial learning rate for delta_min (empirically set).
        gamma0_max : float
            Initial learning rate for delta_max (empirically set).
        desired : {0,1}, optional
            Ground‐truth label for this sample.  **Required** if mode='adaptive'.
        mode : {'static','adaptive'}, default='adaptive'
            If 'static', thresholds remain unchanged; if 'adaptive', they update on
            misclassifications.
        q : float, default=2
            Slowdown factor for DC learning on spikes (alpha_dc_red = alpha_dc/q).
        max_cap : float, default=19000
            Hard cap for delta_max.

        Returns
        -------
        new_eff_mean : float
            Updated mean estimate.
        new_eff_std : float
            Updated standard deviation estimate.
        new_delta_min : float
            Updated minimum threshold.
        new_delta_max : float
            Updated maximum threshold.
        new_t : int
            Updated count.
        meas : float
            |x – eff_dc| (the measured deviation).
        spike : {0,1}
            1 if deviation ∈ (delta_min, delta_max), else 0.
        """

        # 1) measure and classify
        meas = abs(x - eff_mean)
        spike = 1 if (meas > delta_min and meas < delta_max) else 0

        # 2) update mean and std estimate (slow down on spikes)
        alpha_eff = alpha / q if spike == 1 else alpha
        new_eff_mean = alpha_eff * x + (1 - alpha_eff) * eff_mean
        new_eff_std = (alpha_eff * meas**2 + (1 - alpha_eff) * eff_std**2)**(1/2)

        # 3) prepare thresholds (static by default)
        new_delta_min = delta_min
        new_delta_max = delta_max
        new_t = t

        # 4) adaptive‐mode threshold updates
        if mode == 'adaptive':
            if desired is None:
                raise ValueError("`desired` (0 or 1) must be provided in adaptive mode")

            # decayed learning‐rates
            gamma_min = gamma0_min / (1 + t)
            gamma_max = gamma0_max / (1 + t)

            # 4a) missed positive → expand the violated bound toward meas
            if desired == 1 and spike == 0:
                new_t +=1
                if meas <= delta_min:
                    new_delta_min = delta_min + gamma_min * (meas - delta_min)
                else:  # meas >= delta_max
                    new_delta_max = delta_max + gamma_max * (meas - delta_max)

            # 4b) false positive → shrink the nearer bound away from meas
            elif desired == 0 and spike == 1:
                new_t +=1
                if abs(delta_min - meas) < abs(delta_max - meas):
                    # meas closer to delta_min → raise delta_min
                    new_delta_min = delta_min + gamma_min * (meas - delta_min)
                else:
                    # meas closer to delta_max → lower delta_max
                    new_delta_max = delta_max + gamma_max * (meas - delta_max)

            # 5) clip to [0, max_cap] and sanity‐check band
            new_delta_min = max(0.0, new_delta_min)
            new_delta_max = min(max_cap, new_delta_max)

            # if adaptation would invert the band, revert to previous thresholds
            if new_delta_min >= new_delta_max:
                new_delta_min, new_delta_max = delta_min, delta_max

        return new_eff_mean, new_eff_std, new_delta_min, new_delta_max, new_t, meas, spike