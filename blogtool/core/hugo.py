"""Hugo CLI integration for blog management."""

import subprocess
from pathlib import Path
from typing import Optional, Tuple


class HugoManager:
    """Manages Hugo CLI operations."""

    def __init__(self, blog_path: Optional[str] = None):
        """Initialize Hugo manager.

        Args:
            blog_path: Path to Hugo blog root. If None, will search for blog.
        """
        self.blog_path = self._find_blog_path(blog_path)

    def _find_blog_path(self, provided_path: Optional[str]) -> Optional[Path]:
        """Find Hugo blog path."""
        if provided_path:
            path = Path(provided_path)
            if self._is_hugo_site(path):
                return path

        current_dir = Path.cwd()

        # Look in playground directory (for testing)
        playground_blog = current_dir / "playground"
        if self._is_hugo_site(playground_blog):
            return playground_blog

        # Look in sibling directory as mentioned in requirements
        sibling_blog = current_dir.parent / "mkeyran.github.io"
        if self._is_hugo_site(sibling_blog):
            return sibling_blog

        return None

    def _is_hugo_site(self, path: Path) -> bool:
        """Check if path contains a Hugo site."""
        if not path.exists():
            return False

        # Check for Hugo config files
        config_files = [
            "hugo.toml",
            "hugo.yaml",
            "hugo.yml",
            "config.toml",
            "config.yaml",
            "config.yml",
        ]
        has_config = any((path / config).exists() for config in config_files)

        # Check for content directory
        has_content = (path / "content").exists()

        return has_config and has_content

    def create_micropost(
        self, filename: str, content: str
    ) -> Tuple[bool, str]:
        """Create a new micropost using Hugo CLI.

        Args:
            filename: Name of the micropost file
                (e.g., "2025-06-28-example.md")
            content: Content for the micropost

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.blog_path:
            return False, "Hugo blog not found. Please check blog path."

        try:
            # Create micropost using Hugo CLI with explicit content path
            micropost_path = f"content/microposts/{filename}"

            # Run hugo new content command
            result = subprocess.run(
                [
                    "hugo",
                    "new",
                    "content",
                    micropost_path,
                    "--kind",
                    "micropost",
                ],
                cwd=self.blog_path,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return False, f"Hugo command failed: {result.stderr}"

            # Path to the created file
            created_file = self.blog_path / "content" / "microposts" / filename

            if not created_file.exists():
                return False, f"File was not created: {created_file}"

            # Read the generated content
            with open(created_file, "r", encoding="utf-8") as f:
                file_content = f.read()

            # Find where the content starts (after the front matter)
            if "---" in file_content:
                parts = file_content.split("---", 2)
                if len(parts) >= 3:
                    front_matter = parts[1]
                    # Reconstruct with our content
                    new_content = f"---{front_matter}---\n\n{content}\n"
                else:
                    # Fallback if parsing fails
                    new_content = file_content + f"\n\n{content}\n"
            else:
                # No front matter found, just append content
                new_content = file_content + f"\n\n{content}\n"

            # Write the updated content
            with open(created_file, "w", encoding="utf-8") as f:
                f.write(new_content)

            return True, f"Micropost created successfully: {micropost_path}"

        except subprocess.TimeoutExpired:
            return False, "Hugo command timed out"
        except subprocess.CalledProcessError as e:
            return False, f"Hugo command failed: {e}"
        except Exception as e:
            return False, f"Error creating micropost: {e}"

    def get_blog_path(self) -> Optional[Path]:
        """Get the current blog path."""
        return self.blog_path

    def is_blog_available(self) -> bool:
        """Check if Hugo blog is available."""
        return self.blog_path is not None
