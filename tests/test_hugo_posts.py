"""Tests for Hugo post and conversation creation functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from blogtool.core.hugo import HugoManager


class TestHugoPostCreation:
    """Test post and conversation creation in HugoManager."""

    def test_create_post_success(self):
        """Test successful post creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Setup Hugo site structure
            (temp_path / "hugo.yaml").touch()
            content_dir = temp_path / "content"
            content_dir.mkdir()
            english_dir = content_dir / "english"
            english_dir.mkdir()
            posts_dir = english_dir / "posts"
            posts_dir.mkdir()

            # Mock subprocess.run for hugo command
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0, stderr="")

                # Create the expected directory and file that hugo would create
                post_dir = posts_dir / "test-post"
                post_dir.mkdir()
                post_file = post_dir / "index.md"
                post_file.write_text(
                    "---\n"
                    "date: '2025-06-29T10:00:00+02:00'\n"
                    "draft: true\n"
                    "title: 'Test Post'\n"
                    "tags: []\n"
                    "description: ''\n"
                    "keywords: []\n"
                    'aiUsage: "none"\n'
                    'aiComment: ""\n'
                    "---\n"
                )

                manager = HugoManager(str(temp_path))
                success, message = manager.create_post(
                    title="Test Post",
                    slug="test-post",
                    language="en",
                    description="A test post",
                    tags=["test", "blog"],
                    keywords=["test"],
                )

                assert success
                assert "successfully" in message

                # Verify hugo command was called correctly
                mock_run.assert_called_once()
                call_args = mock_run.call_args
                assert call_args[0][0] == [
                    "hugo",
                    "new",
                    "content",
                    "content/english/posts/test-post/index.md",
                ]
                assert call_args[1]["cwd"] == temp_path

                # Verify front matter was updated
                final_content = post_file.read_text()
                assert "title: 'Test Post'" in final_content
                assert "description: 'A test post'" in final_content

    def test_create_post_different_languages(self):
        """Test post creation in different languages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Setup Hugo site structure
            (temp_path / "hugo.yaml").touch()
            content_dir = temp_path / "content"
            content_dir.mkdir()

            # Create language directories
            for lang_dir in ["english", "russian", "polish"]:
                lang_path = content_dir / lang_dir
                lang_path.mkdir()
                (lang_path / "posts").mkdir()

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0, stderr="")

                manager = HugoManager(str(temp_path))

                # Test English
                (content_dir / "english" / "posts" / "en-post").mkdir()
                (content_dir / "english" / "posts" / "en-post" / "index.md").write_text("---\ntitle: ''\n---\n")

                success, _ = manager.create_post(title="English Post", slug="en-post", language="en")
                assert success

                # Test Russian
                (content_dir / "russian" / "posts" / "ru-post").mkdir()
                (content_dir / "russian" / "posts" / "ru-post" / "index.md").write_text("---\ntitle: ''\n---\n")

                success, _ = manager.create_post(title="Russian Post", slug="ru-post", language="ru")
                assert success

                # Test Polish
                (content_dir / "polish" / "posts" / "pl-post").mkdir()
                (content_dir / "polish" / "posts" / "pl-post" / "index.md").write_text("---\ntitle: ''\n---\n")

                success, _ = manager.create_post(title="Polish Post", slug="pl-post", language="pl")
                assert success

                # Verify correct paths were used
                calls = mock_run.call_args_list
                assert len(calls) == 3

                assert "content/english/posts/en-post/index.md" in calls[0][0][0]
                assert "content/russian/posts/ru-post/index.md" in calls[1][0][0]
                assert "content/polish/posts/pl-post/index.md" in calls[2][0][0]

    def test_create_conversation_success(self):
        """Test successful conversation creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Setup Hugo site structure
            (temp_path / "hugo.yaml").touch()
            content_dir = temp_path / "content"
            content_dir.mkdir()
            english_dir = content_dir / "english"
            english_dir.mkdir()
            conversations_dir = english_dir / "conversations"
            conversations_dir.mkdir()

            # Mock subprocess.run for hugo command
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0, stderr="")

                # Create the expected directory and file that hugo would create
                conv_dir = conversations_dir / "test-conversation"
                conv_dir.mkdir()
                conv_file = conv_dir / "index.md"
                conv_file.write_text(
                    "---\n"
                    "date: '2025-06-29T10:00:00+02:00'\n"
                    "draft: true\n"
                    "title: 'Test Conversation'\n"
                    "tags: []\n"
                    "description: ''\n"
                    "keywords: []\n"
                    'aiUsage: "none"\n'
                    'aiComment: ""\n'
                    "---\n"
                )

                manager = HugoManager(str(temp_path))
                success, message = manager.create_conversation(
                    title="Test Conversation",
                    slug="test-conversation",
                    language="en",
                    description="A test conversation",
                    tags=["interview", "dialogue"],
                    keywords=["conversation"],
                )

                assert success
                assert "successfully" in message

                # Verify hugo command was called with conversations archetype
                mock_run.assert_called_once()
                call_args = mock_run.call_args
                assert call_args[0][0] == [
                    "hugo",
                    "new",
                    "content",
                    "content/english/conversations/test-conversation/index.md",
                    "--kind",
                    "conversations",
                ]

    def test_create_post_hugo_command_fails(self):
        """Test post creation when Hugo command fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Setup Hugo site
            (temp_path / "hugo.yaml").touch()
            (temp_path / "content").mkdir()

            # Mock failed hugo command
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=1, stderr="Hugo error")

                manager = HugoManager(str(temp_path))
                success, message = manager.create_post(title="Test", slug="test", language="en")

                assert not success
                assert "Hugo command failed" in message
                assert "Hugo error" in message

    def test_create_post_no_blog(self):
        """Test post creation when no blog is available."""
        manager = HugoManager("/nonexistent/path")
        success, message = manager.create_post(title="test", slug="test", language="en")

        assert not success
        assert "Hugo blog not found" in message

    def test_update_post_front_matter(self):
        """Test updating post front matter with provided data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Setup Hugo site structure
            (temp_path / "hugo.yaml").touch()
            (temp_path / "content").mkdir()

            # Create a test post file
            test_file = temp_path / "test.md"
            test_file.write_text(
                "---\n"
                "date: '2025-06-29T10:00:00+02:00'\n"
                "draft: true\n"
                "title: 'Old Title'\n"
                "tags: []\n"
                "description: 'Old description'\n"
                "keywords: []\n"
                "---\n\n"
                "Content here\n"
            )

            manager = HugoManager(str(temp_path))
            manager._update_post_front_matter(
                test_file,
                title="New Title",
                description="New description",
                tags=["tag1", "tag2"],
                keywords=["kw1", "kw2"],
            )

            # Read updated content
            updated_content = test_file.read_text()

            assert "title: 'New Title'" in updated_content
            assert "description: 'New description'" in updated_content
            assert "tags: ['tag1', 'tag2']" in updated_content
            assert "keywords: ['kw1', 'kw2']" in updated_content
            assert "Content here" in updated_content

    def test_create_conversation_different_languages(self):
        """Test conversation creation in different languages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Setup Hugo site structure
            (temp_path / "hugo.yaml").touch()
            content_dir = temp_path / "content"
            content_dir.mkdir()

            # Create language directories
            for lang_dir in ["english", "russian", "polish"]:
                lang_path = content_dir / lang_dir
                lang_path.mkdir()
                (lang_path / "conversations").mkdir()

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0, stderr="")

                manager = HugoManager(str(temp_path))

                # Create mock files for each language
                for lang, slug in [("en", "en-conv"), ("ru", "ru-conv"), ("pl", "pl-conv")]:
                    lang_map = {"en": "english", "ru": "russian", "pl": "polish"}
                    lang_dir = lang_map[lang]

                    conv_dir = content_dir / lang_dir / "conversations" / slug
                    conv_dir.mkdir()
                    (conv_dir / "index.md").write_text("---\ntitle: ''\n---\n")

                    success, _ = manager.create_conversation(
                        title=f"{lang.upper()} Conversation", slug=slug, language=lang
                    )
                    assert success

                # Verify correct paths were used
                calls = mock_run.call_args_list
                assert len(calls) == 3

                assert "content/english/conversations/en-conv/index.md" in calls[0][0][0]
                assert "content/russian/conversations/ru-conv/index.md" in calls[1][0][0]
                assert "content/polish/conversations/pl-conv/index.md" in calls[2][0][0]

                # Verify conversations archetype is used
                for call in calls:
                    assert "--kind" in call[0][0]
                    assert "conversations" in call[0][0]
