"""Tests for Hugo micropost listing functionality."""

import tempfile
from datetime import datetime
from pathlib import Path

from blogtool.core.hugo import HugoManager


class TestHugoMicropostListing:
    """Test Hugo micropost listing functionality."""

    def test_list_microposts_no_blog(self):
        """Test listing microposts when no blog is available."""
        # Use a path that definitely doesn't exist and isn't detected as a blog
        manager = HugoManager()
        manager.blog_path = None  # Force no blog
        microposts = manager.list_microposts()
        assert microposts == []

    def test_list_microposts_no_microposts_dir(self):
        """Test listing when microposts directory doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create Hugo site without microposts directory
            (temp_path / "hugo.toml").touch()
            (temp_path / "content").mkdir()

            manager = HugoManager(str(temp_path))
            microposts = manager.list_microposts()
            assert microposts == []

    def test_list_microposts_empty_directory(self):
        """Test listing when microposts directory is empty."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create Hugo site with empty microposts directory
            (temp_path / "hugo.toml").touch()
            content_dir = temp_path / "content"
            content_dir.mkdir()
            microposts_dir = content_dir / "microposts"
            microposts_dir.mkdir()

            # Create only _index.md (should be ignored)
            (microposts_dir / "_index.md").write_text("---\ntitle: Microposts\n---\n")

            manager = HugoManager(str(temp_path))
            microposts = manager.list_microposts()
            assert microposts == []

    def test_list_microposts_with_content(self):
        """Test listing microposts with actual content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create Hugo site structure
            (temp_path / "hugo.toml").touch()
            content_dir = temp_path / "content"
            content_dir.mkdir()
            microposts_dir = content_dir / "microposts"
            microposts_dir.mkdir()

            # Create test microposts
            micropost1 = microposts_dir / "2025-06-28-test-1.md"
            micropost1.write_text(
                "---\n"
                "date: '2025-06-28T10:30:00+02:00'\n"
                "draft: false\n"
                "description: ''\n"
                "---\n\n"
                "# Test Title 1\n\n"
                "This is the first test micropost content."
            )

            micropost2 = microposts_dir / "2025-06-27-test-2.md"
            micropost2.write_text(
                "---\n"
                "date: '2025-06-27T15:45:00+02:00'\n"
                "draft: false\n"
                "description: ''\n"
                "---\n\n"
                "This is a micropost without a title.\n\n"
                "It has multiple lines of content."
            )

            manager = HugoManager(str(temp_path))
            microposts = manager.list_microposts()

            # Should have 2 microposts
            assert len(microposts) == 2

            # Should be sorted by date (newest first)
            assert microposts[0].filename == "2025-06-28-test-1.md"
            assert microposts[1].filename == "2025-06-27-test-2.md"

            # Check first micropost details
            mp1 = microposts[0]
            assert mp1.title == "Test Title 1"
            assert mp1.date == datetime(2025, 6, 28, 10, 30, tzinfo=mp1.date.tzinfo)
            assert mp1.file_path == micropost1
            assert "first test micropost" in mp1.preview

            # Check second micropost details
            mp2 = microposts[1]
            assert mp2.title == "This is a micropost without a title."  # Generated from first line
            assert mp2.date == datetime(2025, 6, 27, 15, 45, tzinfo=mp2.date.tzinfo)
            assert mp2.file_path == micropost2
            assert "micropost without a title" in mp2.preview

    def test_parse_micropost_invalid_format(self):
        """Test parsing micropost with invalid format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "hugo.toml").touch()
            content_dir = temp_path / "content"
            content_dir.mkdir()
            microposts_dir = content_dir / "microposts"
            microposts_dir.mkdir()

            # Create invalid micropost (no front matter)
            invalid_micropost = microposts_dir / "invalid.md"
            invalid_micropost.write_text("This is just content without front matter")

            manager = HugoManager(str(temp_path))
            result = manager._parse_micropost(invalid_micropost)
            assert result is None

    def test_parse_micropost_no_date(self):
        """Test parsing micropost without date in front matter."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "hugo.toml").touch()
            content_dir = temp_path / "content"
            content_dir.mkdir()
            microposts_dir = content_dir / "microposts"
            microposts_dir.mkdir()

            # Create micropost without date
            no_date_micropost = microposts_dir / "no-date.md"
            no_date_micropost.write_text("---\n" "draft: false\n" "description: ''\n" "---\n\n" "Content without date")

            manager = HugoManager(str(temp_path))
            result = manager._parse_micropost(no_date_micropost)
            assert result is None

    def test_generate_title_from_content(self):
        """Test title generation from content."""
        manager = HugoManager()

        # Test with clear title in content
        body = "# This is a Title\n\nSome content here"
        title = manager._generate_title("test.md", body)
        assert title == "This is a Title"

        # Test with URL as first line (should fallback to filename)
        body = "https://example.com/article\n\nDescription of the link"
        title = manager._generate_title("2025-06-28-interesting-article.md", body)
        assert title == "Interesting Article"

        # Test with long first line (should fallback to filename)
        body = (
            "This is a very long first line that exceeds 100 characters and should not be used as title "
            "because it's too long"
        )
        title = manager._generate_title("2025-06-28-short-title.md", body)
        assert title == "Short Title"

        # Test with empty content
        body = ""
        title = manager._generate_title("2025-06-28-fallback-title.md", body)
        assert title == "Fallback Title"

    def test_generate_preview(self):
        """Test preview generation."""
        manager = HugoManager()

        # Test normal content
        body = "This is some content that should be used for preview generation."
        preview = manager._generate_preview(body)
        assert preview == "This is some content that should be used for preview generation."

        # Test long content (should be truncated)
        long_body = "This is a very long piece of content " * 10
        preview = manager._generate_preview(long_body)
        assert len(preview) <= 153  # 150 + "..."
        assert preview.endswith("...")

        # Test content with markdown formatting
        body = "This is **bold** text with *italic* and `code` formatting."
        preview = manager._generate_preview(body)
        assert "**" not in preview
        assert "*" not in preview
        assert "`" not in preview

        # Test empty content
        preview = manager._generate_preview("")
        assert preview == ""

    def test_list_microposts_sorting(self):
        """Test that microposts are sorted by date (newest first)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create Hugo site structure
            (temp_path / "hugo.toml").touch()
            content_dir = temp_path / "content"
            content_dir.mkdir()
            microposts_dir = content_dir / "microposts"
            microposts_dir.mkdir()

            # Create microposts with different dates
            dates_and_files = [
                ("2025-06-25T10:00:00+02:00", "2025-06-25-oldest.md"),
                ("2025-06-28T10:00:00+02:00", "2025-06-28-newest.md"),
                ("2025-06-26T10:00:00+02:00", "2025-06-26-middle.md"),
            ]

            for date_str, filename in dates_and_files:
                micropost = microposts_dir / filename
                micropost.write_text(
                    f"---\n" f"date: '{date_str}'\n" f"draft: false\n" f"---\n\n" f"Content for {filename}"
                )

            manager = HugoManager(str(temp_path))
            microposts = manager.list_microposts()

            # Should be sorted newest first
            assert len(microposts) == 3
            assert microposts[0].filename == "2025-06-28-newest.md"
            assert microposts[1].filename == "2025-06-26-middle.md"
            assert microposts[2].filename == "2025-06-25-oldest.md"
