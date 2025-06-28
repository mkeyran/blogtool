"""Tests for Hugo CLI integration."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from blogtool.core.hugo import HugoManager


class TestHugoManager:
    """Test cases for HugoManager."""

    def test_init_with_provided_path(self):
        """Test initialization with provided path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create mock Hugo site structure
            (temp_path / "hugo.toml").touch()
            (temp_path / "content").mkdir()

            manager = HugoManager(str(temp_path))
            assert manager.blog_path == temp_path
            assert manager.is_blog_available()

    def test_init_without_path_finds_sibling(self):
        """Test initialization finds sibling blog directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create sibling blog directory
            sibling_blog = temp_path / "mkeyran.github.io"
            sibling_blog.mkdir()
            (sibling_blog / "hugo.toml").touch()
            (sibling_blog / "content").mkdir()

            with patch("pathlib.Path.cwd", return_value=temp_path / "blogtool"):
                manager = HugoManager()
                assert manager.blog_path == sibling_blog
                assert manager.is_blog_available()

    def test_is_hugo_site_valid(self):
        """Test Hugo site detection with valid site."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create Hugo site structure
            (temp_path / "config.toml").touch()
            (temp_path / "content").mkdir()

            manager = HugoManager()
            assert manager._is_hugo_site(temp_path)

    def test_is_hugo_site_invalid(self):
        """Test Hugo site detection with invalid site."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Missing content directory
            (temp_path / "hugo.toml").touch()

            manager = HugoManager()
            assert not manager._is_hugo_site(temp_path)

    @patch("subprocess.run")
    def test_create_micropost_success(self, mock_run):
        """Test successful micropost creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Setup Hugo site
            (temp_path / "hugo.toml").touch()
            content_dir = temp_path / "content"
            content_dir.mkdir()
            microposts_dir = content_dir / "microposts"
            microposts_dir.mkdir()

            # Mock successful hugo command
            mock_run.return_value = Mock(returncode=0, stderr="")

            # Create mock file that hugo would create
            test_file = microposts_dir / "2025-06-28-test.md"
            test_file.write_text(
                "---\n" "date: '2025-06-28T10:00:00+02:00'\n" "draft: false\n" "description: ''\n" "---\n"
            )

            manager = HugoManager(str(temp_path))
            success, message = manager.create_micropost("2025-06-28-test.md", "Test content")

            assert success
            assert "successfully" in message

            # Verify hugo command was called correctly
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[0][0] == [
                "hugo",
                "new",
                "content",
                "content/microposts/2025-06-28-test.md",
                "--kind",
                "micropost",
            ]
            assert call_args[1]["cwd"] == temp_path

            # Verify content was written
            final_content = test_file.read_text()
            assert "Test content" in final_content

    @patch("subprocess.run")
    def test_create_micropost_hugo_command_fails(self, mock_run):
        """Test micropost creation when Hugo command fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Setup Hugo site
            (temp_path / "hugo.toml").touch()
            (temp_path / "content").mkdir()

            # Mock failed hugo command
            mock_run.return_value = Mock(returncode=1, stderr="Hugo error")

            manager = HugoManager(str(temp_path))
            success, message = manager.create_micropost("2025-06-28-test.md", "Test content")

            assert not success
            assert "Hugo command failed" in message
            assert "Hugo error" in message

    @patch("pathlib.Path.cwd")
    def test_create_micropost_no_blog(self, mock_cwd):
        """Test micropost creation when no blog is available."""
        # Mock current directory to be somewhere without a sibling blog
        mock_cwd.return_value = Path("/tmp/nonexistent")

        manager = HugoManager("/nonexistent/path")
        success, message = manager.create_micropost("test.md", "content")

        assert not success
        assert "Hugo blog not found" in message
