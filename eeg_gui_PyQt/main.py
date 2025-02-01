import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, 
    QStackedWidget, QStatusBar, QMenu, QAction
)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette
import numpy as np
from utils import PlotManager, GridManager, load_file, export_data, BLEWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("EEG Data Visualizer")
        self.setGeometry(100, 100, 1200, 800)
        
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
        self.data_input_button.setFixedWidth(150)
        self.data_input_button.setFixedHeight(25)
        self.data_input_button.setStyleSheet("color: white; background-color: #2C3E50;")

        self.data_input_menu = QMenu(self)
        self.file_input_action = QAction("File Input", self)
        self.real_time_input_action = QAction("Real-Time Input (BLE)", self)
        self.data_input_menu.addAction(self.file_input_action)
        self.data_input_menu.addAction(self.real_time_input_action)

        self.file_input_action.triggered.connect(self.handle_file_input)
        self.real_time_input_action.triggered.connect(self.handle_real_time_input)

        self.data_input_button.setMenu(self.data_input_menu)

        self.title_label = QLabel("GH05T EEG")
        self.title_label.setFont(QFont("Arial", 16))
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        row1.addWidget(self.data_input_button)
        row1.addStretch(1)
        row1.addWidget(self.title_label)

        main_layout.addWidget(row1_widget)

        row2 = QHBoxLayout()
        row2.setContentsMargins(10, 0, 10, 0)
        row2_widget = QWidget()
        row2_widget.setLayout(row2)
        row2_widget.setStyleSheet("background-color: #2C3E50;")
        row2_widget.setVisible(False)
        row2_widget.setFixedHeight(35)

        self.play_button = QPushButton("Start Data Stream")
        self.play_button.setFixedWidth(150)
        self.play_button.setFixedHeight(25)
        self.play_button.setStyleSheet("color: white; background-color: #3498DB;")
        self.play_button.clicked.connect(self.play_data_stream)

        row2.addWidget(self.play_button)

        self.export_button = QPushButton("Export Data")
        self.export_button.setFixedWidth(150)
        self.export_button.setFixedHeight(25)
        self.export_button.setStyleSheet("color: white; background-color: #3498DB;")
        self.export_button.clicked.connect(self.export_data_to_file)

        row2.addWidget(self.export_button)
        row2.addStretch(1)

        self.add_plot_button = QPushButton("Add Plot")
        self.add_plot_button.setFixedWidth(150)
        self.add_plot_button.setFixedHeight(25)
        self.add_plot_button.setStyleSheet("color: white; background-color: #3498DB;")
        self.add_plot_menu = QMenu(self)

        plot_types = ["Time Series", "FFT"]
        for plot_type in plot_types:
            action = QAction(plot_type, self)
            action.triggered.connect(lambda checked, p=plot_type: self.add_plot(p))
            self.add_plot_menu.addAction(action)

        self.add_plot_button.setMenu(self.add_plot_menu)
        row2.addWidget(self.add_plot_button)

        main_layout.addWidget(row2_widget)
        self.row2_widget = row2_widget

        self.row3 = QStackedWidget()
        self.row3_widget = QWidget()
        self.row3_layout = QVBoxLayout(self.row3_widget)
        self.row3_widget.setStyleSheet("background-color: #34495E;")

        # welcome_label = QLabel(
        #     "<span style='font-size: 24px; color: white;'>Welcome to GH05T EEG Visualizer!</span><br><br>"
        #     "This GUI is designed to help you visualize EEG data and connect to Bluetooth devices.<br>"
        #     "You can upload your EEG data files or pair the app with a compatible Bluetooth device.<br><br>"
        #     "Instructions:<br>"
        #     "- Use the 'Data Input' dropdown in the top bar to upload data or connect a Bluetooth device.<br>"
        #     "- Navigate through other options like Settings, Layout, and more.<br><br>"
        #     "Click the link below to view the source code and report any issues!<br>"
        #     "Github Repository: <a href='https://github.com/Keith-Khadar/Gh05t' style='color: #1E2A38; font-weight:bold;'> https://github.com/Keith-Khadar/Gh05t</a>"
        # )
        # welcome_label.setAlignment(Qt.AlignCenter)
        # welcome_label.setStyleSheet("color: white; font-size: 16px;")
        # welcome_label.setTextFormat(Qt.RichText)
        # welcome_label.setWordWrap(True)
        # welcome_label.setOpenExternalLinks(True)

        # self.row3_layout.addStretch()
        # self.row3_layout.addWidget(welcome_label)
        # self.row3_layout.addStretch()

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
        self.play_animation = False

        self.plot_manager = PlotManager(self.row3)

    def handle_file_input(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select EDF File", "", "EDF Files (*.edf);;All Files (*)")
        if file_path:
            self.data_loaded = True
            self.row2_widget.setVisible(True)
            self.statusBar().showMessage(f"Selected file: {file_path}")
            self.data, self.time, self.channel_names = load_file(file_path)
            self.plot_manager.plot_data(self.data, self.time, self.channel_names)
            self.data_loaded = True

    def handle_real_time_input(self):
        """Initialize BLE connection and start real-time data handling."""
        if not hasattr(self, 'ble_worker'):
            self.status_bar.showMessage("Connecting to BLE device...")
            self.ble_worker = BLEWorker()
            self.ble_worker.data_received.connect(self.handle_real_time)
            self.ble_worker.start()
        
        self.data_loaded = True
        self.row2_widget.setVisible(True)

    def handle_real_time(self, ble_data):
        """Process incoming BLE data and update the plot."""
        if ble_data is None:
            return

        self.data, self.time = ble_data
        self.channel_names = ["Ch1", "Ch2", "Ch3", "Ch4", "Ch5", "Ch6", "Ch7", "Ch8"]

        self.plot_manager.plot_data(self.data, self.time, self.channel_names)

    def play_data_stream(self):
        if self.data_loaded & self.play_animation == False:
            self.statusBar().showMessage("Playing data stream...")
            self.plot_manager.play_data(self.data, self.channel_names)
            self.play_button.setText("Stop Data Stream")
            self.play_animation = True
        elif self.play_animation == True & self.data_loaded:
            self.plot_manager.stop_animation()
            self.play_button.setText("Start Data Stream")
            self.play_animation = False
        else:
            self.statusBar().showMessage("No data loaded!")

    def export_data_to_file(self):
        """Export the loaded data to a CSV file."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv)")
        
        if file_path:
            success = export_data(file_path, self.data, self.time, self.channel_names)
            if success:
                self.status_bar.showMessage("Export successful!", 3000)
            else:
                self.status_bar.showMessage("Export failed!", 3000)

    def add_plot(self, plot_type):
        """Dynamically add a new plot based on selection."""
        self.plot_manager.plot_data(self.data, self.time, self.channel_names, plot_type)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())