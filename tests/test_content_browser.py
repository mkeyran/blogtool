"""Tests for content browser functionality."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from blogtool.core.hugo import ContentInfo, HugoManager
from blogtool.ui.content_browser import ContentBrowser


class TestContentBrowser:
    """Test content browser widget."""

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
    def sample_content(self):
        """Create sample content data for testing."""
        return [
            ContentInfo(
                filename="index.md",
                title="Test Blog Post",
                date=datetime(2025, 6, 29, 10, 30),
                file_path=Path("/fake/path/posts/test-post/index.md"),
                preview="This is a test blog post",
                content_type="post",
                language="en",
                slug="test-post",
                description="A test post description",
                tags=["test", "blog"],
                keywords=["test", "blogging"],
            ),
            ContentInfo(
                filename="index.md",
                title="Expert Interview",
                date=datetime(2025, 6, 28, 15, 45),
                file_path=Path("/fake/path/conversations/interview/index.md"),
                preview="Discussion with an expert",
                content_type="conversation",
                language="ru",
                slug="interview",
                description="An expert interview",
                tags=["interview", "expert"],
                keywords=["conversation", "expert"],
            ),
            ContentInfo(
                filename="2025-06-27-micro.md",
                title="Quick Note",
                date=datetime(2025, 6, 27, 12, 00),
                file_path=Path("/fake/path/microposts/2025-06-27-micro.md"),
                preview="A quick micropost",
                content_type="micropost",
                language="en",
                slug="2025-06-27-micro",
                description="",
                tags=[],
                keywords=[],
            ),
        ]

    def test_browser_initialization(self, app, mock_hugo_manager):
        """Test browser widget initialization."""
        mock_hugo_manager.list_all_content.return_value = []
        browser = ContentBrowser(mock_hugo_manager)

        assert browser.hugo_manager == mock_hugo_manager
        assert browser.content_list is not None
        assert browser.filter_combo is not None
        assert browser.open_editor_btn is not None
        assert browser.open_folder_btn is not None
        assert browser.delete_btn is not None

        # Buttons should be disabled initially
        assert not browser.open_editor_btn.isEnabled()
        assert not browser.open_folder_btn.isEnabled()
        assert not browser.delete_btn.isEnabled()

    def test_refresh_content_with_data(self, app, mock_hugo_manager, sample_content):
        """Test refreshing content list with data."""
        mock_hugo_manager.list_all_content.return_value = sample_content

        browser = ContentBrowser(mock_hugo_manager)

        # Should have 3 items
        assert browser.content_list.count() == 3

        # Check first item data
        first_item = browser.content_list.item(0)
        first_content = first_item.data(Qt.ItemDataRole.UserRole)
        assert first_content.title == "Test Blog Post"
        assert first_content.content_type == "post"

    def test_refresh_content_no_blog(self, app):
        """Test refreshing when no blog is available."""
        mock_hugo_manager = Mock(spec=HugoManager)
        mock_hugo_manager.is_blog_available.return_value = False

        browser = ContentBrowser(mock_hugo_manager)

        # Should have 1 item with error message
        assert browser.content_list.count() == 1
        first_item = browser.content_list.item(0)
        assert first_item.text() == "No Hugo blog found"

    def test_refresh_content_empty_list(self, app, mock_hugo_manager):
        """Test refreshing when no content exists."""
        mock_hugo_manager.list_all_content.return_value = []

        browser = ContentBrowser(mock_hugo_manager)

        # Should have 1 item with empty message
        assert browser.content_list.count() == 1
        first_item = browser.content_list.item(0)
        assert first_item.text() == "No content found"

    def test_filter_functionality(self, app, mock_hugo_manager, sample_content):
        """Test content type filtering."""
        mock_hugo_manager.list_all_content.return_value = sample_content

        browser = ContentBrowser(mock_hugo_manager)

        # Test "All" filter (default)
        assert browser.content_list.count() == 3

        # Test "Posts" filter
        browser.filter_combo.setCurrentText("Posts")
        assert browser.content_list.count() == 1
        item = browser.content_list.item(0)
        content = item.data(Qt.ItemDataRole.UserRole)
        assert content.content_type == "post"

        # Test "Conversations" filter
        browser.filter_combo.setCurrentText("Conversations")
        assert browser.content_list.count() == 1
        item = browser.content_list.item(0)
        content = item.data(Qt.ItemDataRole.UserRole)
        assert content.content_type == "conversation"

        # Test "Microposts" filter
        browser.filter_combo.setCurrentText("Microposts")
        assert browser.content_list.count() == 1
        item = browser.content_list.item(0)
        content = item.data(Qt.ItemDataRole.UserRole)
        assert content.content_type == "micropost"

    def test_selection_enables_buttons(self, app, mock_hugo_manager, sample_content):
        """Test that selecting an item enables action buttons."""
        mock_hugo_manager.list_all_content.return_value = sample_content

        browser = ContentBrowser(mock_hugo_manager)

        # Select first item
        browser.content_list.setCurrentRow(0)

        # Buttons should now be enabled
        assert browser.open_editor_btn.isEnabled()
        assert browser.open_folder_btn.isEnabled()
        assert browser.delete_btn.isEnabled()

    def test_get_selected_content(self, app, mock_hugo_manager, sample_content):
        """Test getting selected content."""
        mock_hugo_manager.list_all_content.return_value = sample_content

        browser = ContentBrowser(mock_hugo_manager)

        # No selection initially
        assert browser._get_selected_content() is None

        # Select first item
        browser.content_list.setCurrentRow(0)
        selected = browser._get_selected_content()
        assert selected is not None
        assert selected.title == "Test Blog Post"

    def test_open_in_editor_success(self, app, mock_hugo_manager, sample_content):
        """Test opening content in editor successfully."""
        mock_hugo_manager.list_all_content.return_value = sample_content

        with patch("blogtool.ui.content_browser.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_settings.get_editor_command.return_value = "code"
            mock_get_settings.return_value = mock_settings

            browser = ContentBrowser(mock_hugo_manager)
            browser.content_list.setCurrentRow(0)

            with patch("subprocess.run") as mock_subprocess:
                browser._open_in_editor()

                # Verify subprocess was called with configured editor and file path
                mock_subprocess.assert_called_once()
                args = mock_subprocess.call_args[0][0]
                assert len(args) == 2
                assert args[0] == "code"
                assert str(sample_content[0].file_path) in args

    def test_open_in_editor_no_editor(self, app, mock_hugo_manager, sample_content):
        """Test opening content when no editor is available."""
        mock_hugo_manager.list_all_content.return_value = sample_content

        with patch("blogtool.ui.content_browser.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_settings.get_editor_command.return_value = None
            mock_get_settings.return_value = mock_settings

            browser = ContentBrowser(mock_hugo_manager)
            browser.content_list.setCurrentRow(0)

            with patch("blogtool.ui.content_browser.QMessageBox.warning") as mock_warning:
                browser._open_in_editor()
                mock_warning.assert_called_once()

    def test_delete_content_success(self, app, mock_hugo_manager, sample_content):
        """Test deleting content successfully."""
        mock_hugo_manager.list_all_content.return_value = sample_content

        # Create a temporary file to simulate content
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as temp_file:
            temp_file.write("---\ndate: '2025-06-29T10:30:00+02:00'\n---\nTest content")
            temp_path = Path(temp_file.name)

        # Update sample content with real file path
        sample_content[2].file_path = temp_path  # Use micropost for file deletion

        browser = ContentBrowser(mock_hugo_manager)
        browser.content_list.setCurrentRow(2)  # Select micropost

        # Mock the confirmation dialog to return Yes
        with patch("blogtool.ui.content_browser.QMessageBox.question") as mock_question:
            mock_question.return_value = 16384  # QMessageBox.Yes

            with patch("blogtool.ui.content_browser.QMessageBox.information") as mock_info:
                browser._delete_content()

                # Verify file was deleted
                assert not temp_path.exists()
                mock_info.assert_called_once()

    def test_delete_content_cancelled(self, app, mock_hugo_manager, sample_content):
        """Test cancelling content deletion."""
        mock_hugo_manager.list_all_content.return_value = sample_content

        browser = ContentBrowser(mock_hugo_manager)
        browser.content_list.setCurrentRow(0)

        # Mock the confirmation dialog to return No
        with patch("blogtool.ui.content_browser.QMessageBox.question") as mock_question:
            mock_question.return_value = 65536  # QMessageBox.No

            # Should not delete anything
            browser._delete_content()

            # Verify question was asked but nothing else happened
            mock_question.assert_called_once()

    def test_public_refresh_method(self, app, mock_hugo_manager, sample_content):
        """Test the public refresh method."""
        mock_hugo_manager.list_all_content.return_value = sample_content

        browser = ContentBrowser(mock_hugo_manager)

        # Clear the list manually
        browser.content_list.clear()
        assert browser.content_list.count() == 0

        # Call public refresh method
        browser.refresh()

        # Should repopulate the list
        assert browser.content_list.count() == 3
