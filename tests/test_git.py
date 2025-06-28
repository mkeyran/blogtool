"""Tests for Git operations."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

from blogtool.core.git import GitManager, GitStatus


class TestGitManager:
    """Test cases for GitManager."""

    def test_init_with_path(self):
        """Test initialization with provided path."""
        test_path = Path("/test/path")
        manager = GitManager(test_path)
        assert manager.blog_path == test_path

    def test_init_without_path(self):
        """Test initialization without path uses current directory."""
        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/current/dir")
            manager = GitManager()
            assert manager.blog_path == Path("/current/dir")

    @patch("subprocess.run")
    def test_is_git_repo_true(self, mock_run):
        """Test git repository detection when it is a repo."""
        mock_run.return_value = Mock(returncode=0)

        manager = GitManager()
        assert manager._is_git_repo()

        mock_run.assert_called_once_with(
            ["git", "rev-parse", "--git-dir"],
            cwd=manager.blog_path,
            capture_output=True,
            text=True,
            timeout=5,
        )

    @patch("subprocess.run")
    def test_is_git_repo_false(self, mock_run):
        """Test git repository detection when it is not a repo."""
        mock_run.return_value = Mock(returncode=1)

        manager = GitManager()
        assert not manager._is_git_repo()

    @patch("subprocess.run")
    def test_is_git_repo_exception(self, mock_run):
        """Test git repository detection handles exceptions."""
        mock_run.side_effect = subprocess.TimeoutExpired("git", 5)

        manager = GitManager()
        assert not manager._is_git_repo()

    @patch("subprocess.run")
    def test_get_status_not_repo(self, mock_run):
        """Test getting status when not a git repository."""
        mock_run.return_value = Mock(returncode=1)

        manager = GitManager()
        status = manager.get_status()

        assert not status.is_repo
        assert status.modified_files == 0
        assert status.staged_files == 0
        assert status.untracked_files == 0
        assert not status.has_unpushed_commits
        assert status.current_branch == ""

    @patch("subprocess.run")
    def test_get_status_clean_repo(self, mock_run):
        """Test getting status for clean repository."""

        # Mock git rev-parse for repo check
        # Mock git status for file status
        # Mock git rev-parse for branch
        # Mock git commands for unpushed check
        def side_effect(cmd, **kwargs):
            if cmd[1] == "rev-parse" and cmd[2] == "--git-dir":
                return Mock(returncode=0)
            elif cmd[1] == "status":
                return Mock(returncode=0, stdout="")
            elif cmd[1] == "rev-parse" and cmd[2] == "--abbrev-ref":
                return Mock(returncode=0, stdout="main\n")
            elif cmd[1] == "rev-parse" and cmd[2] == "--verify":
                return Mock(returncode=0)
            elif cmd[1] == "rev-list" and "--count" in cmd:
                return Mock(returncode=0, stdout="0\n")
            return Mock(returncode=0, stdout="")

        mock_run.side_effect = side_effect

        manager = GitManager()
        status = manager.get_status()

        assert status.is_repo
        assert status.modified_files == 0
        assert status.staged_files == 0
        assert status.untracked_files == 0
        assert not status.has_unpushed_commits
        assert status.current_branch == "main"

    @patch("subprocess.run")
    def test_get_status_with_changes(self, mock_run):
        """Test getting status with file changes."""

        def side_effect(cmd, **kwargs):
            if cmd[1] == "rev-parse" and cmd[2] == "--git-dir":
                return Mock(returncode=0)
            elif cmd[1] == "status":
                # Git status porcelain output: XY filename
                # X = staged status, Y = modified status
                return Mock(returncode=0, stdout=" M file1.md\nA  file2.md\n?? file3.md")
            elif cmd[1] == "rev-parse" and cmd[2] == "--abbrev-ref":
                return Mock(returncode=0, stdout="main\n")
            elif cmd[1] == "rev-parse" and cmd[2] == "--verify":
                return Mock(returncode=0)
            elif cmd[1] == "rev-list" and "--count" in cmd:
                return Mock(returncode=0, stdout="0\n")
            return Mock(returncode=0, stdout="")

        mock_run.side_effect = side_effect

        manager = GitManager()
        status = manager.get_status()

        assert status.is_repo
        assert status.modified_files == 1  # " M" - modified file (modified in working tree)
        assert status.staged_files == 1  # "A " - staged file (added to index)
        assert status.untracked_files == 1  # "??" - untracked file

    @patch("subprocess.run")
    def test_has_unpushed_commits_true(self, mock_run):
        """Test detecting unpushed commits."""

        def side_effect(cmd, **kwargs):
            if cmd[1] == "rev-parse" and cmd[2] == "--abbrev-ref":
                return Mock(returncode=0, stdout="main\n")
            elif cmd[1] == "rev-parse" and cmd[2] == "--verify":
                return Mock(returncode=0)
            elif cmd[1] == "rev-list" and "--count" in cmd:
                return Mock(returncode=0, stdout="2\n")  # 2 unpushed commits
            return Mock(returncode=0, stdout="")

        mock_run.side_effect = side_effect

        manager = GitManager()
        assert manager._has_unpushed_commits()

    @patch("subprocess.run")
    def test_commit_and_push_success(self, mock_run):
        """Test successful commit and push."""

        # Mock git repo check, add, commit, and push
        def side_effect(cmd, **kwargs):
            if cmd[1] == "rev-parse" and cmd[2] == "--git-dir":
                return Mock(returncode=0)
            elif cmd[1] == "add":
                return Mock(returncode=0, stderr="")
            elif cmd[1] == "commit":
                return Mock(returncode=0, stderr="")
            elif cmd[1] == "push":
                return Mock(returncode=0, stderr="")
            return Mock(returncode=0, stdout="")

        mock_run.side_effect = side_effect

        manager = GitManager()
        success, message = manager.commit_and_push("Test commit")

        assert success
        assert "successfully" in message

    @patch("subprocess.run")
    def test_commit_and_push_not_repo(self, mock_run):
        """Test commit and push when not a git repository."""
        mock_run.return_value = Mock(returncode=1)

        manager = GitManager()
        success, message = manager.commit_and_push("Test commit")

        assert not success
        assert "Not a git repository" in message

    @patch("subprocess.run")
    def test_commit_and_push_nothing_to_commit(self, mock_run):
        """Test commit and push when nothing to commit."""

        def side_effect(cmd, **kwargs):
            if cmd[1] == "rev-parse" and cmd[2] == "--git-dir":
                return Mock(returncode=0)
            elif cmd[1] == "add":
                return Mock(returncode=0, stderr="")
            elif cmd[1] == "commit":
                return Mock(returncode=1, stdout="nothing to commit, working tree clean")
            return Mock(returncode=0)

        mock_run.side_effect = side_effect

        manager = GitManager()
        success, message = manager.commit_and_push("Test commit")

        assert not success
        assert "No changes to commit" in message

    @patch("subprocess.run")
    def test_commit_and_push_commit_fails(self, mock_run):
        """Test commit and push when commit fails."""

        def side_effect(cmd, **kwargs):
            if cmd[1] == "rev-parse" and cmd[2] == "--git-dir":
                return Mock(returncode=0)
            elif cmd[1] == "add":
                return Mock(returncode=0, stderr="")
            elif cmd[1] == "commit":
                return Mock(returncode=1, stdout="", stderr="Commit error")
            return Mock(returncode=0)

        mock_run.side_effect = side_effect

        manager = GitManager()
        success, message = manager.commit_and_push("Test commit")

        assert not success
        assert "Commit failed" in message

    @patch("subprocess.run")
    def test_commit_and_push_push_fails(self, mock_run):
        """Test commit and push when push fails."""

        def side_effect(cmd, **kwargs):
            if cmd[1] == "rev-parse" and cmd[2] == "--git-dir":
                return Mock(returncode=0)
            elif cmd[1] == "add":
                return Mock(returncode=0, stderr="")
            elif cmd[1] == "commit":
                return Mock(returncode=0, stderr="")
            elif cmd[1] == "push":
                return Mock(returncode=1, stderr="Push error")
            return Mock(returncode=0)

        mock_run.side_effect = side_effect

        manager = GitManager()
        success, message = manager.commit_and_push("Test commit")

        assert not success
        assert "Push failed" in message


def test_git_status_dataclass():
    """Test GitStatus dataclass."""
    status = GitStatus(
        is_repo=True,
        modified_files=2,
        staged_files=1,
        untracked_files=3,
        has_unpushed_commits=True,
        current_branch="main",
    )

    assert status.is_repo
    assert status.modified_files == 2
    assert status.staged_files == 1
    assert status.untracked_files == 3
    assert status.has_unpushed_commits
    assert status.current_branch == "main"
