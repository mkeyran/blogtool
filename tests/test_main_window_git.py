"""Tests for main window git integration."""

from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import QApplication

from blogtool.core.git import GitStatus
from blogtool.ui.main_window import MainWindow


@pytest.fixture
def qt_app():
    """Fixture to provide a QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def main_window(qt_app):
    """Fixture to provide a MainWindow instance."""
    with (
        patch("blogtool.ui.main_window.HugoManager") as mock_hugo_class,
        patch("blogtool.ui.main_window.GitManager") as mock_git_class,
    ):

        # Mock hugo manager
        mock_hugo_manager = Mock()
        mock_hugo_manager.list_microposts.return_value = []
        mock_hugo_class.return_value = mock_hugo_manager

        # Create mock git manager with proper status
        mock_git_manager = Mock()
        default_status = GitStatus(
            is_repo=True,
            modified_files=0,
            staged_files=0,
            untracked_files=0,
            has_unpushed_commits=False,
            current_branch="main",
        )
        mock_git_manager.get_status.return_value = default_status
        mock_git_class.return_value = mock_git_manager

        window = MainWindow()
        yield window


def test_main_window_creates_git_manager(qt_app):
    """Test that MainWindow creates a GitManager."""
    with (
        patch("blogtool.ui.main_window.HugoManager") as mock_hugo,
        patch("blogtool.ui.main_window.GitManager") as mock_git,
    ):

        mock_hugo_instance = Mock()
        mock_hugo_instance.get_blog_path.return_value = "/test/path"
        mock_hugo_instance.list_microposts.return_value = []
        mock_hugo.return_value = mock_hugo_instance

        # Create mock git manager with proper status
        mock_git_manager = Mock()
        default_status = GitStatus(
            is_repo=True,
            modified_files=0,
            staged_files=0,
            untracked_files=0,
            has_unpushed_commits=False,
            current_branch="main",
        )
        mock_git_manager.get_status.return_value = default_status
        mock_git.return_value = mock_git_manager

        window = MainWindow()

        # Verify GitManager was created with blog path
        mock_git.assert_called_once_with("/test/path")
        assert hasattr(window, "git_manager")


def test_main_window_has_status_bar(main_window):
    """Test that MainWindow has a status bar with git status."""
    assert hasattr(main_window, "status_bar")
    assert hasattr(main_window, "git_status_label")
    # Status should be updated from the default mock status
    assert "Git:" in main_window.git_status_label.text()


def test_main_window_updates_git_status(main_window):
    """Test that MainWindow updates git status display."""
    # Mock git status
    test_status = GitStatus(
        is_repo=True,
        modified_files=2,
        staged_files=1,
        untracked_files=0,
        has_unpushed_commits=True,
        current_branch="main",
    )

    main_window.git_manager.get_status = Mock(return_value=test_status)

    # Call update method
    main_window._update_git_status()

    # Check status display
    status_text = main_window.git_status_label.text()
    assert "Branch: main" in status_text
    assert "Changes: 3" in status_text  # 2 modified + 1 staged
    assert "Unpushed commits" in status_text


def test_main_window_git_status_not_repo(main_window):
    """Test git status display when not a repository."""
    test_status = GitStatus(
        is_repo=False,
        modified_files=0,
        staged_files=0,
        untracked_files=0,
        has_unpushed_commits=False,
        current_branch="",
    )

    main_window.git_manager.get_status = Mock(return_value=test_status)
    main_window._update_git_status()

    assert main_window.git_status_label.text() == "Git: Not a repository"


def test_main_window_git_status_clean(main_window):
    """Test git status display when repository is clean."""
    test_status = GitStatus(
        is_repo=True,
        modified_files=0,
        staged_files=0,
        untracked_files=0,
        has_unpushed_commits=False,
        current_branch="main",
    )

    main_window.git_manager.get_status = Mock(return_value=test_status)
    main_window._update_git_status()

    status_text = main_window.git_status_label.text()
    assert "Branch: main" in status_text
    assert "Clean" in status_text


def test_main_window_git_timer_setup(main_window):
    """Test that git status timer is set up."""
    assert hasattr(main_window, "git_timer")
    assert main_window.git_timer.isActive()
    # Timer should update every 30 seconds (30000 ms)
    assert main_window.git_timer.interval() == 30000


def test_main_window_refreshes_git_after_micropost(main_window):
    """Test that git status is refreshed after creating a micropost."""
    # Mock successful micropost creation
    main_window.hugo_manager.is_blog_available = Mock(return_value=True)
    main_window.hugo_manager.create_micropost = Mock(return_value=(True, "Success"))

    # Mock dialog
    with patch("blogtool.ui.main_window.MicropostDialog") as mock_dialog_class:
        mock_dialog = Mock()
        mock_dialog.exec.return_value = 1  # QDialog.Accepted
        mock_dialog.get_micropost_data.return_value = {
            "filename": "test.md",
            "content": "test content",
        }
        mock_dialog_class.return_value = mock_dialog

        # Mock message box to avoid GUI interaction
        with patch("blogtool.ui.main_window.QMessageBox.information"):
            # Mock git status update
            main_window._update_git_status = Mock()

            # Trigger micropost creation
            main_window._create_new_micropost()

            # Verify git status was refreshed
            main_window._update_git_status.assert_called()
