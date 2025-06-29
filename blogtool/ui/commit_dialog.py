"""Dialog for creating git commits."""

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class CommitDialog(QDialog):
    """Dialog for creating git commits with message input and templates."""

    def __init__(self, parent=None, git_manager=None, default_message: str = "", specific_path: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Commit Changes")
        self.setModal(True)
        self.resize(500, 300)

        # Store git manager for auto-generation
        self.git_manager = git_manager
        self.specific_path = specific_path
        self.default_message = default_message

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

        # Commit message input with auto-generate button
        message_layout = QHBoxLayout()
        self.message_edit = QTextEdit()
        self.message_edit.setMaximumHeight(120)
        self.message_edit.setPlaceholderText("Enter your commit message...")
        message_layout.addWidget(self.message_edit)

        # Auto-generate button
        if self.git_manager:
            self.auto_generate_btn = QPushButton("Auto-generate")
            self.auto_generate_btn.clicked.connect(self._auto_generate_message)
            self.auto_generate_btn.setMaximumWidth(100)

            # Check if llm is available and disable if not
            if not self._is_llm_available():
                self.auto_generate_btn.setEnabled(False)
                self.auto_generate_btn.setToolTip("Auto-generation requires the 'llm' command to be installed")

            message_layout.addWidget(self.auto_generate_btn)

        form_layout.addRow("Message:", message_layout)

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

    def _is_llm_available(self) -> bool:
        """Check if llm command is available."""
        import subprocess

        try:
            subprocess.run(
                ["llm", "--help"],
                capture_output=True,
                timeout=5,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _auto_generate_message(self):
        """Auto-generate commit message using llm tool."""
        if not self.git_manager:
            return

        # Temporarily disable button to prevent multiple clicks
        self.auto_generate_btn.setEnabled(False)
        self.auto_generate_btn.setText("Generating...")

        try:
            generated_message = self.git_manager.generate_commit_message()
            if generated_message:
                self.message_edit.setPlainText(generated_message)
                # Reset template combo to "Custom message"
                self.template_combo.setCurrentText("Custom message")
            else:
                # Show warning that generation failed
                QMessageBox.warning(
                    self,
                    "Auto-generation Failed",
                    "Failed to generate commit message.\n\n"
                    "This could be because:\n"
                    "• The 'llm' tool is not installed or configured\n"
                    "• No changes were detected\n"
                    "• The LLM service is unavailable\n\n"
                    "Please write a commit message manually.",
                )
        finally:
            # Re-enable button
            self.auto_generate_btn.setEnabled(True)
            self.auto_generate_btn.setText("Auto-generate")

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
