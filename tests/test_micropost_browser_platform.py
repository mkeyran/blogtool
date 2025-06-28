"""Tests for micropost browser platform-specific functionality."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import QApplication

from blogtool.core.hugo import HugoManager, MicropostInfo
from blogtool.ui.micropost_browser import MicropostBrowser


class TestMicropostBrowserPlatform:
    """Test platform-specific functionality in micropost browser."""

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
        manager.list_microposts.return_value = []
        return manager

    @pytest.fixture
    def sample_micropost(self):
        """Create sample micropost for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as temp_file:
            temp_file.write("---\ndate: '2025-06-28T10:30:00+02:00'\n---\nTest content")
            temp_path = Path(temp_file.name)

        return MicropostInfo(
            filename="test.md",
            title="Test Micropost",
            date=datetime(2025, 6, 28, 10, 30),
            file_path=temp_path,
            preview="Test content",
        )

    def test_open_in_editor_with_configured_editor(self, app, mock_hugo_manager, sample_micropost):
        """Test opening editor with configured editor command."""
        mock_hugo_manager.list_microposts.return_value = [sample_micropost]

        with patch("blogtool.ui.micropost_browser.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_settings.get_editor_command.return_value = "vim"
            mock_get_settings.return_value = mock_settings

            browser = MicropostBrowser(mock_hugo_manager)
            browser.micropost_list.setCurrentRow(0)

            with patch("subprocess.run") as mock_subprocess:
                browser._open_in_editor()

                # Should call subprocess with configured editor
                mock_subprocess.assert_called_once()
                args = mock_subprocess.call_args[0][0]
                assert args[0] == "vim"
                assert str(sample_micropost.file_path) in args

    def test_open_in_editor_no_editor_configured(self, app, mock_hugo_manager, sample_micropost):
        """Test opening editor when no editor is configured."""
        mock_hugo_manager.list_microposts.return_value = [sample_micropost]

        with patch("blogtool.ui.micropost_browser.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_settings.get_editor_command.return_value = None
            mock_get_settings.return_value = mock_settings

            browser = MicropostBrowser(mock_hugo_manager)
            browser.micropost_list.setCurrentRow(0)

            with patch("blogtool.ui.micropost_browser.QMessageBox.warning") as mock_warning:
                browser._open_in_editor()
                mock_warning.assert_called_once()

    def test_open_in_editor_complex_command(self, app, mock_hugo_manager, sample_micropost):
        """Test opening editor with complex command like 'open -t'."""
        mock_hugo_manager.list_microposts.return_value = [sample_micropost]

        with patch("blogtool.ui.micropost_browser.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_settings.get_editor_command.return_value = "open -t"
            mock_get_settings.return_value = mock_settings

            browser = MicropostBrowser(mock_hugo_manager)
            browser.micropost_list.setCurrentRow(0)

            with patch("subprocess.run") as mock_subprocess:
                browser._open_in_editor()

                # Should split command and include file path
                mock_subprocess.assert_called_once()
                args = mock_subprocess.call_args[0][0]
                assert args == ["open", "-t", str(sample_micropost.file_path)]

    @patch("platform.system")
    @patch("subprocess.run")
    def test_open_folder_macos(self, mock_subprocess, mock_platform, app, mock_hugo_manager, sample_micropost):
        """Test opening folder on macOS."""
        mock_platform.return_value = "Darwin"
        mock_hugo_manager.list_microposts.return_value = [sample_micropost]
        mock_subprocess.return_value = Mock(returncode=0)

        browser = MicropostBrowser(mock_hugo_manager)
        browser.micropost_list.setCurrentRow(0)

        browser._open_folder()

        # Should use 'open' command on macOS
        mock_subprocess.assert_called_once()
        args = mock_subprocess.call_args[0][0]
        assert args[0] == "open"
        assert str(sample_micropost.file_path.parent) in args

    @patch("platform.system")
    @patch("subprocess.run")
    def test_open_folder_linux_success(self, mock_subprocess, mock_platform, app, mock_hugo_manager, sample_micropost):
        """Test opening folder on Linux with successful xdg-open."""
        mock_platform.return_value = "Linux"
        mock_hugo_manager.list_microposts.return_value = [sample_micropost]
        mock_subprocess.return_value = Mock(returncode=0)

        browser = MicropostBrowser(mock_hugo_manager)
        browser.micropost_list.setCurrentRow(0)

        browser._open_folder()

        # Should try xdg-open first on Linux
        mock_subprocess.assert_called_once()
        args = mock_subprocess.call_args[0][0]
        assert args[0] == "xdg-open"
        assert str(sample_micropost.file_path.parent) in args

    @patch("platform.system")
    @patch("subprocess.run")
    def test_open_folder_linux_fallback(self, mock_subprocess, mock_platform, app, mock_hugo_manager, sample_micropost):
        """Test opening folder on Linux with fallback to other file managers."""
        mock_platform.return_value = "Linux"
        mock_hugo_manager.list_microposts.return_value = [sample_micropost]

        # Mock xdg-open failure, nautilus success
        mock_subprocess.side_effect = [
            FileNotFoundError(),  # xdg-open fails
            Mock(returncode=0),  # nautilus succeeds
        ]

        browser = MicropostBrowser(mock_hugo_manager)
        browser.micropost_list.setCurrentRow(0)

        browser._open_folder()

        # Should try multiple commands
        assert mock_subprocess.call_count == 2

        # First call should be xdg-open
        first_call_args = mock_subprocess.call_args_list[0][0][0]
        assert first_call_args[0] == "xdg-open"

        # Second call should be nautilus
        second_call_args = mock_subprocess.call_args_list[1][0][0]
        assert second_call_args[0] == "nautilus"

    @patch("platform.system")
    @patch("subprocess.run")
    def test_open_folder_linux_no_file_manager(
        self, mock_subprocess, mock_platform, app, mock_hugo_manager, sample_micropost
    ):
        """Test opening folder on Linux when no file manager is found."""
        mock_platform.return_value = "Linux"
        mock_hugo_manager.list_microposts.return_value = [sample_micropost]
        mock_subprocess.side_effect = FileNotFoundError()

        browser = MicropostBrowser(mock_hugo_manager)
        browser.micropost_list.setCurrentRow(0)

        with patch("blogtool.ui.micropost_browser.QMessageBox.warning") as mock_warning:
            browser._open_folder()
            mock_warning.assert_called_once()

    @patch("platform.system")
    @patch("subprocess.run")
    def test_open_folder_timeout_handling(
        self, mock_subprocess, mock_platform, app, mock_hugo_manager, sample_micropost
    ):
        """Test handling of subprocess timeout when opening folder."""
        mock_platform.return_value = "Darwin"
        mock_hugo_manager.list_microposts.return_value = [sample_micropost]

        # Mock timeout (but this should be handled gracefully)
        from subprocess import TimeoutExpired

        mock_subprocess.side_effect = TimeoutExpired("open", 5)

        browser = MicropostBrowser(mock_hugo_manager)
        browser.micropost_list.setCurrentRow(0)

        # Should not raise exception or show error dialog
        browser._open_folder()

    def test_editor_error_handling(self, app, mock_hugo_manager, sample_micropost):
        """Test error handling when editor command fails."""
        mock_hugo_manager.list_microposts.return_value = [sample_micropost]

        with patch("blogtool.ui.micropost_browser.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_settings.get_editor_command.return_value = "nonexistent-editor"
            mock_get_settings.return_value = mock_settings

            browser = MicropostBrowser(mock_hugo_manager)
            browser.micropost_list.setCurrentRow(0)

            with patch("subprocess.run") as mock_subprocess:
                mock_subprocess.side_effect = FileNotFoundError()

                with patch("blogtool.ui.micropost_browser.QMessageBox.warning") as mock_warning:
                    browser._open_in_editor()
                    mock_warning.assert_called_once()

    def test_settings_integration(self, app, mock_hugo_manager):
        """Test that browser integrates with settings system."""
        with patch("blogtool.ui.micropost_browser.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_get_settings.return_value = mock_settings

            browser = MicropostBrowser(mock_hugo_manager)

            # Should call get_settings during initialization
            mock_get_settings.assert_called_once()
            assert browser.settings == mock_settings
