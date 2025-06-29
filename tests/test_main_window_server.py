"""Tests for main window Hugo server integration."""

from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import QApplication

from blogtool.core.hugo_server import ServerStatus
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
    """Fixture to provide a MainWindow instance with mocked managers."""
    with (
        patch("blogtool.ui.main_window.HugoManager") as mock_hugo_class,
        patch("blogtool.ui.main_window.GitManager") as mock_git_class,
        patch("blogtool.ui.main_window.HugoServerManager") as mock_server_class,
    ):

        # Mock hugo manager
        mock_hugo_manager = Mock()
        mock_hugo_manager.list_all_content.return_value = []
        mock_hugo_manager.is_blog_available.return_value = True
        mock_hugo_manager.get_blog_path.return_value = "/test/path"
        mock_hugo_class.return_value = mock_hugo_manager

        # Mock git manager
        mock_git_manager = Mock()
        mock_git_manager.get_status.return_value = Mock(
            is_repo=True,
            modified_files=0,
            staged_files=0,
            untracked_files=0,
            has_unpushed_commits=False,
            current_branch="main",
        )
        mock_git_class.return_value = mock_git_manager

        # Mock server manager
        mock_server_manager = Mock()
        mock_server_manager.get_status.return_value = ServerStatus(
            is_running=False,
            url="",
            port=0,
            process_id=None,
        )
        mock_server_class.return_value = mock_server_manager

        window = MainWindow()
        yield window


def test_main_window_creates_server_manager(qt_app):
    """Test that MainWindow creates a HugoServerManager."""
    with (
        patch("blogtool.ui.main_window.HugoManager") as mock_hugo,
        patch("blogtool.ui.main_window.GitManager") as mock_git,
        patch("blogtool.ui.main_window.HugoServerManager") as mock_server,
    ):

        mock_hugo_instance = Mock()
        mock_hugo_instance.get_blog_path.return_value = "/test/path"
        mock_hugo_instance.list_all_content.return_value = []
        mock_hugo_instance.is_blog_available.return_value = True
        mock_hugo.return_value = mock_hugo_instance

        # Create proper git status mock
        git_status = Mock()
        git_status.is_repo = True
        git_status.modified_files = 0
        git_status.staged_files = 0
        git_status.untracked_files = 0
        git_status.has_unpushed_commits = False
        git_status.current_branch = "main"

        mock_git_manager = Mock()
        mock_git_manager.get_status.return_value = git_status
        mock_git.return_value = mock_git_manager

        mock_server.return_value = Mock()

        window = MainWindow()

        # Verify HugoServerManager was created with blog path
        mock_server.assert_called_once_with("/test/path")
        assert hasattr(window, "server_manager")


def test_main_window_has_server_menu(main_window):
    """Test that MainWindow has server menu with actions."""
    menu_bar = main_window.menuBar()

    # Find server menu
    server_menu = None
    for action in menu_bar.actions():
        if action.text() == "&Server":
            server_menu = action.menu()
            break

    assert server_menu is not None

    # Check server menu actions
    action_texts = [action.text() for action in server_menu.actions() if not action.isSeparator()]
    expected_actions = ["&Start Server", "St&op Server", "&Restart Server", "&Preview Site"]

    for expected in expected_actions:
        assert expected in action_texts


def test_main_window_has_server_status_label(main_window):
    """Test that MainWindow has server status label."""
    assert hasattr(main_window, "server_status_label")
    assert "Server:" in main_window.server_status_label.text()


def test_main_window_updates_server_status(main_window):
    """Test that MainWindow updates server status display."""
    # Mock server status
    test_status = ServerStatus(
        is_running=True,
        url="http://localhost:1313",
        port=1313,
        process_id=12345,
    )

    main_window.server_manager.get_status = Mock(return_value=test_status)

    # Call update method
    main_window._update_server_status()

    # Check status display
    status_text = main_window.server_status_label.text()
    assert "Server: Running" in status_text
    assert "http://localhost:1313" in status_text


def test_main_window_server_status_stopped(main_window):
    """Test server status display when server is stopped."""
    test_status = ServerStatus(
        is_running=False,
        url="",
        port=0,
        process_id=None,
    )

    main_window.server_manager.get_status = Mock(return_value=test_status)
    main_window._update_server_status()

    assert main_window.server_status_label.text() == "Server: Stopped"


def test_start_server_success(main_window):
    """Test successful server start."""
    main_window.server_manager.is_running.return_value = False
    main_window.server_manager.start_server.return_value = (True, "Server started at http://localhost:1313")

    with patch("blogtool.ui.main_window.QMessageBox.information") as mock_info:
        main_window._start_server()

        main_window.server_manager.start_server.assert_called_once()
        mock_info.assert_called_once()


def test_start_server_already_running(main_window):
    """Test starting server when already running."""
    main_window.server_manager.is_running.return_value = True
    main_window.server_manager.get_server_url.return_value = "http://localhost:1313"

    with patch("blogtool.ui.main_window.QMessageBox.information") as mock_info:
        main_window._start_server()

        main_window.server_manager.start_server.assert_not_called()
        mock_info.assert_called_once()


def test_start_server_no_blog(main_window):
    """Test starting server when no blog is available."""
    main_window.hugo_manager.is_blog_available.return_value = False

    with patch("blogtool.ui.main_window.QMessageBox.warning") as mock_warning:
        main_window._start_server()

        main_window.server_manager.start_server.assert_not_called()
        mock_warning.assert_called_once()


