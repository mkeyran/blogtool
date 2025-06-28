"""Dialog for creating new microposts."""

import uuid
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class MicropostDialog(QDialog):
    """Dialog for creating a new micropost."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Micropost")
        self.setModal(True)
        self.resize(500, 400)

        self._setup_ui()
        self._generate_filename()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()

        # Title input (optional)
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title (optional):"))
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Leave empty for auto-generated filename")
        self.title_edit.textChanged.connect(self._update_filename)
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)

        # Filename preview
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(QLabel("Filename:"))
        self.filename_label = QLabel()
        self.filename_label.setStyleSheet("font-family: monospace; color: #666;")
        filename_layout.addWidget(self.filename_label)
        layout.addLayout(filename_layout)

        # Content input
        layout.addWidget(QLabel("Content:"))
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText(
            "Enter your micropost content here...\n\n"
            "You can include links like: [Link Title](https://example.com)\n"
            "Or just write your thoughts directly."
        )
        layout.addWidget(self.content_edit)

        # Buttons
        button_layout = QHBoxLayout()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        button_layout.addStretch()

        self.create_button = QPushButton("Create Micropost")
        self.create_button.setDefault(True)
        self.create_button.clicked.connect(self.accept)
        button_layout.addWidget(self.create_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _generate_filename(self):
        """Generate filename based on title or use UUID."""
        title = self.title_edit.text().strip()
        current_date = datetime.now().strftime("%Y-%m-%d")

        if title:
            # Convert title to slug
            slug = title.lower().replace(" ", "-")
            # Remove special characters except hyphens
            slug = "".join(c for c in slug if c.isalnum() or c == "-")
            # Remove multiple consecutive hyphens
            while "--" in slug:
                slug = slug.replace("--", "-")
            # Remove leading/trailing hyphens
            slug = slug.strip("-")
            filename = f"{current_date}-{slug}.md"
        else:
            # Use UUID like the original script
            short_uuid = str(uuid.uuid4())[:8]
            filename = f"{current_date}-{short_uuid}.md"

        self.filename_label.setText(filename)
        return filename

    def _update_filename(self):
        """Update filename when title changes."""
        self._generate_filename()

    def get_micropost_data(self):
        """Get the micropost data from the dialog."""
        return {
            "filename": self._generate_filename(),
            "content": self.content_edit.toPlainText(),
            "title": self.title_edit.text().strip(),
        }
