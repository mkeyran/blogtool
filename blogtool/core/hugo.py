"""Hugo CLI integration for blog management."""

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class MicropostInfo:
    """Information about a micropost."""

    filename: str
    title: str
    date: datetime
    file_path: Path
    preview: str


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

    def create_micropost(self, filename: str, content: str) -> Tuple[bool, str]:
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

    def list_microposts(self) -> List[MicropostInfo]:
        """List all microposts in the blog.

        Returns:
            List of MicropostInfo objects sorted by date (newest first).
        """
        if not self.blog_path:
            return []

        microposts_dir = self.blog_path / "content" / "microposts"
        if not microposts_dir.exists():
            return []

        microposts = []
        for md_file in microposts_dir.glob("*.md"):
            if md_file.name == "_index.md":
                continue

            try:
                micropost_info = self._parse_micropost(md_file)
                if micropost_info:
                    microposts.append(micropost_info)
            except Exception:
                # Skip files that can't be parsed
                continue

        # Sort by date, newest first
        microposts.sort(key=lambda m: m.date, reverse=True)
        return microposts

    def _parse_micropost(self, file_path: Path) -> Optional[MicropostInfo]:
        """Parse a micropost file to extract information.

        Args:
            file_path: Path to the micropost file.

        Returns:
            MicropostInfo object or None if parsing fails.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract front matter
            if not content.startswith("---"):
                return None

            parts = content.split("---", 2)
            if len(parts) < 3:
                return None

            front_matter = parts[1]
            body = parts[2].strip()

            # Extract date from front matter
            date_match = re.search(r"date:\s*['\"]?([^'\"]+)['\"]?", front_matter)
            if not date_match:
                return None

            # Parse date
            date_str = date_match.group(1)
            try:
                # Handle various date formats
                if "T" in date_str:
                    # ISO format with time
                    date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                else:
                    # Simple date format
                    date = datetime.fromisoformat(date_str)
            except ValueError:
                return None

            # Generate title from filename or content
            filename = file_path.name
            title = self._generate_title(filename, body)

            # Generate preview from body
            preview = self._generate_preview(body)

            return MicropostInfo(
                filename=filename,
                title=title,
                date=date,
                file_path=file_path,
                preview=preview,
            )

        except Exception:
            return None

    def _generate_title(self, filename: str, body: str) -> str:
        """Generate a title for the micropost.

        Args:
            filename: The filename of the micropost.
            body: The body content of the micropost.

        Returns:
            Generated title string.
        """
        # Try to extract title from first line of content
        first_line = body.split("\n")[0].strip() if body else ""

        # If first line looks like a title (not a URL, not too long)
        if first_line and not first_line.startswith("http") and len(first_line) < 100:
            # Remove markdown formatting
            title = re.sub(r"[#*_`\[\]]", "", first_line).strip()
            if title:
                return title

        # Fallback: use filename without extension and generate readable title
        base_name = filename.replace(".md", "")
        # Remove date prefix if present
        title_part = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", base_name)
        # Replace hyphens with spaces and title case
        return title_part.replace("-", " ").title()

    def _generate_preview(self, body: str) -> str:
        """Generate a preview from the micropost body.

        Args:
            body: The body content of the micropost.

        Returns:
            Preview string (first ~150 characters).
        """
        if not body:
            return ""

        # Remove markdown formatting for preview
        preview = re.sub(r"[#*_`]", "", body)
        # Replace multiple whitespace with single space
        preview = re.sub(r"\s+", " ", preview).strip()

        # Truncate to reasonable length
        max_length = 150
        if len(preview) > max_length:
            preview = preview[:max_length].rsplit(" ", 1)[0] + "..."

        return preview
