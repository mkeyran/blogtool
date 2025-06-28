"""Tests for the micropost dialog."""

import pytest
from PySide6.QtWidgets import QApplication

from blogtool.ui.micropost_dialog import MicropostDialog


@pytest.fixture
def qt_app():
    """Fixture to provide a QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_micropost_dialog_creation(qt_app):
    """Test that MicropostDialog can be created."""
    dialog = MicropostDialog()
    assert dialog.windowTitle() == "New Micropost"
    assert dialog.isModal()


def test_micropost_dialog_filename_generation(qt_app):
    """Test filename generation logic."""
    dialog = MicropostDialog()

    # Test auto-generated filename (UUID-based)
    dialog.title_edit.clear()
    filename = dialog._generate_filename()
    assert filename.startswith("2025-")  # Current year
    assert filename.endswith(".md")
    assert len(filename.split("-")) >= 4  # Date parts + UUID

    # Test title-based filename
    dialog.title_edit.setText("Test Title")
    filename = dialog._generate_filename()
    assert "test-title" in filename
    assert filename.endswith(".md")


def test_micropost_dialog_slug_generation(qt_app):
    """Test slug generation from titles."""
    dialog = MicropostDialog()

    # Test basic slug
    dialog.title_edit.setText("Simple Title")
    filename = dialog._generate_filename()
    assert "simple-title" in filename

    # Test special characters
    dialog.title_edit.setText("Title with Special! Characters@")
    filename = dialog._generate_filename()
    assert "title-with-special-characters" in filename

    # Test multiple spaces
    dialog.title_edit.setText("Title   with   spaces")
    filename = dialog._generate_filename()
    assert "title-with-spaces" in filename


def test_micropost_dialog_data_extraction(qt_app):
    """Test extracting data from the dialog."""
    dialog = MicropostDialog()

    # Set test data
    dialog.title_edit.setText("Test Title")
    dialog.content_edit.setPlainText("Test content for micropost")

    data = dialog.get_micropost_data()

    assert data["title"] == "Test Title"
    assert data["content"] == "Test content for micropost"
    assert "test-title" in data["filename"]
    assert data["filename"].endswith(".md")


def test_micropost_dialog_empty_title(qt_app):
    """Test dialog behavior with empty title."""
    dialog = MicropostDialog()

    # Empty title should generate UUID-based filename
    dialog.title_edit.clear()
    dialog.content_edit.setPlainText("Content without title")

    data = dialog.get_micropost_data()

    assert data["title"] == ""
    assert data["content"] == "Content without title"
    # Should have UUID-like pattern (date + 8 chars)
    filename_parts = data["filename"].replace(".md", "").split("-")
    assert len(filename_parts) == 4  # YYYY-MM-DD-UUID
    assert len(filename_parts[3]) == 8  # UUID part
