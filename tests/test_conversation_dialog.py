"""Tests for conversation creation dialog."""

import pytest
from PySide6.QtWidgets import QApplication

from blogtool.ui.conversation_dialog import ConversationDialog


class TestConversationDialog:
    """Test conversation creation dialog functionality."""

    @pytest.fixture
    def app(self):
        """Create QApplication instance for testing."""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_dialog_initialization(self, app):
        """Test dialog initialization."""
        dialog = ConversationDialog()

        assert dialog.windowTitle() == "New Conversation"
        assert dialog.isModal()
        assert dialog.title == ""
        assert dialog.slug == ""
        assert dialog.language == "en"

        # Check UI elements exist
        assert dialog.title_edit is not None
        assert dialog.language_combo is not None
        assert dialog.slug_preview is not None
        assert dialog.description_edit is not None
        assert dialog.tags_edit is not None
        assert dialog.keywords_edit is not None
        assert dialog.create_btn is not None
        assert dialog.cancel_btn is not None

    def test_language_combo_items(self, app):
        """Test language combo box has correct items."""
        dialog = ConversationDialog()

        assert dialog.language_combo.count() == 3
        assert dialog.language_combo.itemData(0) == "en"
        assert dialog.language_combo.itemData(1) == "ru"
        assert dialog.language_combo.itemData(2) == "pl"

    def test_slug_generation(self, app):
        """Test slug generation from title."""
        dialog = ConversationDialog()

        # Test basic slug generation
        assert dialog._generate_slug("Interview with Expert") == "interview-with-expert"
        assert dialog._generate_slug("Q&A Session") == "qa-session"
        assert dialog._generate_slug("Deep Discussion") == "deep-discussion"
        assert dialog._generate_slug("  Dialogue  ") == "dialogue"
        assert dialog._generate_slug("") == "untitled"

    def test_title_input_updates_previews(self, app):
        """Test that entering title updates slug and path previews."""
        dialog = ConversationDialog()

        # Initially create button should be disabled
        assert not dialog.create_btn.isEnabled()

        # Enter title
        dialog.title_edit.setText("AI Discussion")

        # Check slug preview is updated
        assert dialog.slug_preview.text() == "ai-discussion"

        # Check path preview is updated (conversations go in conversations directory)
        assert "content/english/conversations/ai-discussion/index.md" in dialog.path_preview.toPlainText()

        # Create button should now be enabled
        assert dialog.create_btn.isEnabled()

    def test_language_change_updates_path(self, app):
        """Test that changing language updates path preview."""
        dialog = ConversationDialog()

        # Set a title first
        dialog.title_edit.setText("Test Conversation")

        # Check English path (default)
        assert "content/english/conversations/" in dialog.path_preview.toPlainText()

        # Change to Russian
        dialog.language_combo.setCurrentIndex(1)  # Russian
        assert "content/russian/conversations/" in dialog.path_preview.toPlainText()

        # Change to Polish
        dialog.language_combo.setCurrentIndex(2)  # Polish
        assert "content/polish/conversations/" in dialog.path_preview.toPlainText()

    def test_get_conversation_data_no_title(self, app):
        """Test get_conversation_data returns None when no title."""
        dialog = ConversationDialog()

        assert dialog.get_conversation_data() is None

    def test_get_conversation_data_with_title(self, app):
        """Test get_conversation_data returns correct data."""
        dialog = ConversationDialog()

        # Fill in form
        dialog.title_edit.setText("Expert Interview")
        dialog.description_edit.setText("Discussion with an AI expert")
        dialog.tags_edit.setText("interview, AI, expert")
        dialog.keywords_edit.setText("interview, artificial intelligence")
        dialog.language_combo.setCurrentIndex(1)  # Russian

        data = dialog.get_conversation_data()

        assert data is not None
        assert data["title"] == "Expert Interview"
        assert data["slug"] == "expert-interview"
        assert data["language"] == "ru"
        assert data["description"] == "Discussion with an AI expert"
        assert data["tags"] == ["interview", "AI", "expert"]
        assert data["keywords"] == ["interview", "artificial intelligence"]

    def test_get_conversation_data_empty_fields(self, app):
        """Test get_conversation_data handles empty optional fields."""
        dialog = ConversationDialog()

        # Only set title
        dialog.title_edit.setText("Simple Chat")

        data = dialog.get_conversation_data()

        assert data is not None
        assert data["title"] == "Simple Chat"
        assert data["slug"] == "simple-chat"
        assert data["language"] == "en"  # Default
        assert data["description"] == ""
        assert data["tags"] == []
        assert data["keywords"] == []

    def test_conversation_specific_placeholder(self, app):
        """Test that conversation dialog has conversation-specific placeholder text."""
        dialog = ConversationDialog()

        # Check conversation-specific placeholder for tags
        assert "interview" in dialog.tags_edit.placeholderText().lower()
        assert "dialogue" in dialog.tags_edit.placeholderText().lower()

    def test_conversation_info_label(self, app):
        """Test that conversation dialog includes helpful info about conversations."""
        dialog = ConversationDialog()

        # Should have some informational text about conversations
        # This would be found in the UI layout, but we can test the button text
        assert "Conversation" in dialog.create_btn.text()

    def test_tags_and_keywords_parsing(self, app):
        """Test parsing of comma-separated tags and keywords."""
        dialog = ConversationDialog()

        dialog.title_edit.setText("Test")

        # Test various comma-separated formats
        dialog.tags_edit.setText("interview, discussion,Q&A,  dialogue  ")
        dialog.keywords_edit.setText("talk,chat, conversation")

        data = dialog.get_conversation_data()

        assert data["tags"] == ["interview", "discussion", "Q&A", "dialogue"]
        assert data["keywords"] == ["talk", "chat", "conversation"]
