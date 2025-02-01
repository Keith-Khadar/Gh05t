from PyQt5.QtWidgets import QGridLayout

class GridManager:
    def __init__(self):
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.current_row = 0
        self.current_col = 0

    def add_plot(self, plot_canvas):
        """Add a plot to the grid."""
        self.grid_layout.addWidget(plot_canvas, self.current_row, self.current_col)

        self.current_col += 1
        if self.current_col > 1:
            self.current_col = 0
            self.current_row += 1