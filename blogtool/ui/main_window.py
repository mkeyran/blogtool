"""Main window for the Hugo Blog Management Console."""

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from ..core.hugo import HugoManager
from .micropost_dialog import MicropostDialog


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hugo Blog Management Console")
        self.setGeometry(100, 100, 800, 600)

        # Initialize Hugo manager
        self.hugo_manager = HugoManager()

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
        file_menu = menubar.addMenu("&File")

        # New Micropost action
        new_micropost_action = QAction("New &Micropost", self)
        new_micropost_action.setShortcut("Ctrl+M")
        new_micropost_action.triggered.connect(self._create_new_micropost)
        file_menu.addAction(new_micropost_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _create_new_micropost(self):
        """Create a new micropost."""
        if not self.hugo_manager.is_blog_available():
            QMessageBox.warning(
                self,
                "Hugo Blog Not Found",
                "Could not find a Hugo blog in the expected location.\n\n"
                "Please ensure you have a Hugo blog in the sibling directory "
                "'mkeyran.github.io' or check your blog configuration.",
            )
            return

        dialog = MicropostDialog(self)
        if dialog.exec() == QDialog.Accepted:
            micropost_data = dialog.get_micropost_data()

            # Create the micropost
            success, message = self.hugo_manager.create_micropost(
                micropost_data["filename"], micropost_data["content"]
            )

            if success:
                QMessageBox.information(
                    self,
                    "Micropost Created",
                    f"Micropost created successfully!\n\n{message}",
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error Creating Micropost",
                    f"Failed to create micropost:\n\n{message}",
                )

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
