"""Hugo development server management."""

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import requests


@dataclass
class ServerStatus:
    """Hugo server status information."""

    is_running: bool
    url: str
    port: int
    process_id: Optional[int] = None


class HugoServerManager:
    """Manages Hugo development server operations."""

    def __init__(self, blog_path: Optional[Path] = None):
        """Initialize Hugo server manager.

        Args:
            blog_path: Path to the Hugo blog directory.
                If None, will use current working directory.
        """
        self.blog_path = blog_path or Path.cwd()
        self.process: Optional[subprocess.Popen] = None
        self.default_port = 1313
        self.default_host = "localhost"

    def start_server(self, port: int = None, host: str = None) -> Tuple[bool, str]:
        """Start the Hugo development server.

        Args:
            port: Port to run server on (default: 1313)
            host: Host to bind server to (default: localhost)

        Returns:
            Tuple of (success: bool, message: str)
        """
        if self.is_running():
            return False, "Hugo server is already running"

        port = port or self.default_port
        host = host or self.default_host

        try:
            # Start Hugo server process
            self.process = subprocess.Popen(
                [
                    "hugo",
                    "server",
                    "--bind",
                    host,
                    "--port",
                    str(port),
                    "--buildDrafts",
                    "--buildFuture",
                    "--disableFastRender",
                ],
                cwd=self.blog_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait a moment for server to start
            time.sleep(2)

            # Check if server is actually running
            if self.process.poll() is not None:
                # Process has terminated
                stdout, stderr = self.process.communicate()
                self.process = None
                return False, f"Hugo server failed to start: {stderr or stdout}"

            # Verify server is responding
            server_url = f"http://{host}:{port}"
            if self._check_server_response(server_url):
                self.default_port = port
                self.default_host = host
                return True, f"Hugo server started successfully at {server_url}"
            else:
                # Server process is running but not responding
                self.stop_server()
                return False, "Hugo server started but is not responding"

        except FileNotFoundError:
            return False, "Hugo command not found. Please ensure Hugo is installed and in PATH."
        except Exception as e:
            return False, f"Failed to start Hugo server: {e}"

    def stop_server(self) -> Tuple[bool, str]:
        """Stop the Hugo development server.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_running():
            return False, "Hugo server is not running"

        try:
            # Terminate the process
            self.process.terminate()

            # Wait for process to terminate gracefully
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate gracefully
                self.process.kill()
                self.process.wait(timeout=2)

            self.process = None
            return True, "Hugo server stopped successfully"

        except Exception as e:
            return False, f"Failed to stop Hugo server: {e}"

    def restart_server(self, port: int = None, host: str = None) -> Tuple[bool, str]:
        """Restart the Hugo development server.

        Args:
            port: Port to run server on (default: current port)
            host: Host to bind server to (default: current host)

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Stop current server if running
        if self.is_running():
            stop_success, stop_message = self.stop_server()
            if not stop_success:
                return False, f"Failed to stop server for restart: {stop_message}"

        # Start server with new parameters
        return self.start_server(port or self.default_port, host or self.default_host)

    def is_running(self) -> bool:
        """Check if Hugo server is currently running.

        Returns:
            True if server is running, False otherwise.
        """
        if self.process is None:
            return False

        # Check if process is still alive
        if self.process.poll() is not None:
            # Process has terminated
            self.process = None
            return False

        return True

    def get_status(self) -> ServerStatus:
        """Get current server status.

        Returns:
            ServerStatus object with current server information.
        """
        if not self.is_running():
            return ServerStatus(
                is_running=False,
                url="",
                port=0,
                process_id=None,
            )

        url = f"http://{self.default_host}:{self.default_port}"
        return ServerStatus(
            is_running=True,
            url=url,
            port=self.default_port,
            process_id=self.process.pid if self.process else None,
        )

    def get_server_url(self) -> str:
        """Get the current server URL.

        Returns:
            Server URL string, or empty string if not running.
        """
        status = self.get_status()
        return status.url if status.is_running else ""

    def _check_server_response(self, url: str, timeout: int = 5) -> bool:
        """Check if server is responding at the given URL.

        Args:
            url: URL to check
            timeout: Request timeout in seconds

        Returns:
            True if server responds, False otherwise.
        """
        try:
            response = requests.get(url, timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False

    def cleanup(self):
        """Clean up resources when manager is destroyed."""
        if self.is_running():
            self.stop_server()
