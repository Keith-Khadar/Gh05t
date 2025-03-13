import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, 
    QStatusBar, QMenu, QAction, QGridLayout, QSplitter
)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QColor, QPalette, QFontDatabase
import numpy as np
from utils import PlotManager, EEGWebSocket, load_file, BLEWorker, SignalProcessingWindow, FileHandler

class MainWindow(QMainWindow):
    def __init__(self):
        '''Initialize the main window of the GUI'''
        super().__init__()

        self.setWindowTitle("EEG Data Visualizer")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)

        font_id = QFontDatabase.addApplicationFont("resources\FuturisticYourself.ttf")
        if font_id == -1:
            print("Failed to load font.")
        else:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        QApplication.setPalette(dark_palette)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        row1 = QHBoxLayout()
        row1.setContentsMargins(10, 0, 10, 0)
        row1_widget = QWidget()
        row1_widget.setLayout(row1)
        row1_widget.setStyleSheet("background-color: #1E2A38;")
        row1_widget.setFixedHeight(35)

        self.data_input_button = QPushButton("Data Input")
        self.data_input_button.setCursor(Qt.PointingHandCursor)
        self.data_input_button.setFixedWidth(150)
        self.data_input_button.setFixedHeight(25)
        self.data_input_button.setStyleSheet("color: white; background-color: #2C3E50;")

        self.data_input_menu = QMenu(self)
        self.data_input_menu.setCursor(Qt.PointingHandCursor)
        self.file_input_action = QAction("File Input", self)
        self.data_input_menu.addAction(self.file_input_action)

        self.real_time_input_menu = QMenu("Real-Time Input", self)

        self.ble_action = QAction("BLE (ADS1299 PCB)", self)
        self.websocket_action = QAction("WebSocket (Low Cost)", self)
        self.real_time_input_menu.addAction(self.ble_action)
        self.real_time_input_menu.addAction(self.websocket_action)

        self.data_input_menu.addMenu(self.real_time_input_menu)
        self.file_input_action.triggered.connect(self.handle_file_input)
        self.ble_action.triggered.connect(self.handle_real_time_ble_input)
        self.websocket_action.triggered.connect(self.websocket_input)

        self.data_input_button.setMenu(self.data_input_menu)

        title_layout = QHBoxLayout()

        custom_font = QFont(font_family, 23)
        self.title_label = QLabel("GH05T EEG")
        self.title_label.setCursor(Qt.PointingHandCursor)
        self.title_label.setFont(custom_font)
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.title_label.mousePressEvent = self.reset_application

        title_layout.addWidget(self.title_label)
        title_layout.addStretch(1)

        row1.addWidget(self.data_input_button)
        row1.addStretch(1)
        row1.addLayout(title_layout)

        main_layout.addWidget(row1_widget)

        row2 = QHBoxLayout()
        row2.setContentsMargins(10, 0, 10, 0)
        row2_widget = QWidget()
        row2_widget.setLayout(row2)
        row2_widget.setStyleSheet("background-color: #2C3E50;")
        row2_widget.setVisible(False)
        row2_widget.setFixedHeight(35)

        self.play_button = QPushButton("Start Data Stream")
        self.play_button.setCursor(Qt.PointingHandCursor)
        self.play_button.setFixedWidth(150)
        self.play_button.setFixedHeight(25)
        self.play_button.setStyleSheet("color: white; background-color: #3498DB;")
        self.play_button.clicked.connect(self.play_data_stream)

        row2.addWidget(self.play_button)

        self.export_button = QPushButton("Export Data")
        self.export_button.setCursor(Qt.PointingHandCursor)
        self.export_button.setFixedWidth(150)
        self.export_button.setFixedHeight(25)
        self.export_button.setStyleSheet("color: white; background-color: #3498DB;")
        self.export_button.clicked.connect(self.export_data_to_file)

        self.signal_processing = QPushButton("Signal Processing")
        self.signal_processing.setCursor(Qt.PointingHandCursor)
        self.signal_processing.setFixedWidth(150)
        self.signal_processing.setFixedHeight(25)
        self.signal_processing.setStyleSheet("color: white; background-color: #3498DB;")
        self.signal_processing.clicked.connect(self.open_signal_processing_window)

        row2.addWidget(self.export_button)
        row2.addWidget(self.signal_processing)
        row2.addStretch(1)

        self.active_plots = {}
        self.plot_actions = {}

        self.add_plot_button = QPushButton("Add/Remove Plots")
        self.add_plot_button.setCursor(Qt.PointingHandCursor)
        self.add_plot_button.setFixedWidth(150)
        self.add_plot_button.setFixedHeight(25)
        self.add_plot_button.setStyleSheet("color: white; background-color: #3498DB;")
        self.add_plot_menu = QMenu(self)
        self.add_plot_menu.setCursor(Qt.PointingHandCursor)

        plot_types = ["Time Series", "Polar FFT", "FFT"]
        for plot_type in plot_types:
            action = QAction(plot_type, self)
            action.setCheckable(True)
            action.toggled.connect(lambda checked, pt=plot_type: self.toggle_plot(pt, checked))
            self.plot_actions[plot_type] = action
            self.add_plot_menu.addAction(action)
            self.add_plot_menu.setStyleSheet("""QMenu::indicator:checked {
                                                    background-color: #3498DB;
                                                    border: 1px solid #3498DB;
                                                    border-radius: 3px;
                                                    width: 12px;
                                                    height: 12px;
                                                }
                                                
                                                QMenu::indicator:checked:disabled {
                                                    background-color: #666666;
                                                }
                                                
                                                QMenu::indicator:unchecked {
                                                    background-color: transparent;
                                                    border: 1px solid #5d5b59;
                                                    border-radius: 3px;
                                                    width: 12px;
                                                    height: 12px;
                                                }""")

        self.add_plot_button.setMenu(self.add_plot_menu)
        row2.addWidget(self.add_plot_button)

        main_layout.addWidget(row2_widget)
        self.row2_widget = row2_widget

        self.row3 = QSplitter()
        self.row3_widget = QWidget()
        self.row3_layout = QGridLayout(self.row3_widget)
        self.row3_widget.setStyleSheet("background-color: #34495E;")

        welcome_layout = QHBoxLayout()

        icon_label = QLabel()
        pixmap = QPixmap("resources\Icon.png").scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(pixmap)

        self.welcome_label = QLabel(
            "<br><br><br>"
            "<span style='font-size: 24px; color: #1E2A38;'>Welcome to GH05T EEG Visualizer!</span><br><br>"
            "This GUI is designed to help you visualize EEG data and connect to Bluetooth/Wifi devices.<br>"
            "You can upload your EEG data files or pair the app with a compatible Bluetooth/Wifi device.<br><br>"
            "Instructions:<br>"
            "- Use the 'Data Input' dropdown in the top bar to upload data or connect a Bluetooth device.<br><br>"
            "Click the link below to view the source code and report any issues!<br>"
            "Github Repository: <a href='https://github.com/Keith-Khadar/Gh05t' style='color: #1E2A38; font-weight:bold;'> https://github.com/Keith-Khadar/Gh05t</a>"
        )
        self.welcome_label.setAlignment(Qt.AlignLeft)
        self.welcome_label.setStyleSheet("color: #1E2A38; font-size: 16px; font-weight:bold;")
        self.welcome_label.setTextFormat(Qt.RichText)
        self.welcome_label.setWordWrap(True)
        self.welcome_label.setOpenExternalLinks(True)

        welcome_layout.addStretch(1)
        welcome_layout.addWidget(icon_label)
        welcome_layout.addWidget(self.welcome_label)
        welcome_layout.addStretch(1)
        
        self.welcome_widget = QWidget()
        self.welcome_widget.setLayout(welcome_layout)

        self.row3_layout.setRowStretch(0, 1)
        self.row3_layout.addWidget(self.welcome_widget, 1, 0, alignment=Qt.AlignCenter)
        self.row3_layout.setRowStretch(2, 1)

        self.row3_layout.addWidget(self.row3)
        self.row3_widget.setLayout(self.row3_layout)

        main_layout.addWidget(self.row3_widget)

        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("background-color: #1E2A38; color: white;")
        self.setStatusBar(self.status_bar)
        self.animation_index = 0
        self.status_bar.showMessage("Waiting for data input...")
        self.status_bar.setFixedHeight(30)

        self.animation_timer = QTimer(self)

        self.data_loaded = False
        self.ble_reading = False
        self.websocket_reading = False
        self.play_animation = False
        self.play_rt_animation = False
        self.paused_rt = False
        self.fft_rt = False
        self.polar = False

        self.plot_manager = PlotManager(self.row3)
        self.file_handler = FileHandler()

        self.channel_names = ["Ch1", "Ch2", "Ch3", "Ch4", "Ch5", "Ch6", "Ch7", "Ch8"]
        self.sampling_rate = 0
        self.data = np.empty((0, 3))
        self.time = np.empty((0, 1))

