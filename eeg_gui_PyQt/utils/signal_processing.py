from PyQt5.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QPushButton, QLabel, QComboBox
from PyQt5.QtCore import pyqtSignal

class SignalProcessingWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Signal Processing")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.filter_label = QLabel("Select Filter: TBA")
        layout.addWidget(self.filter_label)

        self.apply_button = QPushButton("Apply")

        self.setLayout(layout)