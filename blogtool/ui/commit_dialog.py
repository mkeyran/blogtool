"""Dialog for creating git commits."""

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
)


class CommitDialog(QDialog):
    """Dialog for creating git commits with message input and templates."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Commit Changes")
        self.setModal(True)
        self.resize(500, 300)

        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create form layout for input fields
        form_layout = QFormLayout()

        # Message template selector
        self.template_combo = QComboBox()
        self.template_combo.addItems(
            [
                "Custom message",
                "Add new micropost",
                "Update existing content",
                "Fix content issues",
                "Add new blog post",
                "Update blog configuration",
            ]
        )
        self.template_combo.currentTextChanged.connect(self._on_template_changed)
        form_layout.addRow("Template:", self.template_combo)

        # Commit message input
        self.message_edit = QTextEdit()
        self.message_edit.setMaximumHeight(120)
        self.message_edit.setPlaceholderText("Enter your commit message...")
        form_layout.addRow("Message:", self.message_edit)

        layout.addLayout(form_layout)

        # Add information label
        info_label = QLabel("This will add all changes to git, commit them, and push to the remote repository.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 10px; margin: 10px 0;")
        layout.addWidget(info_label)

        # Create button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Set initial focus to message input
        self.message_edit.setFocus()

    def _on_template_changed(self, template_text: str):
        """Handle template selection change."""
        templates = {
            "Add new micropost": "Add new micropost\n\nCreated a new micropost with relevant content.",
            "Update existing content": "Update content\n\nImproved existing content with corrections and enhancements.",
            "Fix content issues": "Fix content issues\n\nResolved formatting, spelling, or structural issues.",
            "Add new blog post": "Add new blog post\n\nPublished a new blog post covering [topic].",
            "Update blog configuration": "Update blog configuration\n\nModified blog settings, themes, or config.",
        }

        if template_text in templates:
            self.message_edit.setPlainText(templates[template_text])
            # Position cursor at the end for editing
            cursor = self.message_edit.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.message_edit.setTextCursor(cursor)

    def get_commit_message(self) -> str:
        """Get the commit message from the dialog.

        Returns:
            The commit message text.
        """
        return self.message_edit.toPlainText().strip()

    def is_message_valid(self) -> bool:
        """Check if the commit message is valid.

        Returns:
            True if message is not empty, False otherwise.
        """
        return bool(self.get_commit_message())

    def accept(self):
        """Accept the dialog only if message is valid."""
        if not self.is_message_valid():
            # Could show a warning message here
            return
        super().accept()
