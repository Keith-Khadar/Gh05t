import sys
import unittest
from unittest.mock import patch
import urllib.request
import urllib.error
import re
from PyQt5.QtWidgets import QApplication, QFileDialog, QAction
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt, QTimer
from main import MainWindow 

class TestMainWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()

    def setUp(self):
        self.window = MainWindow()
        self.window.show()

    def tearDown(self):
        self.window.close()

    def test_initial_state(self):
        """Test the initial state of the main window."""
        self.assertEqual(self.window.windowTitle(), "EEG Data Visualizer")
        self.assertFalse(self.window.row2_widget.isVisible())
        self.assertEqual(self.window.statusBar().currentMessage(), "Waiting for data input...")

    @patch('PyQt5.QtWidgets.QFileDialog.getOpenFileName')
    def test_file_input_action(self, mock_getOpenFileName):
        """Test the file input action."""
        mock_getOpenFileName.return_value = ('example_eeg_data/Subject00_1.edf', '')

        QTest.mouseClick(self.window.data_input_button, Qt.LeftButton)

        self.window.file_input_action.trigger()

        def handle_dialog():
            file_dialog = self.window.findChild(QFileDialog)
            if file_dialog:
                file_dialog.accept()

        QTimer.singleShot(0, handle_dialog)
        self.window.handle_file_input()

        self.assertTrue(self.window.row2_widget.isVisible())
        self.assertEqual(self.window.statusBar().currentMessage(), "Selected file: example_eeg_data/Subject00_1.edf")

    def test_initial_widget_visibility(self):
        """Test the visibility of widgets on startup."""
        self.assertTrue(self.window.data_input_button.isVisible())

        self.assertFalse(self.window.play_button.isVisible())
        self.assertFalse(self.window.export_button.isVisible())
        self.assertFalse(self.window.add_plot_button.isVisible())

    def test_load_data_widget_visibility(self):
        """Test the visibility of widgets on startup."""
        self.assertTrue(self.window.data_input_button.isVisible())
        self.test_file_input_action()
        self.assertTrue(self.window.play_button.isVisible())
        self.assertTrue(self.window.export_button.isVisible())
        self.assertTrue(self.window.add_plot_button.isVisible())

    def test_play_data_stream(self):
        """Test the play data stream button."""
        QTest.mouseClick(self.window.play_button, Qt.LeftButton)
        self.assertEqual(self.window.play_button.text(), "Start Data Stream")
        self.assertFalse(self.window.play_animation)
        self.assertEqual(self.window.statusBar().currentMessage(), "No plots to animate!")

    @patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName')
    def test_export_data_to_file(self, mock_getSaveFileName):
        """Test the export data to file functionality."""
        self.test_file_input_action()
        mock_getSaveFileName.return_value = ('example_eeg_data/exported_test_data.csv', '')

        def handle_dialog():
            file_dialog = self.window.findChild(QFileDialog)
            if file_dialog:
                file_dialog.accept()

        QTimer.singleShot(0, handle_dialog)
        self.window.export_data_to_file()

        self.assertEqual(self.window.statusBar().currentMessage(), "Export successful!")

    def test_add_plot(self):
        """Test adding a new plot."""
        self.test_file_input_action()

        QTest.mouseClick(self.window.add_plot_button, Qt.LeftButton)
        time_series_action = self.window.add_plot_menu.actions()[0]
        time_series_action.trigger()

        self.assertEqual(len(self.window.plots), 1)
        self.assertEqual(self.window.statusBar().currentMessage(), "Loaded Time Series Plot")

    def test_add_multiple_plots(self):
        """Test adding multiple plots to the window."""
        self.test_file_input_action()

        self.test_add_plot()

        QTest.mouseClick(self.window.add_plot_button, Qt.LeftButton)
        fft_action = self.window.add_plot_menu.actions()[1]
        fft_action.trigger()
        self.assertEqual(len(self.window.plots), 2)
        self.assertEqual(self.window.statusBar().currentMessage(), "Loaded FFT Plot")

    def test_load_play_data_stream(self):
        """Test the play data stream button."""
        self.test_file_input_action()
        self.test_add_plot()

        QTest.mouseClick(self.window.play_button, Qt.LeftButton)
        self.assertEqual(self.window.play_button.text(), "Stop Data Stream")
        self.assertTrue(self.window.play_animation)
        self.assertEqual(self.window.statusBar().currentMessage(), "Playing data stream...")

    def test_real_time_input_action_failure(self):
        """Test the real-time input action."""
        QTest.mouseClick(self.window.data_input_button, Qt.LeftButton)
        self.window.real_time_input_action.trigger()

        self.assertTrue(self.window.row2_widget.isVisible())
        self.assertEqual(self.window.statusBar().currentMessage(), "Connecting to BLE device...")

        QTest.qWait(4000) 

        self.assertIn( self.window.statusBar().currentMessage(), "Scanning for devices...'")

    def test_close_application(self):
        """Test that the application closes properly."""
        self.window.close()
        self.assertFalse(self.window.isVisible(), "Window should be closed.")

if __name__ == "__main__":
    unittest.main()