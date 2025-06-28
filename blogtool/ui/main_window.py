"""Main window for the Hugo Blog Management Console."""

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hugo Blog Management Console")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Create menu bar
        self._create_menu_bar()

    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()

        # File menu
        menubar.addMenu("&File")

        # Help menu
        help_menu = menubar.addMenu("&Help")

        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _show_about_dialog(self):
        """Show the About dialog."""
        QMessageBox.about(
            self,
            "About Hugo Blog Management Console",
            "Hugo Blog Management Console\n"
            "Version: 0.1.0\n\n"
            "A Qt-based tool for managing Hugo blogs.\n"
            "Simplifies common blog management operations.",
        )
