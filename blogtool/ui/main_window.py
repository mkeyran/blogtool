"""Main window for the Hugo Blog Management Console."""

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from ..core.git import GitManager
from ..core.hugo import HugoManager
from .commit_dialog import CommitDialog
from .micropost_dialog import MicropostDialog


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hugo Blog Management Console")
        self.setGeometry(100, 100, 800, 600)

        # Initialize managers
        self.hugo_manager = HugoManager()
        self.git_manager = GitManager(self.hugo_manager.get_blog_path())

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Create menu bar
        self._create_menu_bar()

        # Create status bar
        self._create_status_bar()

        # Set up timer for git status updates
        self._setup_git_status_timer()

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

        file_menu.addSeparator()

        # Commit & Push action
        commit_action = QAction("&Commit && Push", self)
        commit_action.setShortcut("Ctrl+Shift+C")
        commit_action.triggered.connect(self._commit_and_push)
        file_menu.addAction(commit_action)

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
            success, message = self.hugo_manager.create_micropost(micropost_data["filename"], micropost_data["content"])

            if success:
                QMessageBox.information(
                    self,
                    "Micropost Created",
                    f"Micropost created successfully!\n\n{message}",
                )
                # Refresh git status after creating content
                self._update_git_status()
            else:
                QMessageBox.critical(
                    self,
                    "Error Creating Micropost",
                    f"Failed to create micropost:\n\n{message}",
                )

    def _commit_and_push(self):
        """Commit changes and push to remote repository."""
        # Check if this is a git repository
        if not self.git_manager.get_status().is_repo:
            QMessageBox.warning(
                self,
                "Not a Git Repository",
                "The blog directory is not a git repository.\n\n" "Please initialize git in your blog directory first.",
            )
            return

        # Get current git status to show in dialog
        status = self.git_manager.get_status()
        total_changes = status.modified_files + status.staged_files + status.untracked_files

        if total_changes == 0:
            QMessageBox.information(
                self,
                "No Changes",
                "There are no changes to commit.\n\n" "The working directory is clean.",
            )
            return

        # Show commit dialog
        dialog = CommitDialog(self)
        if dialog.exec() == QDialog.Accepted:
            commit_message = dialog.get_commit_message()

            # Perform commit and push
            success, message = self.git_manager.commit_and_push(commit_message)

            if success:
                QMessageBox.information(
                    self,
                    "Commit Successful",
                    f"Changes committed and pushed successfully!\n\n{message}",
                )
                # Refresh git status after successful commit
                self._update_git_status()
            else:
                QMessageBox.critical(
                    self,
                    "Commit Failed",
                    f"Failed to commit and push changes:\n\n{message}",
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

    def _create_status_bar(self):
        """Create and configure the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Create git status label
        self.git_status_label = QLabel("Git: Loading...")
        self.status_bar.addPermanentWidget(self.git_status_label)

        # Update git status immediately
        self._update_git_status()

    def _setup_git_status_timer(self):
        """Set up timer for periodic git status updates."""
        self.git_timer = QTimer()
        self.git_timer.timeout.connect(self._update_git_status)
        # Update every 30 seconds
        self.git_timer.start(30000)

    def _update_git_status(self):
        """Update git status display."""
        status = self.git_manager.get_status()

        if not status.is_repo:
            self.git_status_label.setText("Git: Not a repository")
            return

        status_parts = []

        # Show branch
        if status.current_branch:
            status_parts.append(f"Branch: {status.current_branch}")

        # Show file counts
        total_changes = status.modified_files + status.staged_files + status.untracked_files
        if total_changes > 0:
            status_parts.append(f"Changes: {total_changes}")

        # Show unpushed commits indicator
        if status.has_unpushed_commits:
            status_parts.append("Unpushed commits")

        # If no changes and no unpushed commits, show clean status
        if total_changes == 0 and not status.has_unpushed_commits:
            status_parts.append("Clean")

        self.git_status_label.setText(f"Git: {' | '.join(status_parts)}")
