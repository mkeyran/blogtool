"""Tests for Hugo content listing functionality."""

import tempfile
from pathlib import Path

from blogtool.core.hugo import HugoManager


class TestHugoContentListing:
    """Test Hugo content listing methods."""

    def test_list_all_content_empty_blog(self):
        """Test listing content when blog has no content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Setup empty Hugo site structure
            (temp_path / "hugo.yaml").touch()
            (temp_path / "content").mkdir()

            manager = HugoManager(str(temp_path))
            content = manager.list_all_content()

            assert content == []

    def test_list_all_content_with_microposts_only(self):
        """Test listing content with only microposts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Setup Hugo site structure
            (temp_path / "hugo.yaml").touch()
            content_dir = temp_path / "content"
            content_dir.mkdir()
            microposts_dir = content_dir / "microposts"
            microposts_dir.mkdir()

            # Create a micropost
            micropost_file = microposts_dir / "2025-06-29-test.md"
            micropost_file.write_text(
                "---\n"
                "date: '2025-06-29T10:00:00+02:00'\n"
                "draft: false\n"
                "title: 'Test Micropost'\n"
                "---\n\n"
                "This is a test micropost.\n"
            )

            manager = HugoManager(str(temp_path))
            content = manager.list_all_content()

            assert len(content) == 1
            assert content[0].content_type == "micropost"
            assert content[0].title == "Test Micropost"
            assert content[0].language == "en"

    def test_list_all_content_with_posts_and_conversations(self):
        """Test listing content with posts and conversations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Setup Hugo site structure
            (temp_path / "hugo.yaml").touch()
            content_dir = temp_path / "content"
            content_dir.mkdir()

            # Create English content structure
            english_dir = content_dir / "english"
            english_dir.mkdir()

            # Create a post
            posts_dir = english_dir / "posts"
            posts_dir.mkdir()
            post_dir = posts_dir / "test-post"
            post_dir.mkdir()
            post_file = post_dir / "index.md"
            post_file.write_text(
                "---\n"
                "date: '2025-06-29T10:00:00+02:00'\n"
                "draft: false\n"
                "title: 'Test Post'\n"
                "description: 'A test post'\n"
                "tags: ['test', 'blog']\n"
                "keywords: ['testing']\n"
                "---\n\n"
                "This is a test post.\n"
            )

            # Create a conversation
            conversations_dir = english_dir / "conversations"
            conversations_dir.mkdir()
            conv_dir = conversations_dir / "test-conversation"
            conv_dir.mkdir()
            conv_file = conv_dir / "index.md"
            conv_file.write_text(
                "---\n"
                "date: '2025-06-28T15:00:00+02:00'\n"
                "draft: false\n"
                "title: 'Test Conversation'\n"
                "description: 'A test conversation'\n"
                "tags: ['interview']\n"
                "keywords: ['conversation']\n"
                "---\n\n"
                "This is a test conversation.\n"
            )

            manager = HugoManager(str(temp_path))
            content = manager.list_all_content()

            assert len(content) == 2

            # Check post
            post_content = next(c for c in content if c.content_type == "post")
            assert post_content.title == "Test Post"
            assert post_content.language == "en"
            assert post_content.slug == "test-post"
            assert post_content.description == "A test post"
            assert post_content.tags == ["test", "blog"]
            assert post_content.keywords == ["testing"]

            # Check conversation
            conv_content = next(c for c in content if c.content_type == "conversation")
            assert conv_content.title == "Test Conversation"
            assert conv_content.language == "en"
            assert conv_content.slug == "test-conversation"
            assert conv_content.description == "A test conversation"
            assert conv_content.tags == ["interview"]
            assert conv_content.keywords == ["conversation"]

    def test_list_all_content_multiple_languages(self):
        """Test listing content across multiple languages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Setup Hugo site structure
            (temp_path / "hugo.yaml").touch()
            content_dir = temp_path / "content"
            content_dir.mkdir()

            # Create content in multiple languages
            for lang_code, lang_dir in [("en", "english"), ("ru", "russian"), ("pl", "polish")]:
                lang_path = content_dir / lang_dir
                lang_path.mkdir()

                posts_dir = lang_path / "posts"
                posts_dir.mkdir()
                post_dir = posts_dir / f"{lang_code}-post"
                post_dir.mkdir()
                post_file = post_dir / "index.md"
                post_file.write_text(
                    f"---\n"
                    f"date: '2025-06-29T10:00:00+02:00'\n"
                    f"draft: false\n"
                    f"title: '{lang_code.upper()} Post'\n"
                    f"description: 'A {lang_code} post'\n"
                    f"tags: ['{lang_code}']\n"
                    f"keywords: ['{lang_code}']\n"
                    f"---\n\n"
                    f"This is a {lang_code} post.\n"
                )

            manager = HugoManager(str(temp_path))
            content = manager.list_all_content()

            assert len(content) == 3

            # Check each language
            en_content = next(c for c in content if c.language == "en")
            assert en_content.title == "EN Post"
            assert en_content.slug == "en-post"

            ru_content = next(c for c in content if c.language == "ru")
            assert ru_content.title == "RU Post"
            assert ru_content.slug == "ru-post"

            pl_content = next(c for c in content if c.language == "pl")
            assert pl_content.title == "PL Post"
            assert pl_content.slug == "pl-post"

    def test_parse_content_item_with_tags_and_keywords(self):
        """Test parsing content with complex tags and keywords."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Setup Hugo site structure
            (temp_path / "hugo.yaml").touch()
            (temp_path / "content").mkdir()

            # Create a test file with complex front matter
            test_file = temp_path / "test.md"
            test_file.write_text(
                "---\n"
                "date: '2025-06-29T10:00:00+02:00'\n"
                "draft: false\n"
                "title: 'Complex Test'\n"
                "description: 'Complex test description'\n"
                "tags: ['tag1', 'tag2', 'tag with spaces']\n"
                "keywords: ['keyword1', 'keyword2']\n"
                "---\n\n"
                "Complex content here.\n"
            )

            manager = HugoManager(str(temp_path))
            content_info = manager._parse_content_item(test_file, "post", "en", "complex-test")

            assert content_info is not None
            assert content_info.title == "Complex Test"
            assert content_info.description == "Complex test description"
            assert content_info.tags == ["tag1", "tag2", "tag with spaces"]
            assert content_info.keywords == ["keyword1", "keyword2"]
            assert content_info.preview == "Complex content here."

    def test_parse_content_item_malformed_front_matter(self):
        """Test parsing content with malformed front matter."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Setup Hugo site structure
            (temp_path / "hugo.yaml").touch()
            (temp_path / "content").mkdir()

            # Create a test file with malformed front matter
            test_file = temp_path / "malformed.md"
            test_file.write_text("---\n" "invalid front matter\n" "no date field\n" "---\n\n" "Some content.\n")

            manager = HugoManager(str(temp_path))
            content_info = manager._parse_content_item(test_file, "post", "en", "malformed")

            # Should return None for malformed content
            assert content_info is None

    def test_parse_content_item_no_front_matter(self):
        """Test parsing content without front matter."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Setup Hugo site structure
            (temp_path / "hugo.yaml").touch()
            (temp_path / "content").mkdir()

            # Create a test file without front matter
            test_file = temp_path / "no-frontmatter.md"
            test_file.write_text("Just plain content without front matter.\n")

            manager = HugoManager(str(temp_path))
            content_info = manager._parse_content_item(test_file, "post", "en", "no-frontmatter")

            # Should return None for content without front matter
            assert content_info is None
