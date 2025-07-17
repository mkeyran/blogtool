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


@dataclass
class ContentInfo:
    """Information about any Hugo content item."""

    filename: str
    title: str
    date: datetime
    file_path: Path
    preview: str
    content_type: str  # "post", "conversation", "micropost"
    language: str  # "en", "ru", "pl"
    slug: str
    description: str
    tags: List[str]
    keywords: List[str]
    is_draft: bool


class HugoManager:
    """Manages Hugo CLI operations."""

    def __init__(self, blog_path: Optional[str] = None):
        """Initialize Hugo manager.

        Args:
            blog_path: Path to Hugo blog root. If None, will use settings or auto-detect.
        """
        if blog_path:
            self.blog_path = Path(blog_path) if self._is_hugo_site(Path(blog_path)) else None
        else:
            # Use settings system for blog path
            from .settings import get_settings

            settings = get_settings()
            configured_path = settings.get_blog_path()
            self.blog_path = Path(configured_path) if configured_path else None
        
        # Get Hugo executable from settings
        from .settings import get_settings
        settings = get_settings()
        self.hugo_cmd = settings.get_hugo_executable()
        
        # Set up environment with proper PATH
        self.env = self._setup_environment(settings)

    def _setup_environment(self, settings) -> dict:
        """Set up environment variables with proper PATH for Hugo and Go."""
        import os
        
        # Start with current environment
        env = os.environ.copy()
        
        # Get configured paths
        go_path = settings.get_go_executable()
        hugo_path = settings.get_hugo_executable()
        
        # Build PATH components
        path_components = []
        
        # Add Go binary directory to PATH if we have it
        if go_path and go_path != "go":  # If not just "go" (meaning it's a full path)
            go_dir = str(Path(go_path).parent)
            path_components.append(go_dir)
        
        # Add Hugo binary directory to PATH if we have it
        if hugo_path and hugo_path != "hugo":  # If not just "hugo" (meaning it's a full path)
            hugo_dir = str(Path(hugo_path).parent)
            path_components.append(hugo_dir)
        
        # Add common binary directories
        common_dirs = [
            "/opt/homebrew/bin",
            "/usr/local/bin",
            "/usr/local/go/bin",
            "/usr/bin",
        ]
        path_components.extend(common_dirs)
        
        # Add original PATH
        if "PATH" in env:
            path_components.append(env["PATH"])
        
        # Set the new PATH
        env["PATH"] = ":".join(path_components)
        
        return env

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
        
        if not self.hugo_cmd:
            return False, "Hugo executable not found. Please ensure Hugo is installed and accessible."

        try:
            # Create micropost using Hugo CLI with explicit content path
            micropost_path = f"content/microposts/{filename}"

            # Run hugo new content command
            cmd = [
                self.hugo_cmd,
                "new",
                "content",
                micropost_path,
                "--kind",
                "micropost",
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.blog_path,
                capture_output=True,
                text=True,
                timeout=30,
                env=self.env,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                if not error_msg:
                    error_msg = f"Hugo command returned code {result.returncode} with no output"
                debug_info = f"Command: {' '.join(cmd)}\nWorking directory: {self.blog_path}\nReturn code: {result.returncode}"
                return False, f"Hugo command failed: {error_msg}\n\nDebug info:\n{debug_info}"

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

    def list_all_content(self) -> List[ContentInfo]:
        """List all content items (posts, conversations, microposts) across all languages.

        Returns:
            List of ContentInfo objects sorted by date (newest first).
        """
        if not self.blog_path:
            return []

        all_content = []

        # Add microposts (language-agnostic)
        microposts = self.list_microposts()
        for micropost in microposts:
            # Try to extract title from front matter for consistency
            micropost_title = micropost.title
            try:
                with open(micropost.file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        front_matter = parts[1]
                        title_match = re.search(r"title:\s*['\"]([^'\"]+)['\"]", front_matter)
                        if title_match:
                            micropost_title = title_match.group(1)
            except Exception:
                pass  # Keep original title if parsing fails

            # Extract draft status from micropost front matter
            is_draft = False
            try:
                with open(micropost.file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        front_matter = parts[1]
                        draft_match = re.search(r"draft:\s*(true|false)", front_matter)
                        if draft_match:
                            is_draft = draft_match.group(1).lower() == "true"
            except Exception:
                pass  # Keep default draft status if parsing fails

            content_info = ContentInfo(
                filename=micropost.filename,
                title=micropost_title,
                date=micropost.date,
                file_path=micropost.file_path,
                preview=micropost.preview,
                content_type="micropost",
                language="en",  # Default for microposts
                slug=micropost.filename.replace(".md", ""),
                description="",
                tags=[],
                keywords=[],
                is_draft=is_draft,
            )
            all_content.append(content_info)

        # Add posts and conversations from each language
        language_map = {"en": "english", "ru": "russian", "pl": "polish"}

        for lang_code, lang_dir in language_map.items():
            content_base = self.blog_path / "content" / lang_dir

            # Add posts
            posts_dir = content_base / "posts"
            if posts_dir.exists():
                for post_dir in posts_dir.iterdir():
                    if post_dir.is_dir() and (post_dir / "index.md").exists():
                        content_info = self._parse_content_item(post_dir / "index.md", "post", lang_code, post_dir.name)
                        if content_info:
                            all_content.append(content_info)

            # Add conversations
            conversations_dir = content_base / "conversations"
            if conversations_dir.exists():
                for conv_dir in conversations_dir.iterdir():
                    if conv_dir.is_dir() and (conv_dir / "index.md").exists():
                        content_info = self._parse_content_item(
                            conv_dir / "index.md", "conversation", lang_code, conv_dir.name
                        )
                        if content_info:
                            all_content.append(content_info)

        # Sort by date, newest first
        all_content.sort(key=lambda c: c.date, reverse=True)
        return all_content

    def _parse_content_item(
        self, file_path: Path, content_type: str, language: str, slug: str
    ) -> Optional[ContentInfo]:
        """Parse a content item (post or conversation) to extract information.

        Args:
            file_path: Path to the content file.
            content_type: Type of content ("post" or "conversation").
            language: Language code.
            slug: URL slug for the content.

        Returns:
            ContentInfo object or None if parsing fails.
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

            # Extract fields from front matter
            date_match = re.search(r"date:\s*['\"]?([^'\"]+)['\"]?", front_matter)
            if not date_match:
                return None

            # Parse date
            date_str = date_match.group(1)
            try:
                if "T" in date_str:
                    date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                else:
                    date = datetime.fromisoformat(date_str)
            except ValueError:
                return None

            # Extract title
            title_match = re.search(r"title:\s*['\"]([^'\"]+)['\"]", front_matter)
            title = title_match.group(1) if title_match else slug.replace("-", " ").title()

            # Extract description
            desc_match = re.search(r"description:\s*['\"]([^'\"]*)['\"]", front_matter)
            description = desc_match.group(1) if desc_match else ""

            # Extract tags
            tags_match = re.search(r"tags:\s*\[([^\]]*)\]", front_matter)
            tags = []
            if tags_match:
                tags_str = tags_match.group(1)
                if tags_str:
                    tags = [tag.strip().strip("'\"") for tag in tags_str.split(",") if tag.strip()]

            # Extract keywords
            keywords_match = re.search(r"keywords:\s*\[([^\]]*)\]", front_matter)
            keywords = []
            if keywords_match:
                keywords_str = keywords_match.group(1)
                if keywords_str:
                    keywords = [kw.strip().strip("'\"") for kw in keywords_str.split(",") if kw.strip()]

            # Extract draft status
            draft_match = re.search(r"draft:\s*(true|false)", front_matter)
            is_draft = False
            if draft_match:
                is_draft = draft_match.group(1).lower() == "true"

            # Generate preview from body
            preview = self._generate_preview(body)

            return ContentInfo(
                filename=file_path.name,
                title=title,
                date=date,
                file_path=file_path,
                preview=preview,
                content_type=content_type,
                language=language,
                slug=slug,
                description=description,
                tags=tags,
                keywords=keywords,
                is_draft=is_draft,
            )

        except Exception:
            return None

    def create_post(
        self,
        title: str,
        slug: str,
        language: str,
        description: str = "",
        tags: List[str] = None,
        keywords: List[str] = None,
    ) -> Tuple[bool, str]:
        """Create a new blog post using Hugo CLI.

        Args:
            title: Title of the post
            slug: URL-friendly slug for the post
            language: Language code (en, ru, pl)
            description: Brief description of the post
            tags: List of tags
            keywords: List of keywords

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.blog_path:
            return False, "Hugo blog not found. Please check blog path."
        
        if not self.hugo_cmd:
            return False, "Hugo executable not found. Please ensure Hugo is installed and accessible."

        try:
            # Map language codes to content directories
            language_map = {"en": "english", "ru": "russian", "pl": "polish"}

            language_dir = language_map.get(language, "english")
            post_path = f"content/{language_dir}/posts/{slug}/index.md"

            # Run hugo new content command
            result = subprocess.run(
                [
                    self.hugo_cmd,
                    "new",
                    "content",
                    post_path,
                ],
                cwd=self.blog_path,
                capture_output=True,
                text=True,
                timeout=30,
                env=self.env,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                if not error_msg:
                    error_msg = f"Hugo command returned code {result.returncode} with no output"
                return False, f"Hugo command failed: {error_msg}"

            # Path to the created file
            created_file = self.blog_path / "content" / language_dir / "posts" / slug / "index.md"

            if not created_file.exists():
                return False, f"File was not created: {created_file}"

            # Update the front matter with provided data
            self._update_post_front_matter(created_file, title, description, tags or [], keywords or [])

            return True, f"Post created successfully: {post_path}"

        except subprocess.TimeoutExpired:
            return False, "Hugo command timed out"
        except subprocess.CalledProcessError as e:
            return False, f"Hugo command failed: {e}"
        except Exception as e:
            return False, f"Error creating post: {e}"

    def create_conversation(
        self,
        title: str,
        slug: str,
        language: str,
        description: str = "",
        tags: List[str] = None,
        keywords: List[str] = None,
    ) -> Tuple[bool, str]:
        """Create a new conversation using Hugo CLI.

        Args:
            title: Title of the conversation
            slug: URL-friendly slug for the conversation
            language: Language code (en, ru, pl)
            description: Brief description of the conversation
            tags: List of tags
            keywords: List of keywords

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.blog_path:
            return False, "Hugo blog not found. Please check blog path."
        
        if not self.hugo_cmd:
            return False, "Hugo executable not found. Please ensure Hugo is installed and accessible."

        try:
            # Map language codes to content directories
            language_map = {"en": "english", "ru": "russian", "pl": "polish"}

            language_dir = language_map.get(language, "english")
            conversation_path = f"content/{language_dir}/conversations/{slug}/index.md"

            # Run hugo new content command with conversations archetype
            result = subprocess.run(
                [
                    self.hugo_cmd,
                    "new",
                    "content",
                    conversation_path,
                    "--kind",
                    "conversations",
                ],
                cwd=self.blog_path,
                capture_output=True,
                text=True,
                timeout=30,
                env=self.env,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                if not error_msg:
                    error_msg = f"Hugo command returned code {result.returncode} with no output"
                return False, f"Hugo command failed: {error_msg}"

            # Path to the created file
            created_file = self.blog_path / "content" / language_dir / "conversations" / slug / "index.md"

            if not created_file.exists():
                return False, f"File was not created: {created_file}"

            # Update the front matter with provided data
            self._update_post_front_matter(created_file, title, description, tags or [], keywords or [])

            return True, f"Conversation created successfully: {conversation_path}"

        except subprocess.TimeoutExpired:
            return False, "Hugo command timed out"
        except subprocess.CalledProcessError as e:
            return False, f"Hugo command failed: {e}"
        except Exception as e:
            return False, f"Error creating conversation: {e}"

    def _update_post_front_matter(
        self, file_path: Path, title: str, description: str, tags: List[str], keywords: List[str]
    ) -> None:
        """Update the front matter of a created post with provided data.

        Args:
            file_path: Path to the post file
            title: Title to set
            description: Description to set
            tags: List of tags
            keywords: List of keywords
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split front matter and body
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                front_matter = parts[1]
                body = parts[2] if len(parts) > 2 else ""

                # Update front matter fields
                front_matter = re.sub(r"title:\s*['\"]?[^'\"]*['\"]?", f"title: '{title}'", front_matter)
                front_matter = re.sub(
                    r"description:\s*['\"]?[^'\"]*['\"]?", f"description: '{description}'", front_matter
                )

                # Format tags and keywords as YAML arrays
                tags_yaml = str(tags) if tags else "[]"
                keywords_yaml = str(keywords) if keywords else "[]"

                front_matter = re.sub(r"tags:\s*\[.*?\]", f"tags: {tags_yaml}", front_matter)
                front_matter = re.sub(r"keywords:\s*\[.*?\]", f"keywords: {keywords_yaml}", front_matter)

                # Reconstruct content
                new_content = f"---{front_matter}---{body}"

                # Write back to file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
