# Unit Tests for the GUI

## Overview
This repository contains unit tests for the GH05T GUI. These tests check the functionality of the interface and ensure a bug free user experience.

## Running the Tests
To run the unit tests (make sure to be in the parent directory of the GUI):
run ```python -m unittest discover test```

## Unit Tests Overview

1. **test_initial_state**
   - **Purpose:** Tests the initial state of the main window.
   - **Checks:** Window title, visibility of widgets, and status bar message.

2. **test_file_input_action**
   - **Purpose:** Tests the action of inputting a file.
   - **Checks:** Visibility of the row2 widget and updates to the status bar upon file selection.

3. **test_initial_widget_visibility**
   - **Purpose:** Tests the visibility of widgets upon startup.
   - **Checks:** Visibility of the data input button and other buttons (play, export, add plot).

4. **test_load_data_widget_visibility**
   - **Purpose:** Tests the visibility of widgets after loading data.
   - **Checks:** Ensures buttons are visible after a file is selected.

5. **test_play_data_stream**
   - **Purpose:** Tests the functionality of the play data stream button.
   - **Checks:** Button text, play animation state, and status bar message when no plots are available.

6. **test_export_data_to_file**
   - **Purpose:** Tests the functionality to export data to a file.
   - **Checks:** Status bar message confirming successful export after selecting a file.

7. **test_add_plot**
   - **Purpose:** Tests adding a new plot to the main window.
   - **Checks:** Number of plots and status bar message after adding a time series plot.

8. **test_add_multiple_plots**
   - **Purpose:** Tests adding multiple plots to the main window.
   - **Checks:** Total number of plots and status bar message after adding an FFT plot.

9. **test_load_play_data_stream**
   - **Purpose:** Tests the functionality of the play data stream button with plots loaded.
   - **Checks:** Button text, play animation state, and status bar message indicating playback status.

10. **test_real_time_input_action_failure**
    - **Purpose:** Tests the behavior of the real-time input action in case of a failure (device not found).
    - **Checks:** Visibility of the row2 widget and status bar message indicating connection issues.

11. **test_close_application**
    - **Purpose:** Tests that the application closes properly.
    - **Checks:** Ensures that the main window is no longer visible after closing.
