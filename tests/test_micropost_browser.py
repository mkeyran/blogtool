"""Tests for micropost browser functionality."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from blogtool.core.hugo import HugoManager, MicropostInfo
from blogtool.ui.micropost_browser import MicropostBrowser


class TestMicropostBrowser:
    """Test micropost browser widget."""

    @pytest.fixture
    def app(self):
        """Create QApplication instance for testing."""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    @pytest.fixture
    def mock_hugo_manager(self):
        """Create a mock HugoManager for testing."""
        manager = Mock(spec=HugoManager)
        manager.is_blog_available.return_value = True
        return manager

    @pytest.fixture
    def sample_microposts(self):
        """Create sample micropost data for testing."""
        return [
            MicropostInfo(
                filename="2025-06-28-test-1.md",
                title="Test Micropost 1",
                date=datetime(2025, 6, 28, 10, 30),
                file_path=Path("/fake/path/test-1.md"),
                preview="This is a test micropost for unit testing.",
            ),
            MicropostInfo(
                filename="2025-06-27-test-2.md",
                title="Test Micropost 2",
                date=datetime(2025, 6, 27, 15, 45),
                file_path=Path("/fake/path/test-2.md"),
                preview="Another test micropost with different content.",
            ),
        ]

    def test_browser_initialization(self, app, mock_hugo_manager):
        """Test browser widget initialization."""
        mock_hugo_manager.list_microposts.return_value = []
        browser = MicropostBrowser(mock_hugo_manager)

        assert browser.hugo_manager == mock_hugo_manager
        assert browser.micropost_list is not None
        assert browser.open_editor_btn is not None
        assert browser.open_folder_btn is not None
        assert browser.delete_btn is not None

        # Buttons should be disabled initially
        assert not browser.open_editor_btn.isEnabled()
        assert not browser.open_folder_btn.isEnabled()
        assert not browser.delete_btn.isEnabled()

    def test_refresh_microposts_with_content(self, app, mock_hugo_manager, sample_microposts):
        """Test refreshing micropost list with content."""
        mock_hugo_manager.list_microposts.return_value = sample_microposts

        browser = MicropostBrowser(mock_hugo_manager)

        # Should have 2 items
        assert browser.micropost_list.count() == 2

        # Check first item data
        first_item = browser.micropost_list.item(0)
        first_micropost = first_item.data(Qt.ItemDataRole.UserRole)
        assert first_micropost.title == "Test Micropost 1"
        assert first_micropost.filename == "2025-06-28-test-1.md"

    def test_refresh_microposts_no_blog(self, app):
        """Test refreshing when no blog is available."""
        mock_hugo_manager = Mock(spec=HugoManager)
        mock_hugo_manager.is_blog_available.return_value = False

        browser = MicropostBrowser(mock_hugo_manager)

        # Should have 1 item with error message
        assert browser.micropost_list.count() == 1
        first_item = browser.micropost_list.item(0)
        assert first_item.text() == "No Hugo blog found"

    def test_refresh_microposts_empty_list(self, app, mock_hugo_manager):
        """Test refreshing when no microposts exist."""
        mock_hugo_manager.list_microposts.return_value = []

        browser = MicropostBrowser(mock_hugo_manager)

        # Should have 1 item with empty message
        assert browser.micropost_list.count() == 1
        first_item = browser.micropost_list.item(0)
        assert first_item.text() == "No microposts found"

    def test_selection_enables_buttons(self, app, mock_hugo_manager, sample_microposts):
        """Test that selecting an item enables action buttons."""
        mock_hugo_manager.list_microposts.return_value = sample_microposts

        browser = MicropostBrowser(mock_hugo_manager)

        # Select first item
        browser.micropost_list.setCurrentRow(0)

        # Buttons should now be enabled
        assert browser.open_editor_btn.isEnabled()
        assert browser.open_folder_btn.isEnabled()
        assert browser.delete_btn.isEnabled()

    def test_get_selected_micropost(self, app, mock_hugo_manager, sample_microposts):
        """Test getting selected micropost."""
        mock_hugo_manager.list_microposts.return_value = sample_microposts

        browser = MicropostBrowser(mock_hugo_manager)

        # No selection initially
        assert browser._get_selected_micropost() is None

        # Select first item
        browser.micropost_list.setCurrentRow(0)
        selected = browser._get_selected_micropost()
        assert selected is not None
        assert selected.title == "Test Micropost 1"

    @patch("subprocess.run")
    def test_open_in_editor_success(self, mock_subprocess, app, mock_hugo_manager, sample_microposts):
        """Test opening micropost in editor successfully."""
        mock_hugo_manager.list_microposts.return_value = sample_microposts
        mock_subprocess.return_value = Mock(returncode=0)

        browser = MicropostBrowser(mock_hugo_manager)
        browser.micropost_list.setCurrentRow(0)

        # Should not raise any exception
        browser._open_in_editor()

        # Verify subprocess was called with editor and file path
        mock_subprocess.assert_called_once()
        args = mock_subprocess.call_args[0][0]
        assert len(args) == 2
        assert args[0] in ["code", "subl", "atom", "vim", "nano", "gedit"]
        assert str(sample_microposts[0].file_path) in args

    @patch("subprocess.run")
    def test_open_in_editor_no_editor(self, mock_subprocess, app, mock_hugo_manager, sample_microposts):
        """Test opening micropost when no editor is available."""
        mock_hugo_manager.list_microposts.return_value = sample_microposts
        mock_subprocess.side_effect = FileNotFoundError()

        browser = MicropostBrowser(mock_hugo_manager)
        browser.micropost_list.setCurrentRow(0)

        with patch("blogtool.ui.micropost_browser.QMessageBox.warning") as mock_warning:
            browser._open_in_editor()
            mock_warning.assert_called_once()

    @patch("subprocess.run")
    def test_open_folder_success(self, mock_subprocess, app, mock_hugo_manager, sample_microposts):
        """Test opening folder successfully."""
        mock_hugo_manager.list_microposts.return_value = sample_microposts
        mock_subprocess.return_value = Mock(returncode=0)

        browser = MicropostBrowser(mock_hugo_manager)
        browser.micropost_list.setCurrentRow(0)

        browser._open_folder()

        # Verify subprocess was called with file manager command
        mock_subprocess.assert_called_once()
        args = mock_subprocess.call_args[0][0]
        assert args[0] in ["xdg-open", "open", "explorer"]

    def test_delete_micropost_success(self, app, mock_hugo_manager, sample_microposts):
        """Test deleting micropost successfully."""
        mock_hugo_manager.list_microposts.return_value = sample_microposts

        # Create a temporary file to simulate micropost
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as temp_file:
            temp_file.write("---\ndate: '2025-06-28T10:30:00+02:00'\n---\nTest content")
            temp_path = Path(temp_file.name)

        # Update sample micropost with real file path
        sample_microposts[0].file_path = temp_path

        browser = MicropostBrowser(mock_hugo_manager)
        browser.micropost_list.setCurrentRow(0)

        # Mock the confirmation dialog to return Yes
        with patch("blogtool.ui.micropost_browser.QMessageBox.question") as mock_question:
            mock_question.return_value = mock_question.return_value = 16384  # QMessageBox.Yes

            with patch("blogtool.ui.micropost_browser.QMessageBox.information") as mock_info:
                browser._delete_micropost()

                # Verify file was deleted
                assert not temp_path.exists()
                mock_info.assert_called_once()

    def test_delete_micropost_cancelled(self, app, mock_hugo_manager, sample_microposts):
        """Test cancelling micropost deletion."""
        mock_hugo_manager.list_microposts.return_value = sample_microposts

        browser = MicropostBrowser(mock_hugo_manager)
        browser.micropost_list.setCurrentRow(0)

        # Mock the confirmation dialog to return No
        with patch("blogtool.ui.micropost_browser.QMessageBox.question") as mock_question:
            mock_question.return_value = 65536  # QMessageBox.No

            # Should not delete anything
            browser._delete_micropost()

            # Verify question was asked but nothing else happened
            mock_question.assert_called_once()

    def test_public_refresh_method(self, app, mock_hugo_manager, sample_microposts):
        """Test the public refresh method."""
        mock_hugo_manager.list_microposts.return_value = sample_microposts

        browser = MicropostBrowser(mock_hugo_manager)

        # Clear the list manually
        browser.micropost_list.clear()
        assert browser.micropost_list.count() == 0

        # Call public refresh method
        browser.refresh()

        # Should repopulate the list
        assert browser.micropost_list.count() == 2
