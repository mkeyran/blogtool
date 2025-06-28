"""Integration tests for real Hugo operations."""

import pytest

from blogtool.core.hugo import HugoManager


class TestRealHugoIntegration:
    """Integration tests with real Hugo blog."""

    @pytest.fixture
    def temp_micropost_name(self):
        """Generate a temporary micropost filename for testing."""
        import uuid
        from datetime import datetime

        current_date = datetime.now().strftime("%Y-%m-%d")
        test_uuid = str(uuid.uuid4())[:8]
        return f"{current_date}-test-{test_uuid}.md"

    def test_hugo_manager_finds_real_blog(self):
        """Test that HugoManager can find the real blog."""
        manager = HugoManager()

        # Should find the playground or sibling blog
        assert manager.is_blog_available()
        assert manager.blog_path is not None
        assert manager.blog_path.name in ["playground", "mkeyran.github.io"]

    @pytest.mark.integration
    def test_create_real_micropost(self, temp_micropost_name):
        """Test creating a real micropost file.

        Note: This test creates an actual file in the Hugo blog.
        Use with caution and clean up afterwards.
        """
        manager = HugoManager()

        if not manager.is_blog_available():
            pytest.skip("Hugo blog not available for integration testing")

        test_content = (
            f"This is a test micropost created during automated testing.\n\n"
            f"Filename: {temp_micropost_name}"
        )

        # Create the micropost
        success, message = manager.create_micropost(
            temp_micropost_name, test_content
        )

        # Verify creation
        assert success, f"Failed to create micropost: {message}"
        assert "successfully" in message.lower()

        # Verify file exists in the correct location
        expected_file = (
            manager.blog_path / "content" / "microposts" / temp_micropost_name
        )
        assert expected_file.exists(), (
            f"Micropost file not found: {expected_file}"
        )

        # Verify content
        content = expected_file.read_text(encoding="utf-8")
        assert test_content in content
        assert "date:" in content  # Front matter should be present
        assert "draft: false" in content

        # Clean up - remove the test file
        try:
            expected_file.unlink()
        except Exception as e:
            print(
                f"Warning: Could not clean up test file {expected_file}: {e}"
            )

    def test_micropost_front_matter_format(self):
        """Test that generated microposts have correct front matter format."""
        manager = HugoManager()

        if not manager.is_blog_available():
            pytest.skip("Hugo blog not available for integration testing")

        # Check existing micropost to understand format
        microposts_dir = manager.blog_path / "content" / "microposts"
        existing_microposts = list(microposts_dir.glob("*.md"))

        # Filter out index and non-date files
        date_microposts = [
            f
            for f in existing_microposts
            if f.name != "_index.md" and f.name.startswith("2025-")
        ]

        assert len(date_microposts) > 0, (
            "No existing microposts found to verify format"
        )

        # Read an existing micropost to check format
        sample_micropost = date_microposts[0]
        content = sample_micropost.read_text(encoding="utf-8")

        # Verify expected front matter structure
        assert content.startswith("---\n")
        assert "date:" in content
        assert "draft:" in content
        assert "description:" in content

        # Check date format (should be ISO 8601 with timezone)
        lines = content.split("\n")
        date_line = next(line for line in lines if line.startswith("date:"))
        assert "T" in date_line  # ISO 8601 format
        assert "+" in date_line or "Z" in date_line  # Timezone info