# ------------------- HANDLE DATA INPUT TYPE ------------------- #
    def mousePressEvent(self, event):
        """Handle title label click event"""
        if event.button() == Qt.LeftButton:
            if self.title_label.underMouse():
                self.reset_application(event)
        super().mousePressEvent(event)

    def handle_file_input(self):
        '''Opens a file dialog to upload data from a file.'''
        if self.ble_reading:
            self.ble_worker.disconnect()

        file_path, _ = QFileDialog.getOpenFileName(self, "Select EDF File", "", "EDF Files (*.edf);;All Files (*)")
        if file_path:
            self.row2_widget.setVisible(True)
            self.statusBar().showMessage(f"Selected file: {file_path}")
            self.data, self.time, self.channel_names, self.sampling_rate = load_file(file_path)
            self.plot_manager.sampling_rate = self.sampling_rate

            self.clear_layout(self.row3_layout)
            self.data_loaded = True

    def websocket_input(self):
        '''Connects to Websocket port.'''
        if self.ble_reading:
            self.ble_worker.disconnect()

        if not hasattr(self, 'web_socket'):
            self.clear_layout(self.row3_layout)

            self.real_time = PlotManager(self.row3)
            self.real_time.web_socket = True
            self.row3_layout.addWidget(self.real_time.canvas)
            row_splitter = QSplitter(Qt.Horizontal)
            row_splitter.addWidget(self.real_time.canvas)
            self.row3.addWidget(row_splitter)

            self.status_bar.showMessage("Connecting to Web Port...")
            self.websocket = EEGWebSocket()
            self.websocket.data_received.connect(self.handle_real_time)
            self.websocket.start()

            self.websocket.status_update_signal.connect(self.update_status_bar)
            self.websocket.connection_failed_signal.connect(self.handle_connection_failed)

            self.websocket_reading = True
            self.row2_widget.setVisible(True)

    def handle_real_time_ble_input(self):
        """Initialize BLE connection and start real-time data handling."""
        if not hasattr(self, 'ble_worker'):
            self.clear_layout(self.row3_layout)
            
            self.real_time = PlotManager(self.row3)
            self.real_time.ble_reading = True
            self.row3_layout.addWidget(self.real_time.canvas)
            row_splitter = QSplitter(Qt.Horizontal)
            row_splitter.addWidget(self.real_time.canvas)
            self.row3.addWidget(row_splitter)

            self.real_fft = PlotManager(self.row3)
                
            self.status_bar.showMessage("Connecting to BLE device...")
            self.ble_worker = BLEWorker()
            self.ble_worker.data_received.connect(self.handle_real_time)
            self.ble_worker.start()

            self.ble_worker.status_update_signal.connect(self.update_status_bar)
            self.ble_worker.connection_failed_signal.connect(self.handle_connection_failed)
        
            self.ble_reading = True
            self.row2_widget.setVisible(True)

            if "Time Series" in self.plot_actions:
                self.plot_actions["Time Series"].setVisible(not self.ble_reading)
        
            if "FFT" in self.plot_actions:
                self.plot_actions["FFT"].setVisible(True)
            if "Polar FFT" in self.plot_actions:
                self.plot_actions["Polar FFT"].setVisible(True)
    
    def handle_connection_failed(self):
        """Handle connection failure and update the ble_reading status."""
        self.ble_reading = False

    def update_status_bar(self, message):
        """Update the status bar with the given message.
        
        :param message: The message to display in the status bar."""
        self.statusBar().showMessage(message)

