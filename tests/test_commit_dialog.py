"""Tests for the commit dialog."""

import pytest
from PySide6.QtWidgets import QApplication

from blogtool.ui.commit_dialog import CommitDialog


@pytest.fixture
def qt_app():
    """Fixture to provide a QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_commit_dialog_creation(qt_app):
    """Test that CommitDialog can be created."""
    dialog = CommitDialog()
    assert dialog.windowTitle() == "Commit Changes"
    assert dialog.isModal()


def test_commit_dialog_default_state(qt_app):
    """Test commit dialog default state."""
    dialog = CommitDialog()

    # Should have default template selected
    assert dialog.template_combo.currentText() == "Custom message"

    # Message should be empty by default
    assert dialog.get_commit_message() == ""

    # Should not be valid without message
    assert not dialog.is_message_valid()


def test_commit_dialog_template_selection(qt_app):
    """Test template selection functionality."""
    dialog = CommitDialog()

    # Select micropost template
    dialog.template_combo.setCurrentText("Add new micropost")

    # Should populate message
    message = dialog.get_commit_message()
    assert "Add new micropost" in message
    assert "Created a new micropost" in message


def test_commit_dialog_custom_message(qt_app):
    """Test custom message input."""
    dialog = CommitDialog()

    # Set custom message
    test_message = "This is a custom commit message"
    dialog.message_edit.setPlainText(test_message)

    assert dialog.get_commit_message() == test_message
    assert dialog.is_message_valid()


def test_commit_dialog_empty_message_validation(qt_app):
    """Test validation of empty messages."""
    dialog = CommitDialog()

    # Empty message should not be valid
    dialog.message_edit.setPlainText("")
    assert not dialog.is_message_valid()

    # Whitespace-only message should not be valid
    dialog.message_edit.setPlainText("   \n\t  ")
    assert not dialog.is_message_valid()


def test_commit_dialog_template_messages(qt_app):
    """Test all template messages are properly formatted."""
    dialog = CommitDialog()

    templates = [
        "Add new micropost",
        "Update existing content",
        "Fix content issues",
        "Add new blog post",
        "Update blog configuration",
    ]

    for template in templates:
        dialog.template_combo.setCurrentText(template)
        message = dialog.get_commit_message()

        # Each template should have content
        assert len(message) > 0
        assert dialog.is_message_valid()

        # Should contain key words from the template name
        template_words = template.lower().split()
        message_lower = message.lower()
        # At least one key word should be in the message
        assert any(word in message_lower for word in template_words if len(word) > 3)


def test_commit_dialog_multiline_message(qt_app):
    """Test multiline commit messages."""
    dialog = CommitDialog()

    multiline_message = "Short summary\n\nDetailed description\nwith multiple lines"
    dialog.message_edit.setPlainText(multiline_message)

    assert dialog.get_commit_message() == multiline_message
    assert dialog.is_message_valid()


def test_commit_dialog_template_switching(qt_app):
    """Test switching between templates."""
    dialog = CommitDialog()

    # Start with custom message
    custom_message = "My custom message"
    dialog.message_edit.setPlainText(custom_message)

    # Switch to template - should replace content
    dialog.template_combo.setCurrentText("Add new micropost")
    template_message = dialog.get_commit_message()
    assert template_message != custom_message
    assert "Add new micropost" in template_message

    # Switch back to custom - should keep template message
    # (this is expected behavior - templates overwrite content)
    dialog.template_combo.setCurrentText("Custom message")
    # Content should remain as template message
    assert dialog.get_commit_message() == template_message
