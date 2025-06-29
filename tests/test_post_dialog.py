"""Tests for post creation dialog."""

import pytest
from PySide6.QtWidgets import QApplication

from blogtool.ui.post_dialog import PostDialog


class TestPostDialog:
    """Test post creation dialog functionality."""

    @pytest.fixture
    def app(self):
        """Create QApplication instance for testing."""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_dialog_initialization(self, app):
        """Test dialog initialization."""
        dialog = PostDialog()

        assert dialog.windowTitle() == "New Post"
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
        dialog = PostDialog()

        assert dialog.language_combo.count() == 3
        assert dialog.language_combo.itemData(0) == "en"
        assert dialog.language_combo.itemData(1) == "ru"
        assert dialog.language_combo.itemData(2) == "pl"

    def test_slug_generation(self, app):
        """Test slug generation from title."""
        dialog = PostDialog()

        # Test basic slug generation
        assert dialog._generate_slug("Hello World") == "hello-world"
        assert dialog._generate_slug("Test Post Title") == "test-post-title"
        assert dialog._generate_slug("Special!@# Characters") == "special-characters"
        assert dialog._generate_slug("  Whitespace  ") == "whitespace"
        assert dialog._generate_slug("") == "untitled"

    def test_title_input_updates_previews(self, app):
        """Test that entering title updates slug and path previews."""
        dialog = PostDialog()

        # Initially create button should be disabled
        assert not dialog.create_btn.isEnabled()

        # Enter title
        dialog.title_edit.setText("My Test Post")

        # Check slug preview is updated
        assert dialog.slug_preview.text() == "my-test-post"

        # Check path preview is updated
        assert "content/english/posts/my-test-post/index.md" in dialog.path_preview.toPlainText()

        # Create button should now be enabled
        assert dialog.create_btn.isEnabled()

    def test_language_change_updates_path(self, app):
        """Test that changing language updates path preview."""
        dialog = PostDialog()

        # Set a title first
        dialog.title_edit.setText("Test Post")

        # Check English path (default)
        assert "content/english/posts/" in dialog.path_preview.toPlainText()

        # Change to Russian
        dialog.language_combo.setCurrentIndex(1)  # Russian
        assert "content/russian/posts/" in dialog.path_preview.toPlainText()

        # Change to Polish
        dialog.language_combo.setCurrentIndex(2)  # Polish
        assert "content/polish/posts/" in dialog.path_preview.toPlainText()

    def test_get_post_data_no_title(self, app):
        """Test get_post_data returns None when no title."""
        dialog = PostDialog()

        assert dialog.get_post_data() is None

    def test_get_post_data_with_title(self, app):
        """Test get_post_data returns correct data."""
        dialog = PostDialog()

        # Fill in form
        dialog.title_edit.setText("My Test Post")
        dialog.description_edit.setText("A test post description")
        dialog.tags_edit.setText("test, blog, example")
        dialog.keywords_edit.setText("test, keyword")
        dialog.language_combo.setCurrentIndex(1)  # Russian

        data = dialog.get_post_data()

        assert data is not None
        assert data["title"] == "My Test Post"
        assert data["slug"] == "my-test-post"
        assert data["language"] == "ru"
        assert data["description"] == "A test post description"
        assert data["tags"] == ["test", "blog", "example"]
        assert data["keywords"] == ["test", "keyword"]

    def test_get_post_data_empty_fields(self, app):
        """Test get_post_data handles empty optional fields."""
        dialog = PostDialog()

        # Only set title
        dialog.title_edit.setText("Title Only")

        data = dialog.get_post_data()

        assert data is not None
        assert data["title"] == "Title Only"
        assert data["slug"] == "title-only"
        assert data["language"] == "en"  # Default
        assert data["description"] == ""
        assert data["tags"] == []
        assert data["keywords"] == []

    def test_tags_and_keywords_parsing(self, app):
        """Test parsing of comma-separated tags and keywords."""
        dialog = PostDialog()

        dialog.title_edit.setText("Test")

        # Test various comma-separated formats
        dialog.tags_edit.setText("tag1, tag2,tag3,  tag4  ")
        dialog.keywords_edit.setText("kw1,kw2, kw3")

        data = dialog.get_post_data()

        assert data["tags"] == ["tag1", "tag2", "tag3", "tag4"]
        assert data["keywords"] == ["kw1", "kw2", "kw3"]

    def test_tags_and_keywords_empty_handling(self, app):
        """Test handling of empty tags and keywords."""
        dialog = PostDialog()

        dialog.title_edit.setText("Test")

        # Test empty and whitespace-only entries
        dialog.tags_edit.setText("tag1, , tag2,  ")
        dialog.keywords_edit.setText(" , kw1, ")

        data = dialog.get_post_data()

        assert data["tags"] == ["tag1", "tag2"]
        assert data["keywords"] == ["kw1"]
