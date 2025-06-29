"""Conversation creation dialog for conversation posts."""

from typing import Optional

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class ConversationDialog(QDialog):
    """Dialog for creating new conversation posts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Conversation")
        self.setModal(True)
        self.resize(600, 400)

        # Form data
        self.title = ""
        self.slug = ""
        self.language = "en"
        self.description = ""
        self.tags = ""
        self.keywords = ""

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Form layout
        form_layout = QFormLayout()

        # Title input
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter conversation title...")
        form_layout.addRow("Title:", self.title_edit)

        # Language selection
        self.language_combo = QComboBox()
        self.language_combo.addItems([("English", "en"), ("Russian", "ru"), ("Polish", "pl")])
        # Set items with data
        for i, (name, code) in enumerate([("English", "en"), ("Russian", "ru"), ("Polish", "pl")]):
            self.language_combo.setItemData(i, code)
        form_layout.addRow("Language:", self.language_combo)

        # Slug preview (read-only)
        self.slug_preview = QLineEdit()
        self.slug_preview.setReadOnly(True)
        self.slug_preview.setStyleSheet("background-color: #f0f0f0;")
        form_layout.addRow("Slug (auto):", self.slug_preview)

        # Description
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Brief description of the conversation...")
        form_layout.addRow("Description:", self.description_edit)

        # Tags (conversation-specific suggestions)
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("e.g., interview, dialogue, Q&A, discussion")
        form_layout.addRow("Tags:", self.tags_edit)

        # Keywords
        self.keywords_edit = QLineEdit()
        self.keywords_edit.setPlaceholderText("SEO keywords (comma-separated)")
        form_layout.addRow("Keywords:", self.keywords_edit)

        layout.addLayout(form_layout)

        # Info note
        info_label = QLabel(
            "💡 Conversations use the 'conversations' archetype and are optimized for dialogue/interview content."
        )
        info_label.setStyleSheet("color: #666; font-style: italic; margin: 10px 0;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Preview section
        preview_label = QLabel("File path preview:")
        preview_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(preview_label)

        self.path_preview = QTextEdit()
        self.path_preview.setReadOnly(True)
        self.path_preview.setMaximumHeight(80)
        self.path_preview.setStyleSheet("background-color: #f8f8f8; font-family: monospace;")
        layout.addWidget(self.path_preview)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.create_btn = QPushButton("Create Conversation")
        self.create_btn.setDefault(True)
        self.create_btn.setEnabled(False)  # Disabled until title is provided

        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.create_btn)

        layout.addLayout(button_layout)

    def _connect_signals(self):
        """Connect widget signals."""
        self.title_edit.textChanged.connect(self._update_previews)
        self.language_combo.currentIndexChanged.connect(self._update_previews)

        self.cancel_btn.clicked.connect(self.reject)
        self.create_btn.clicked.connect(self.accept)

    def _update_previews(self):
        """Update slug and path previews based on current input."""
        title = self.title_edit.text().strip()

        if not title:
            self.slug_preview.clear()
            self.path_preview.clear()
            self.create_btn.setEnabled(False)
            return

        # Generate slug from title
        self.slug = self._generate_slug(title)
        self.slug_preview.setText(self.slug)

        # Get selected language
        current_index = self.language_combo.currentIndex()
        language_code = self.language_combo.itemData(current_index)

        # Generate path preview
        language_map = {"en": "english", "ru": "russian", "pl": "polish"}
        language_dir = language_map.get(language_code, "english")

        path = f"content/{language_dir}/conversations/{self.slug}/index.md"
        self.path_preview.setPlainText(f"Will create: {path}")

        self.create_btn.setEnabled(True)

    def _generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug from title."""
        import re

        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r"[^\w\s-]", "", title.lower())
        slug = re.sub(r"[-\s]+", "-", slug)
        slug = slug.strip("-")

        return slug or "untitled"

    def get_conversation_data(self) -> Optional[dict]:
        """Get the conversation data from form inputs."""
        if not self.title_edit.text().strip():
            return None

        current_index = self.language_combo.currentIndex()
        language_code = self.language_combo.itemData(current_index)

        # Parse tags and keywords
        tags = [tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip()]
        keywords = [kw.strip() for kw in self.keywords_edit.text().split(",") if kw.strip()]

        return {
            "title": self.title_edit.text().strip(),
            "slug": self.slug,
            "language": language_code,
            "description": self.description_edit.text().strip(),
            "tags": tags,
            "keywords": keywords,
        }
