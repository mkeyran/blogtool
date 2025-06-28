"""Git operations for blog management."""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


@dataclass
class GitStatus:
    """Git repository status information."""

    is_repo: bool
    modified_files: int
    staged_files: int
    untracked_files: int
    has_unpushed_commits: bool
    current_branch: str


class GitManager:
    """Manages Git operations for the blog repository."""

    def __init__(self, blog_path: Optional[Path] = None):
        """Initialize Git manager.

        Args:
            blog_path: Path to the blog repository.
                If None, will use current working directory.
        """
        self.blog_path = blog_path or Path.cwd()

    def get_status(self) -> GitStatus:
        """Get current git status.

        Returns:
            GitStatus object with repository information.
        """
        if not self._is_git_repo():
            return GitStatus(
                is_repo=False,
                modified_files=0,
                staged_files=0,
                untracked_files=0,
                has_unpushed_commits=False,
                current_branch="",
            )

        try:
            # Get git status porcelain output for file counts
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.blog_path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return self._empty_status()

            status_lines = result.stdout.split("\n") if result.stdout else []
            # Filter out empty lines
            status_lines = [line for line in status_lines if line.strip()]

            modified_files = 0
            staged_files = 0
            untracked_files = 0

            for line in status_lines:
                if len(line) >= 2:
                    staged_status = line[0]
                    modified_status = line[1]

                    if staged_status == "?" and modified_status == "?":
                        untracked_files += 1
                    else:
                        if staged_status != " ":
                            staged_files += 1
                        if modified_status != " " and modified_status != "?":
                            modified_files += 1

            # Get current branch
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.blog_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

            # Check for unpushed commits
            has_unpushed = self._has_unpushed_commits()

            return GitStatus(
                is_repo=True,
                modified_files=modified_files,
                staged_files=staged_files,
                untracked_files=untracked_files,
                has_unpushed_commits=has_unpushed,
                current_branch=current_branch,
            )

        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            Exception,
        ):
            return self._empty_status()

    def _is_git_repo(self) -> bool:
        """Check if current directory is a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.blog_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _has_unpushed_commits(self) -> bool:
        """Check if there are unpushed commits."""
        try:
            # Get current branch
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.blog_path,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if branch_result.returncode != 0:
                return False

            current_branch = branch_result.stdout.strip()

            # Check if remote branch exists
            remote_result = subprocess.run(
                ["git", "rev-parse", "--verify", f"origin/{current_branch}"],
                cwd=self.blog_path,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if remote_result.returncode != 0:
                # No remote branch, consider as having unpushed commits
                # if there are commits
                commits_result = subprocess.run(
                    ["git", "rev-list", "--count", "HEAD"],
                    cwd=self.blog_path,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                return commits_result.returncode == 0 and int(commits_result.stdout.strip()) > 0

            # Compare local and remote
            diff_result = subprocess.run(
                [
                    "git",
                    "rev-list",
                    "--count",
                    f"origin/{current_branch}..HEAD",
                ],
                cwd=self.blog_path,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if diff_result.returncode == 0:
                unpushed_count = int(diff_result.stdout.strip())
                return unpushed_count > 0

            return False
        except Exception:
            return False

    def _empty_status(self) -> GitStatus:
        """Return empty git status."""
        return GitStatus(
            is_repo=True,
            modified_files=0,
            staged_files=0,
            untracked_files=0,
            has_unpushed_commits=False,
            current_branch="",
        )

    def commit_and_push(self, message: str, add_all: bool = True) -> Tuple[bool, str]:
        """Commit changes and push to remote.

        Args:
            message: Commit message
            add_all: Whether to add all changes before committing

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self._is_git_repo():
            return False, "Not a git repository"

        try:
            # Add all changes if requested
            if add_all:
                add_result = subprocess.run(
                    ["git", "add", "."],
                    cwd=self.blog_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if add_result.returncode != 0:
                    return False, f"Failed to add files: {add_result.stderr}"

            # Commit changes
            commit_result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.blog_path,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if commit_result.returncode != 0:
                if "nothing to commit" in commit_result.stdout:
                    return False, "No changes to commit"
                return False, f"Commit failed: {commit_result.stderr}"

            # Push to remote
            push_result = subprocess.run(
                ["git", "push"],
                cwd=self.blog_path,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if push_result.returncode != 0:
                return False, f"Push failed: {push_result.stderr}"

            return True, "Changes committed and pushed successfully"

        except subprocess.TimeoutExpired:
            return False, "Git operation timed out"
        except Exception as e:
            return False, f"Error: {e}"
