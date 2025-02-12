import sys
import asyncio
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, 
    QStatusBar, QMenu, QAction, QGridLayout, QSplitter, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QColor, QPalette
import numpy as np
from utils import PlotManager, load_file, export_data, BLEWorker, EEGBLE

class MainWindow(QMainWindow):
    def __init__(self):
        '''Initialize the main window of the GUI'''
        super().__init__()

        self.setWindowTitle("EEG Data Visualizer")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        
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

        title_layout = QHBoxLayout()

        # icon_label = QLabel()
        # icon_pixmap = QPixmap("resources\icon_white.png")
        # icon_label.setPixmap(icon_pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        self.title_label = QLabel("GH05T EEG")
        self.title_label.setFont(QFont("Arial", 16))
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # title_layout.addWidget(icon_label)
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

        self.row3 = QSplitter()
        self.row3_widget = QWidget()
        self.row3_layout = QGridLayout(self.row3_widget)
        self.row3_widget.setStyleSheet("background-color: #34495E;")

        welcome_layout = QHBoxLayout()

        icon_label = QLabel()
        pixmap = QPixmap("resources\Icon.png").scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(pixmap)

        welcome_label = QLabel(
            "<br><br><br>"
            "<span style='font-size: 24px; color: #1E2A38;'>Welcome to GH05T EEG Visualizer!</span><br><br>"
            "This GUI is designed to help you visualize EEG data and connect to Bluetooth devices.<br>"
            "You can upload your EEG data files or pair the app with a compatible Bluetooth device.<br><br>"
            "Instructions:<br>"
            "- Use the 'Data Input' dropdown in the top bar to upload data or connect a Bluetooth device.<br>"
            "- Navigate through other options like Settings, Layout, and more.<br><br>"
            "Click the link below to view the source code and report any issues!<br>"
            "Github Repository: <a href='https://github.com/Keith-Khadar/Gh05t' style='color: #1E2A38; font-weight:bold;'> https://github.com/Keith-Khadar/Gh05t</a>"
        )
        welcome_label.setAlignment(Qt.AlignLeft)
        welcome_label.setStyleSheet("color: #1E2A38; font-size: 16px; font-weight:bold;")
        welcome_label.setTextFormat(Qt.RichText)
        welcome_label.setWordWrap(True)
        welcome_label.setOpenExternalLinks(True)

        welcome_layout.addStretch(1)
        welcome_layout.addWidget(icon_label)
        welcome_layout.addWidget(welcome_label)
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
        self.play_animation = False

        self.plot_manager = PlotManager(self.row3)

        self.plots = []

    def handle_file_input(self):
        '''Opens a file dialog to upload data from a file.'''
        if self.ble_reading:
            self.ble_worker.disconnect()

        file_path, _ = QFileDialog.getOpenFileName(self, "Select EDF File", "", "EDF Files (*.edf);;All Files (*)")
        if file_path:
            self.row2_widget.setVisible(True)
            self.statusBar().showMessage(f"Selected file: {file_path}")
            self.data, self.time, self.channel_names = load_file(file_path)

            self.clear_layout(self.row3_layout)

            self.add_plot("Time Series")
            self.data_loaded = True

    def handle_real_time_input(self):
        """Initialize BLE connection and start real-time data handling."""
        if not hasattr(self, 'ble_worker'):
            self.clear_layout(self.row3_layout)

            self.status_bar.showMessage("Connecting to BLE device...")
            self.ble_worker = BLEWorker()
            self.ble_worker.data_received.connect(self.handle_real_time)
            self.ble_worker.start()

            self.ble_worker.status_update_signal.connect(self.update_status_bar)
            self.ble_worker.connection_failed_signal.connect(self.handle_connection_failed)
        
            self.ble_reading = True
            self.data_loaded = True
            self.row2_widget.setVisible(True)
    
    def handle_connection_failed(self):
        """Handle connection failure and update the ble_reading status."""
        self.ble_reading = False

    def update_status_bar(self, message):
        self.statusBar().showMessage(message)

    def handle_real_time(self, ble_timestamp, ble_data):
        """Process incoming BLE data and update the plot."""
        if ble_data is None:
            return

        self.data = ble_data
        self.timestamp = ble_timestamp
        self.channel_names = ["Ch1", "Ch2", "Ch3", "Ch4", "Ch5", "Ch6", "Ch7", "Ch8"]
        print("Setting up Real Time plotting")

        self.plot_manager.handle_real_time_data(self.data, self.timestamp)

    def play_data_stream(self):
        """Start the animation for all applicable plots."""
        if self.data_loaded and not self.play_animation:
            self.statusBar().showMessage("Playing data stream...")
            for plot in self.plots:
                if plot.plot_type == "Time Series":
                    plot.play_data(self.data, self.channel_names)
            self.play_button.setText("Stop Data Stream")
            self.play_animation = True
        elif self.play_animation and self.data_loaded:
            self.statusBar().showMessage("Stopping data stream...")
            for plot in self.plots:
                plot.stop_animation()
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
        """Dynamically add a new plot to a resizable grid."""
        new_plot = PlotManager(self.row3)
        new_plot.plot_type = plot_type

        if plot_type == "Time Series":
            new_plot.plot_data(self.data, self.time, self.channel_names, plot_type)
            self.statusBar().showMessage("Loaded Time Series Plot")
        elif plot_type == "FFT":
            fft_data = np.fft.fft(self.data, axis=1)
            freqs = np.fft.fftfreq(self.data.shape[1], d=1/250)
            new_plot.plot_data(np.abs(fft_data), freqs, self.channel_names, plot_type)
            self.statusBar().showMessage("Loaded FFT Plot")
        if self.row3.count() == 0:
            row_splitter = QSplitter(Qt.Horizontal)
            row_splitter.addWidget(new_plot.canvas)
            self.row3.addWidget(row_splitter)
        else:
            last_row = self.row3.widget(self.row3.count() - 1)
            if last_row.count() < 2:
                last_row.addWidget(new_plot.canvas)
            else:
                row_splitter = QSplitter(Qt.Horizontal)
                row_splitter.addWidget(new_plot.canvas)
                self.row3.addWidget(row_splitter)

        self.plots.append(new_plot)

    def clear_layout(self, layout):
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
        # reply = QMessageBox.question(
        #     self, 
        #     "Window Close", 
        #     "<span style='color: black;'>Are you sure you want to close the window?</span>", 
        #     QMessageBox.Yes | QMessageBox.No, 
        #     QMessageBox.No
        # )

        # if reply == QMessageBox.Yes:
        if self.ble_reading is None:
            self.ble_worker.disconnect_ble()
        self.close()
        print('Window closed')
        # else:
        #     pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())