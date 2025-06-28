"""Qt application setup and management."""

import sys

from PySide6.QtWidgets import QApplication

from .main_window import MainWindow


class BlogToolApp:
    """Main application class."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.main_window = MainWindow()

    def run(self):
        """Start the application."""
        self.main_window.show()
        return self.app.exec()
