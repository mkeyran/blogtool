"""Tests for Hugo server management functionality."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from blogtool.core.hugo_server import HugoServerManager, ServerStatus


class TestHugoServerManager:
    """Test Hugo server manager."""

    @pytest.fixture
    def temp_blog_path(self):
        """Create temporary blog directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Create basic Hugo structure
            (temp_path / "hugo.yaml").touch()
            (temp_path / "content").mkdir()
            yield temp_path

    def test_server_manager_initialization(self, temp_blog_path):
        """Test server manager initialization."""
        manager = HugoServerManager(temp_blog_path)

        assert manager.blog_path == temp_blog_path
        assert manager.process is None
        assert manager.default_port == 1313
        assert manager.default_host == "localhost"

    def test_server_manager_with_no_path(self):
        """Test server manager initialization with no path."""
        manager = HugoServerManager()

        assert manager.blog_path == Path.cwd()
        assert manager.process is None

    def test_is_running_with_no_process(self, temp_blog_path):
        """Test is_running when no process exists."""
        manager = HugoServerManager(temp_blog_path)

        assert not manager.is_running()

    def test_is_running_with_terminated_process(self, temp_blog_path):
        """Test is_running when process has terminated."""
        manager = HugoServerManager(temp_blog_path)

        # Mock a terminated process
        mock_process = Mock()
        mock_process.poll.return_value = 0  # Process has terminated
        manager.process = mock_process

        assert not manager.is_running()
        assert manager.process is None  # Should be cleaned up

    def test_is_running_with_active_process(self, temp_blog_path):
        """Test is_running with active process."""
        manager = HugoServerManager(temp_blog_path)

        # Mock an active process
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process still running
        manager.process = mock_process

        assert manager.is_running()

    def test_get_status_when_not_running(self, temp_blog_path):
        """Test get_status when server is not running."""
        manager = HugoServerManager(temp_blog_path)

        status = manager.get_status()

        assert isinstance(status, ServerStatus)
        assert not status.is_running
        assert status.url == ""
        assert status.port == 0
        assert status.process_id is None

    def test_get_status_when_running(self, temp_blog_path):
        """Test get_status when server is running."""
        manager = HugoServerManager(temp_blog_path)

        # Mock running process
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.pid = 12345
        manager.process = mock_process

        status = manager.get_status()

        assert status.is_running
        assert status.url == "http://localhost:1313"
        assert status.port == 1313
        assert status.process_id == 12345

    def test_get_server_url_when_not_running(self, temp_blog_path):
        """Test get_server_url when not running."""
        manager = HugoServerManager(temp_blog_path)

        url = manager.get_server_url()

        assert url == ""

    def test_get_server_url_when_running(self, temp_blog_path):
        """Test get_server_url when running."""
        manager = HugoServerManager(temp_blog_path)

        # Mock running process
        mock_process = Mock()
        mock_process.poll.return_value = None
        manager.process = mock_process

        url = manager.get_server_url()

        assert url == "http://localhost:1313"

    def test_start_server_already_running(self, temp_blog_path):
        """Test starting server when already running."""
        manager = HugoServerManager(temp_blog_path)

        # Mock running process
        mock_process = Mock()
        mock_process.poll.return_value = None
        manager.process = mock_process

        success, message = manager.start_server()

        assert not success
        assert "already running" in message

    def test_start_server_hugo_not_found(self, temp_blog_path):
        """Test starting server when Hugo command not found."""
        manager = HugoServerManager(temp_blog_path)

        with patch("subprocess.Popen", side_effect=FileNotFoundError):
            success, message = manager.start_server()

            assert not success
            assert "Hugo command not found" in message

    def test_start_server_process_fails(self, temp_blog_path):
        """Test starting server when process fails to start."""
        manager = HugoServerManager(temp_blog_path)

        # Mock process that terminates immediately
        mock_process = Mock()
        mock_process.poll.return_value = 1  # Process terminated with error
        mock_process.communicate.return_value = ("", "Error starting server")

        with patch("subprocess.Popen", return_value=mock_process):
            with patch("time.sleep"):  # Skip sleep in tests
                success, message = manager.start_server()

                assert not success
                assert "failed to start" in message.lower()

    def test_start_server_success(self, temp_blog_path):
        """Test successful server start."""
        manager = HugoServerManager(temp_blog_path)

        # Mock successful process
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process still running

        with patch("subprocess.Popen", return_value=mock_process):
            with patch("time.sleep"):  # Skip sleep in tests
                with patch.object(manager, "_check_server_response", return_value=True):
                    success, message = manager.start_server()

                    assert success
                    assert "started successfully" in message
                    assert manager.process == mock_process

    def test_start_server_not_responding(self, temp_blog_path):
        """Test server start when process starts but doesn't respond."""
        manager = HugoServerManager(temp_blog_path)

        # Mock process that starts but doesn't respond
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.terminate = Mock()
        mock_process.wait = Mock()

        with patch("subprocess.Popen", return_value=mock_process):
            with patch("time.sleep"):
                with patch.object(manager, "_check_server_response", return_value=False):
                    success, message = manager.start_server()

                    assert not success
                    assert "not responding" in message
                    # Should clean up the process
                    mock_process.terminate.assert_called_once()

    def test_stop_server_not_running(self, temp_blog_path):
        """Test stopping server when not running."""
        manager = HugoServerManager(temp_blog_path)

        success, message = manager.stop_server()

        assert not success
        assert "not running" in message

    def test_stop_server_success(self, temp_blog_path):
        """Test successful server stop."""
        manager = HugoServerManager(temp_blog_path)

        # Mock running process
        mock_process = Mock()
        mock_process.terminate = Mock()
        mock_process.wait = Mock()
        manager.process = mock_process

        # Mock is_running to return True initially
        with patch.object(manager, "is_running", return_value=True):
            success, message = manager.stop_server()

            assert success
            assert "stopped successfully" in message
            assert manager.process is None
            mock_process.terminate.assert_called_once()
            mock_process.wait.assert_called_once()

    def test_stop_server_force_kill(self, temp_blog_path):
        """Test stopping server with force kill."""
        manager = HugoServerManager(temp_blog_path)

        # Mock process that doesn't terminate gracefully
        mock_process = Mock()
        mock_process.terminate = Mock()
        mock_process.wait = Mock(
            side_effect=[subprocess.TimeoutExpired("cmd", 5), None]
        )  # First call times out, second succeeds
        mock_process.kill = Mock()
        manager.process = mock_process

        # Mock is_running to return True initially
        with patch.object(manager, "is_running", return_value=True):
            success, message = manager.stop_server()

            assert success
            mock_process.terminate.assert_called_once()
            mock_process.kill.assert_called_once()
            assert mock_process.wait.call_count == 2

    def test_restart_server(self, temp_blog_path):
        """Test server restart."""
        manager = HugoServerManager(temp_blog_path)

        # Mock the stop and start methods
        with patch.object(manager, "stop_server", return_value=(True, "Stopped")):
            with patch.object(manager, "start_server", return_value=(True, "Started")):
                # Mock running server
                mock_process = Mock()
                mock_process.poll.return_value = None
                manager.process = mock_process

                success, message = manager.restart_server()

                assert success
                assert "Started" in message

    def test_restart_server_stop_fails(self, temp_blog_path):
        """Test server restart when stop fails."""
        manager = HugoServerManager(temp_blog_path)

        # Mock the stop method to fail
        with patch.object(manager, "stop_server", return_value=(False, "Stop failed")):
            # Mock running server
            mock_process = Mock()
            mock_process.poll.return_value = None
            manager.process = mock_process

            success, message = manager.restart_server()

            assert not success
            assert "Stop failed" in message

    def test_check_server_response_success(self, temp_blog_path):
        """Test successful server response check."""
        manager = HugoServerManager(temp_blog_path)

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = manager._check_server_response("http://localhost:1313")

            assert result is True
            mock_get.assert_called_once_with("http://localhost:1313", timeout=5)

    def test_check_server_response_failure(self, temp_blog_path):
        """Test failed server response check."""
        manager = HugoServerManager(temp_blog_path)

        with patch("requests.get", side_effect=Exception("Connection failed")):
            result = manager._check_server_response("http://localhost:1313")

            assert result is False

    def test_cleanup_with_running_server(self, temp_blog_path):
        """Test cleanup when server is running."""
        manager = HugoServerManager(temp_blog_path)

        # Mock running server
        mock_process = Mock()
        mock_process.poll.return_value = None
        manager.process = mock_process

        with patch.object(manager, "stop_server", return_value=(True, "Stopped")) as mock_stop:
            manager.cleanup()

            mock_stop.assert_called_once()

    def test_cleanup_with_stopped_server(self, temp_blog_path):
        """Test cleanup when server is stopped."""
        manager = HugoServerManager(temp_blog_path)

        # Should not raise any errors
        manager.cleanup()