def test_start_server_failure(main_window):
    """Test server start failure."""
    main_window.server_manager.is_running.return_value = False
    main_window.server_manager.start_server.return_value = (False, "Hugo command not found")

    with patch("blogtool.ui.main_window.QMessageBox.critical") as mock_critical:
        main_window._start_server()

        main_window.server_manager.start_server.assert_called_once()
        mock_critical.assert_called_once()


def test_stop_server_success(main_window):
    """Test successful server stop."""
    main_window.server_manager.is_running.return_value = True
    main_window.server_manager.stop_server.return_value = (True, "Server stopped")

    with patch("blogtool.ui.main_window.QMessageBox.information") as mock_info:
        main_window._stop_server()

        main_window.server_manager.stop_server.assert_called_once()
        mock_info.assert_called_once()


def test_stop_server_not_running(main_window):
    """Test stopping server when not running."""
    main_window.server_manager.is_running.return_value = False

    with patch("blogtool.ui.main_window.QMessageBox.information") as mock_info:
        main_window._stop_server()

        main_window.server_manager.stop_server.assert_not_called()
        mock_info.assert_called_once()


def test_restart_server_success(main_window):
    """Test successful server restart."""
    main_window.server_manager.restart_server.return_value = (True, "Server restarted at http://localhost:1313")

    with patch("blogtool.ui.main_window.QMessageBox.information") as mock_info:
        main_window._restart_server()

        main_window.server_manager.restart_server.assert_called_once()
        mock_info.assert_called_once()


def test_restart_server_no_blog(main_window):
    """Test restarting server when no blog is available."""
    main_window.hugo_manager.is_blog_available.return_value = False

    with patch("blogtool.ui.main_window.QMessageBox.warning") as mock_warning:
        main_window._restart_server()

        main_window.server_manager.restart_server.assert_not_called()
        mock_warning.assert_called_once()


def test_preview_site_server_running(main_window):
    """Test preview site when server is running."""
    main_window.server_manager.is_running.return_value = True
    main_window.server_manager.get_server_url.return_value = "http://localhost:1313"

    with patch("webbrowser.open") as mock_browser:
        main_window._preview_site()

        mock_browser.assert_called_once_with("http://localhost:1313")


def test_preview_site_server_not_running_start_yes(main_window):
    """Test preview site when server not running and user chooses to start."""
    main_window.server_manager.is_running.return_value = False
    main_window.server_manager.start_server.return_value = (True, "Server started")
    main_window.server_manager.get_server_url.return_value = "http://localhost:1313"

    with patch("blogtool.ui.main_window.QMessageBox.question", return_value=16384):  # Yes
        with patch("webbrowser.open") as mock_browser:
            main_window._preview_site()

            main_window.server_manager.start_server.assert_called_once()
            mock_browser.assert_called_once_with("http://localhost:1313")


def test_preview_site_server_not_running_start_no(main_window):
    """Test preview site when server not running and user chooses not to start."""
    main_window.server_manager.is_running.return_value = False

    with patch("blogtool.ui.main_window.QMessageBox.question", return_value=65536):  # No
        with patch("webbrowser.open") as mock_browser:
            main_window._preview_site()

            main_window.server_manager.start_server.assert_not_called()
            mock_browser.assert_not_called()


def test_preview_site_start_fails(main_window):
    """Test preview site when server start fails."""
    main_window.server_manager.is_running.return_value = False
    main_window.server_manager.start_server.return_value = (False, "Start failed")

    with patch("blogtool.ui.main_window.QMessageBox.question", return_value=16384):  # Yes
        with patch("blogtool.ui.main_window.QMessageBox.critical") as mock_critical:
            with patch("webbrowser.open") as mock_browser:
                main_window._preview_site()

                main_window.server_manager.start_server.assert_called_once()
                mock_critical.assert_called_once()
                mock_browser.assert_not_called()


def test_preview_site_browser_fails(main_window):
    """Test preview site when browser launch fails."""
    main_window.server_manager.is_running.return_value = True
    main_window.server_manager.get_server_url.return_value = "http://localhost:1313"

    with patch("webbrowser.open", side_effect=Exception("Browser failed")):
        with patch("blogtool.ui.main_window.QMessageBox.critical") as mock_critical:
            main_window._preview_site()

            mock_critical.assert_called_once()


def test_close_event_cleanup(main_window):
    """Test that close event cleans up server manager."""
    main_window.server_manager.cleanup = Mock()

    # Create a mock close event
    mock_event = Mock()
    main_window.closeEvent(mock_event)

    main_window.server_manager.cleanup.assert_called_once()
    mock_event.accept.assert_called_once()


def test_settings_refresh_server_manager(main_window):
    """Test that changing settings refreshes server manager."""
    with patch("blogtool.ui.main_window.SettingsDialog") as mock_dialog_class:
        mock_dialog = Mock()
        mock_dialog.exec.return_value = 1  # QDialog.Accepted
        mock_dialog_class.return_value = mock_dialog

        with patch("blogtool.ui.main_window.HugoServerManager") as mock_server_class:
            main_window._show_settings()

            # Should create new server manager with updated blog path
            mock_server_class.assert_called_with("/test/path")
