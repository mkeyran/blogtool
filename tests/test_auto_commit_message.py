"""Tests for automated commit message generation."""

import subprocess
from unittest.mock import Mock, patch

from blogtool.core.git import GitManager


class TestAutoCommitMessage:
    """Test automated commit message generation functionality."""

    def test_generate_commit_message_with_staged_changes(self, tmp_path):
        """Test generating commit message with staged changes."""
        git_manager = GitManager(str(tmp_path))

        # Mock git diff --cached to return some changes
        mock_diff = "diff --git a/test.md b/test.md\n+Added content"
        mock_llm_output = "other: Updated test file"

        with patch("subprocess.run") as mock_run:
            # Mock llm availability check, git diff --cached, and llm command
            mock_run.side_effect = [
                Mock(returncode=0, stdout=""),  # llm --help (available)
                Mock(returncode=0, stdout=mock_diff),  # git diff --cached
                Mock(returncode=0, stdout=mock_llm_output),  # llm command
            ]

            result = git_manager.generate_commit_message()

            assert result == "other: Updated test file"
            # Verify correct commands were called
            assert mock_run.call_count == 3

    def test_generate_commit_message_with_unstaged_changes(self, tmp_path):
        """Test generating commit message when no staged changes but unstaged exist."""
        git_manager = GitManager(str(tmp_path))

        mock_diff = "diff --git a/test.md b/test.md\n+Added content"
        mock_llm_output = "other: Added new content to test file"

        with patch("subprocess.run") as mock_run:
            # Mock llm availability check, git diff --cached (no changes), then git diff (has changes)
            mock_run.side_effect = [
                Mock(returncode=0, stdout=""),  # llm --help (available)
                Mock(returncode=0, stdout=""),  # git diff --cached (empty)
                Mock(returncode=0, stdout=mock_diff),  # git diff
                Mock(returncode=0, stdout=mock_llm_output),  # llm command
            ]

            result = git_manager.generate_commit_message()

            assert result == "other: Added new content to test file"
            assert mock_run.call_count == 4

    def test_generate_commit_message_no_changes(self, tmp_path):
        """Test generating commit message when no changes exist."""
        git_manager = GitManager(str(tmp_path))

        with patch("subprocess.run") as mock_run:
            # Mock llm availability check and both git diff commands returning empty
            mock_run.side_effect = [
                Mock(returncode=0, stdout=""),  # llm --help (available)
                Mock(returncode=0, stdout=""),  # git diff --cached
                Mock(returncode=0, stdout=""),  # git diff
            ]

            result = git_manager.generate_commit_message()

            assert result == ""
            # llm should not be called if no changes
            assert mock_run.call_count == 3

    def test_generate_commit_message_llm_failure(self, tmp_path):
        """Test handling llm command failure."""
        git_manager = GitManager(str(tmp_path))

        mock_diff = "diff --git a/test.md b/test.md\n+Added content"

        with patch("subprocess.run") as mock_run:
            # Mock llm availability check, git diff success, llm failure
            mock_run.side_effect = [
                Mock(returncode=0, stdout=""),  # llm --help (available)
                Mock(returncode=0, stdout=mock_diff),  # git diff --cached
                Mock(returncode=1, stdout="", stderr="LLM error"),  # llm command fails
            ]

            result = git_manager.generate_commit_message()

            assert result == ""

    def test_generate_commit_message_timeout(self, tmp_path):
        """Test handling timeout during command execution."""
        git_manager = GitManager(str(tmp_path))

        with patch("subprocess.run") as mock_run:
            # Mock timeout exception on availability check
            mock_run.side_effect = subprocess.TimeoutExpired("llm", 5)

            result = git_manager.generate_commit_message()

            assert result == ""

    def test_generate_commit_message_llm_not_available(self, tmp_path):
        """Test handling when llm tool is not available."""
        git_manager = GitManager(str(tmp_path))

        with patch("subprocess.run") as mock_run:
            # Mock FileNotFoundError for llm not available
            mock_run.side_effect = FileNotFoundError("llm command not found")

            result = git_manager.generate_commit_message()

            assert result == ""

    def test_generate_commit_message_blog_post_format(self, tmp_path):
        """Test that blog post changes generate correct format."""
        git_manager = GitManager(str(tmp_path))

        # Mock diff that includes blog post changes
        mock_diff = """diff --git a/content/english/posts/my-post/index.md b/content/english/posts/my-post/index.md
index 123..456 100644
--- a/content/english/posts/my-post/index.md
+++ b/content/english/posts/my-post/index.md
@@ -1,3 +1,4 @@
 # My Post

 Content here
+More content added"""

        mock_llm_output = "my-post en: Added more content to the post"

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0, stdout=""),  # llm --help (available)
                Mock(returncode=0, stdout=mock_diff),  # git diff --cached
                Mock(returncode=0, stdout=mock_llm_output),  # llm command
            ]

            result = git_manager.generate_commit_message()

            assert result == "my-post en: Added more content to the post"

            # Verify llm was called with correct prompt format
            llm_call = mock_run.call_args_list[2]
            assert "llm" in llm_call[0][0]
            assert "-m" in llm_call[0][0]
            assert "openrouter/google/gemini-2.5-flash" in llm_call[0][0]

            # Check that prompt contains instructions
            prompt = llm_call[1]["input"]
            assert "<blog_post_handle> <languages>: <description>" in prompt
            assert "other: <description>" in prompt
