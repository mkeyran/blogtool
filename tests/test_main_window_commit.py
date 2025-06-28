"""Tests for main window commit functionality."""

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
        patch("blogtool.ui.main_window.HugoManager"),
        patch("blogtool.ui.main_window.GitManager") as mock_git_class,
    ):

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


def test_main_window_has_commit_action(main_window):
    """Test that MainWindow has commit action in menu."""
    # Test that the method exists
    assert hasattr(main_window, "_commit_and_push")

    # Test menu bar exists
    assert main_window.menuBar() is not None


def test_commit_and_push_not_git_repo(main_window):
    """Test commit and push when not a git repository."""
    # Mock git status to indicate not a repo
    not_repo_status = GitStatus(
        is_repo=False,
        modified_files=0,
        staged_files=0,
        untracked_files=0,
        has_unpushed_commits=False,
        current_branch="",
    )
    main_window.git_manager.get_status.return_value = not_repo_status

    with patch("blogtool.ui.main_window.QMessageBox.warning") as mock_warning:
        main_window._commit_and_push()

        # Should show warning about not being a git repo
        mock_warning.assert_called_once()
        args = mock_warning.call_args[0]
        assert "Not a Git Repository" in args[1]


def test_commit_and_push_no_changes(main_window):
    """Test commit and push when there are no changes."""
    # Mock git status with no changes
    clean_status = GitStatus(
        is_repo=True,
        modified_files=0,
        staged_files=0,
        untracked_files=0,
        has_unpushed_commits=False,
        current_branch="main",
    )
    main_window.git_manager.get_status.return_value = clean_status

    with patch("blogtool.ui.main_window.QMessageBox.information") as mock_info:
        main_window._commit_and_push()

        # Should show info about no changes
        mock_info.assert_called_once()
        args = mock_info.call_args[0]
        assert "No Changes" in args[1]


def test_commit_and_push_with_changes_success(main_window):
    """Test successful commit and push with changes."""
    # Mock git status with changes
    changes_status = GitStatus(
        is_repo=True,
        modified_files=2,
        staged_files=1,
        untracked_files=1,
        has_unpushed_commits=False,
        current_branch="main",
    )
    main_window.git_manager.get_status.return_value = changes_status

    # Mock successful commit and push
    main_window.git_manager.commit_and_push.return_value = (True, "Success message")

    with patch("blogtool.ui.main_window.CommitDialog") as mock_dialog_class:
        mock_dialog = Mock()
        mock_dialog.exec.return_value = 1  # QDialog.Accepted
        mock_dialog.get_commit_message.return_value = "Test commit message"
        mock_dialog_class.return_value = mock_dialog

        with patch("blogtool.ui.main_window.QMessageBox.information") as mock_info:
            # Mock git status update
            main_window._update_git_status = Mock()

            main_window._commit_and_push()

            # Should call commit and push
            main_window.git_manager.commit_and_push.assert_called_once_with("Test commit message")

            # Should show success message
            mock_info.assert_called_once()
            args = mock_info.call_args[0]
            assert "Commit Successful" in args[1]

            # Should refresh git status
            main_window._update_git_status.assert_called_once()


def test_commit_and_push_with_changes_failure(main_window):
    """Test failed commit and push with changes."""
    # Mock git status with changes
    changes_status = GitStatus(
        is_repo=True,
        modified_files=1,
        staged_files=0,
        untracked_files=0,
        has_unpushed_commits=False,
        current_branch="main",
    )
    main_window.git_manager.get_status.return_value = changes_status

    # Mock failed commit and push
    main_window.git_manager.commit_and_push.return_value = (False, "Error message")

    with patch("blogtool.ui.main_window.CommitDialog") as mock_dialog_class:
        mock_dialog = Mock()
        mock_dialog.exec.return_value = 1  # QDialog.Accepted
        mock_dialog.get_commit_message.return_value = "Test commit message"
        mock_dialog_class.return_value = mock_dialog

        with patch("blogtool.ui.main_window.QMessageBox.critical") as mock_critical:
            main_window._commit_and_push()

            # Should call commit and push
            main_window.git_manager.commit_and_push.assert_called_once_with("Test commit message")

            # Should show error message
            mock_critical.assert_called_once()
            args = mock_critical.call_args[0]
            assert "Commit Failed" in args[1]


def test_commit_and_push_dialog_cancelled(main_window):
    """Test commit and push when dialog is cancelled."""
    # Mock git status with changes
    changes_status = GitStatus(
        is_repo=True,
        modified_files=1,
        staged_files=0,
        untracked_files=0,
        has_unpushed_commits=False,
        current_branch="main",
    )
    main_window.git_manager.get_status.return_value = changes_status

    with patch("blogtool.ui.main_window.CommitDialog") as mock_dialog_class:
        mock_dialog = Mock()
        mock_dialog.exec.return_value = 0  # QDialog.Rejected
        mock_dialog_class.return_value = mock_dialog

        main_window._commit_and_push()

        # Should not call commit and push
        main_window.git_manager.commit_and_push.assert_not_called()