# ------------------- HANDLE REAL TIME INCOMING DATA ------------------- #
    def handle_real_time(self, timestamp, data):
        """Process incoming BLE data and update the plot.
        
        :param ble_timestamp: The timestamp of the incoming data.
        :param ble_data: The incoming data."""
        if data is None:
            return
    
        self.data = data
        self.time = timestamp

        new_data = np.array(data).reshape((8, 1))
        timestamp_s = timestamp / 1000.0

        self.file_handler.add_data(timestamp, new_data.flatten())

        self.real_time.handle_real_time_data(data, timestamp)
        for plot_type in list(self.active_plots.keys()):
            real_fft, splitter = self.active_plots[plot_type]
            real_fft.handle_real_time_data(data, timestamp)

        if not self.play_rt_animation and not self.paused_rt:
            print("Starting real-time animation...")
            self.statusBar().showMessage("Starting Real Time Animation Plot")
            self.play_button.setText("Stop Data Stream")
            self.play_rt_animation = True
            self.real_time.start_rt_animation()

    def play_data_stream(self):
        """Start the animation for all applicable plots."""
        if len(self.active_plots) == 0 and not self.ble_reading:
            self.statusBar().showMessage("No plots to animate!")
            return

        if self.data_loaded and not self.play_animation:
            self.statusBar().showMessage("Playing data stream...")
            for plot_mgr, _ in self.active_plots.values():
                if plot_mgr.plot_type == "Time Series":
                    plot_mgr.play_time(self.data, self.channel_names)
                elif plot_mgr.plot_type == "Polar FFT":
                    plot_mgr.play_fft(self.data)
                elif plot_mgr.plot_type == "FFT":
                    plot_mgr.play_fft(self.data)
            self.play_button.setText("Stop Data Stream")
            self.play_animation = True
        elif self.play_animation and self.data_loaded:
            self.statusBar().showMessage("Stopping data stream...")
            for plot_mgr, _ in self.active_plots.values():
                plot_mgr.stop_animation()
            self.play_button.setText("Start Data Stream")
            self.play_animation = False
        elif self.play_rt_animation and self.ble_reading:
            self.statusBar().showMessage("Stopping real-time data stream...")
            self.play_button.setText("Start Data Stream")
            self.real_time.stop_animation()
            self.play_rt_animation = False
            self.paused_rt = True
        elif self.paused_rt and self.ble_reading:
            self.statusBar().showMessage("Resuming real-time data stream...")
            self.play_button.setText("Stop Data Stream")
            self.real_time.start_rt_animation()
            self.paused_rt = False
        else:
            self.statusBar().showMessage("No data loaded!")

    def export_data_to_file(self):
        """Export the loaded data to a CSV file."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv)")
        
        if file_path:
            if self.ble_reading:
                success = self.file_handler.export_data(file_path, self.channel_names, mode='full')
            else: 
                success = self.file_handler.export_data(file_path, self.channel_names, mode='full')

            if success:
                self.status_bar.showMessage("Export successful!", 3000)
            else:
                self.status_bar.showMessage("Export failed!", 3000)
    
    def open_signal_processing_window(self):
        """Open the signal processing window and connect its signals"""
        self.signal_processing_window = SignalProcessingWindow(self)

        self.signal_processing_window.exec_()
                
    def toggle_plot(self, plot_type, checked):
        """Handle plot visibility based on checkbox state"""
        if checked:
            self.add_plot(plot_type)
        else:
            self.remove_plot(plot_type)

    def add_plot(self, plot_type):
        """Create and show a new plot if not already exists"""
        if plot_type in self.active_plots:
            return
            
        plot_mgr = PlotManager(self.row3)
        plot_mgr.plot_type = plot_type
        
        if plot_type == "Time Series":
            plot_mgr.plot_data(self.data, self.time, self.channel_names, 
                              self.sampling_rate, plot_type)
        elif plot_type in ["Polar FFT", "FFT"]:
            if self.ble_reading:
                plot_mgr.real_fft = self.real_fft
                plot_mgr.ble_reading = True
                plot_mgr.fft_rt = True
                plot_mgr.plot_type = plot_type
                plot_mgr.plot_data(self.data, self.time, self.channel_names, self.sampling_rate, plot_type)
            else:
                plot_mgr.plot_data(self.data, self.time, self.channel_names, self.sampling_rate, plot_type)
        
        splitter = self.find_or_create_splitter()
        splitter.addWidget(plot_mgr.canvas)
        
        self.active_plots[plot_type] = (plot_mgr, splitter)
        self.statusBar().showMessage(f"Added {plot_type} plot")

    def remove_plot(self, plot_type):
        """Remove an existing plot"""
        if plot_type not in self.active_plots:
            return
            
        plot_mgr, splitter = self.active_plots[plot_type]

        if hasattr(plot_mgr, 'animt') and plot_mgr.animt is not None:
            plot_mgr.animt.event_source.stop()
            plot_mgr.animt = None

        if hasattr(plot_mgr, 'animf') and plot_mgr.animf is not None:
            plot_mgr.animf.event_source.stop()
            plot_mgr.animf = None

        plot_mgr.canvas.setParent(None)
        plot_mgr.canvas.deleteLater()
        
        del self.active_plots[plot_type]
        self.statusBar().showMessage(f"Removed {plot_type} plot")

    def find_or_create_splitter(self):
        """Manage splitter layout organization"""
        if self.row3.count() == 0:
            new_splitter = QSplitter(Qt.Horizontal)
            self.row3.addWidget(new_splitter)
            return new_splitter
            
        last_splitter = self.row3.widget(self.row3.count() - 1)
        if last_splitter.count() < 3:
            return last_splitter
            
        new_splitter = QSplitter(Qt.Horizontal)
        self.row3.addWidget(new_splitter)
        return new_splitter
    
    def copy_rt(self):
        self.data = self.real_time.return_rt_data()
    
    def reset_application(self, event):
        """Reset the application to its initial state"""
        for plot_type in list(self.active_plots.keys()):
            self.remove_plot(plot_type)
        
        self.data = np.empty((0, 3))
        self.time = np.empty((0, 1))
        self.data_loaded = False
        self.ble_reading = False
        self.websocket_reading = False
        
        self.row2_widget.setVisible(False)
        self.statusBar().showMessage("Back to Home")

        welcome_layout = QHBoxLayout()

        icon_label = QLabel()
        pixmap = QPixmap("resources\Icon.png").scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(pixmap)

        self.welcome_label = QLabel(
            "<br><br><br>"
            "<span style='font-size: 24px; color: #1E2A38;'>Welcome to GH05T EEG Visualizer!</span><br><br>"
            "This GUI is designed to help you visualize EEG data and connect to Bluetooth/Wifi devices.<br>"
            "You can upload your EEG data files or pair the app with a compatible Bluetooth/Wifi device.<br><br>"
            "Instructions:<br>"
            "- Use the 'Data Input' dropdown in the top bar to upload data or connect a Bluetooth device.<br><br>"
            "Click the link below to view the source code and report any issues!<br>"
            "Github Repository: <a href='https://github.com/Keith-Khadar/Gh05t' style='color: #1E2A38; font-weight:bold;'> https://github.com/Keith-Khadar/Gh05t</a>"
        )
        self.welcome_label.setAlignment(Qt.AlignLeft)
        self.welcome_label.setStyleSheet("color: #1E2A38; font-size: 16px; font-weight:bold;")
        self.welcome_label.setTextFormat(Qt.RichText)
        self.welcome_label.setWordWrap(True)
        self.welcome_label.setOpenExternalLinks(True)

        welcome_layout.addStretch(1)
        welcome_layout.addWidget(icon_label)
        welcome_layout.addWidget(self.welcome_label)
        welcome_layout.addStretch(1)
        
        self.welcome_widget = QWidget()
        self.welcome_widget.setLayout(welcome_layout)

        self.row3_layout.setRowStretch(0, 1)
        self.row3_layout.addWidget(self.welcome_widget, 1, 0, alignment=Qt.AlignCenter)
        self.row3_layout.setRowStretch(2, 1)

        self.row3_layout.addWidget(self.row3)

        if hasattr(self, 'ble_worker'):
            self.ble_worker.disconnect()
            del self.ble_worker
        if hasattr(self, 'web_socket'):
            self.web_socket.stop()
            del self.web_socket

        if self.ble_reading:
            if hasattr(self.real_time, 'animt') and self.real_time.animt is not None:
                self.real_time.animt.event_source.stop()
                self.real_time.animt = None

            self.real_time.canvas.setParent(None)
            self.real_time.canvas.deleteLater()
            
            del self.real_time
        
        # Reset plot checkboxes
        for action in self.plot_actions.values():
            action.setChecked(False)

    def clear_layout(self, layout):
        """Clear the layout of all widgets.

        :param layout: The layout to clear."""
        if self.welcome_widget is not None:
            self.row3_layout.setRowStretch(0, 0)
            self.row3_layout.setRowStretch(2, 0)
            self.row3_layout.removeWidget(self.welcome_widget)
            self.welcome_widget.deleteLater()
            self.welcome_widget = None
        else: 
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.spacerItem():
                    layout.removeItem(item)

    def closeEvent(self, event):
        """Close the window and disconnect the BLE worker."""
        if self.ble_reading is None:
            self.ble_worker.disconnect()
        
        bin_file = "data/raw_data.bin"
        self.file_handler.stop()
        if os.path.exists(bin_file):
            os.remove(bin_file)

        self.close()
        print('Window closed')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())