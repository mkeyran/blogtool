"""Micropost browser widget for viewing and managing microposts."""

import subprocess
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core.hugo import HugoManager, MicropostInfo


class MicropostItem(QWidget):
    """Custom widget for displaying micropost information in the list."""

    def __init__(self, micropost: MicropostInfo):
        super().__init__()
        self.micropost = micropost
        self._setup_ui()

    def _setup_ui(self):
        """Set up the micropost item UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(2)

        # Title and date row
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)

        # Title
        title_label = QLabel(self.micropost.title)
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        title_row.addWidget(title_label)

        title_row.addStretch()

        # Date
        date_str = self.micropost.date.strftime("%Y-%m-%d %H:%M")
        date_label = QLabel(date_str)
        date_label.setStyleSheet("color: #666; font-size: 10px;")
        title_row.addWidget(date_label)

        layout.addLayout(title_row)

        # Preview
        if self.micropost.preview:
            preview_label = QLabel(self.micropost.preview)
            preview_label.setWordWrap(True)
            preview_label.setStyleSheet("color: #555; font-size: 10px;")
            preview_label.setMaximumHeight(40)
            layout.addWidget(preview_label)

        self.setLayout(layout)


class MicropostBrowser(QWidget):
    """Widget for browsing and managing microposts."""

    # Signals
    micropost_updated = Signal()  # Emitted when microposts are modified

    def __init__(self, hugo_manager: Optional[HugoManager] = None):
        super().__init__()
        self.hugo_manager = hugo_manager or HugoManager()
        self._setup_ui()
        self._refresh_microposts()

    def _setup_ui(self):
        """Set up the browser UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Microposts")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 5px 0;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_microposts)
        refresh_btn.setMaximumWidth(80)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Micropost list
        self.micropost_list = QListWidget()
        self.micropost_list.setAlternatingRowColors(True)
        self.micropost_list.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.micropost_list)

        # Action buttons
        button_layout = QHBoxLayout()

        self.open_editor_btn = QPushButton("Open in Editor")
        self.open_editor_btn.clicked.connect(self._open_in_editor)
        self.open_editor_btn.setEnabled(False)
        button_layout.addWidget(self.open_editor_btn)

        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.clicked.connect(self._open_folder)
        self.open_folder_btn.setEnabled(False)
        button_layout.addWidget(self.open_folder_btn)

        button_layout.addStretch()

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._delete_micropost)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; }")
        button_layout.addWidget(self.delete_btn)

        layout.addLayout(button_layout)

    def _refresh_microposts(self):
        """Refresh the micropost list."""
        self.micropost_list.clear()

        if not self.hugo_manager.is_blog_available():
            item = QListWidgetItem("No Hugo blog found")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.micropost_list.addItem(item)
            return

        microposts = self.hugo_manager.list_microposts()

        if not microposts:
            item = QListWidgetItem("No microposts found")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.micropost_list.addItem(item)
            return

        for micropost in microposts:
            # Create list item
            item = QListWidgetItem()
            item.setSizeHint(MicropostItem(micropost).sizeHint())

            # Store micropost data
            item.setData(Qt.ItemDataRole.UserRole, micropost)

            # Add to list
            self.micropost_list.addItem(item)

            # Create and set custom widget
            item_widget = MicropostItem(micropost)
            self.micropost_list.setItemWidget(item, item_widget)

    def _on_selection_changed(self):
        """Handle selection change."""
        current_item = self.micropost_list.currentItem()
        has_selection = current_item is not None and current_item.data(Qt.ItemDataRole.UserRole) is not None

        self.open_editor_btn.setEnabled(has_selection)
        self.open_folder_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def _get_selected_micropost(self) -> Optional[MicropostInfo]:
        """Get the currently selected micropost."""
        current_item = self.micropost_list.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None

    def _open_in_editor(self):
        """Open the selected micropost in external editor."""
        micropost = self._get_selected_micropost()
        if not micropost:
            return

        # Try common editors (could be made configurable later)
        editors = ["code", "subl", "atom", "vim", "nano", "gedit"]

        for editor in editors:
            try:
                subprocess.run(
                    [editor, str(micropost.file_path)],
                    check=True,
                    timeout=5,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                continue

        # Fallback: show error message
        QMessageBox.warning(
            self,
            "Editor Not Found",
            "Could not find a suitable text editor.\n\n"
            "Please install one of the following editors:\n"
            "• Visual Studio Code (code)\n"
            "• Sublime Text (subl)\n"
            "• Vim (vim)\n"
            "• Nano (nano)",
        )

    def _open_folder(self):
        """Open the micropost's folder in file manager."""
        micropost = self._get_selected_micropost()
        if not micropost:
            return

        folder_path = micropost.file_path.parent

        # Try different file managers
        commands = [
            ["xdg-open", str(folder_path)],  # Linux
            ["open", str(folder_path)],  # macOS
            ["explorer", str(folder_path)],  # Windows
        ]

        for cmd in commands:
            try:
                subprocess.run(
                    cmd,
                    check=True,
                    timeout=5,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                continue

        # Fallback: show error message
        QMessageBox.warning(
            self,
            "File Manager Not Found",
            f"Could not open file manager.\n\nPath: {folder_path}",
        )

    def _delete_micropost(self):
        """Delete the selected micropost."""
        micropost = self._get_selected_micropost()
        if not micropost:
            return

        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Delete Micropost",
            f"Are you sure you want to delete this micropost?\n\n"
            f"Title: {micropost.title}\n"
            f"Date: {micropost.date.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                micropost.file_path.unlink()
                self._refresh_microposts()
                self.micropost_updated.emit()
                QMessageBox.information(self, "Micropost Deleted", "Micropost has been deleted successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Delete Failed", f"Failed to delete micropost:\n\n{e}")

    def refresh(self):
        """Public method to refresh the micropost list."""
        self._refresh_microposts()
