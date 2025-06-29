"""Content browser widget for viewing and managing all Hugo content types."""

import platform
import subprocess
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core.git import GitManager
from ..core.hugo import ContentInfo, HugoManager
from ..core.settings import get_settings


class ContentItem(QWidget):
    """Custom widget for displaying content information in the list."""

    def __init__(self, content: ContentInfo):
        super().__init__()
        self.content = content
        self._setup_ui()

    def _setup_ui(self):
        """Set up the content item UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(2)

        # Title and metadata row
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)

        # Content type badge
        type_badge = QLabel(self.content.content_type.upper())
        type_color = {"post": "#2563eb", "conversation": "#059669", "micropost": "#dc2626"}  # Blue  # Green  # Red
        badge_color = type_color.get(self.content.content_type, "#6b7280")
        type_badge.setStyleSheet(
            f"background-color: {badge_color}; color: white; padding: 2px 6px; "
            f"border-radius: 3px; font-size: 9px; font-weight: bold;"
        )
        type_badge.setMaximumWidth(80)
        title_row.addWidget(type_badge)

        # Language badge
        if self.content.language:
            lang_badge = QLabel(self.content.language.upper())
            lang_badge.setStyleSheet(
                "background-color: #6b7280; color: white; padding: 2px 6px; "
                "border-radius: 3px; font-size: 9px; font-weight: bold;"
            )
            lang_badge.setMaximumWidth(30)
            title_row.addWidget(lang_badge)

        # Draft status badge
        if self.content.is_draft:
            draft_badge = QLabel("DRAFT")
            draft_badge.setStyleSheet(
                "background-color: #f59e0b; color: white; padding: 2px 6px; "
                "border-radius: 3px; font-size: 9px; font-weight: bold;"
            )
            draft_badge.setMaximumWidth(50)
            title_row.addWidget(draft_badge)
        else:
            published_badge = QLabel("PUBLISHED")
            published_badge.setStyleSheet(
                "background-color: #10b981; color: white; padding: 2px 6px; "
                "border-radius: 3px; font-size: 9px; font-weight: bold;"
            )
            published_badge.setMaximumWidth(80)
            title_row.addWidget(published_badge)

        title_row.addStretch()

        # Date
        date_str = self.content.date.strftime("%Y-%m-%d %H:%M")
        date_label = QLabel(date_str)
        date_label.setStyleSheet("color: #666; font-size: 10px;")
        title_row.addWidget(date_label)

        layout.addLayout(title_row)

        # Title
        title_label = QLabel(self.content.title)
        title_label.setStyleSheet("font-weight: bold; font-size: 12px; margin: 2px 0;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Description/Preview
        description_text = self.content.description or self.content.preview
        if description_text:
            desc_label = QLabel(description_text)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #555; font-size: 10px;")
            desc_label.setMaximumHeight(40)
            layout.addWidget(desc_label)

        # Tags (if any)
        if self.content.tags:
            tags_text = " • ".join(self.content.tags[:5])  # Limit to 5 tags
            if len(self.content.tags) > 5:
                tags_text += f" (+{len(self.content.tags) - 5} more)"
            tags_label = QLabel(f"Tags: {tags_text}")
            tags_label.setStyleSheet("color: #4b5563; font-size: 9px; font-style: italic;")
            layout.addWidget(tags_label)

        self.setLayout(layout)


class ContentBrowser(QWidget):
    """Widget for browsing and managing all content types."""

    # Signals
    content_updated = Signal()  # Emitted when content is modified

    def __init__(self, hugo_manager: Optional[HugoManager] = None):
        super().__init__()
        self.hugo_manager = hugo_manager or HugoManager()
        self.settings = get_settings()

        # Initialize GitManager for commit/push functionality
        blog_path = self.hugo_manager.get_blog_path()
        self.git_manager = GitManager(str(blog_path)) if blog_path else None

        self._setup_ui()
        self._refresh_content()

    def _setup_ui(self):
        """Set up the browser UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header with filter
        header_layout = QHBoxLayout()

        title_label = QLabel("Content Browser")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 5px 0;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Content type filter
        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet("font-size: 11px; color: #666;")
        header_layout.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Posts", "Conversations", "Microposts"])
        self.filter_combo.currentTextChanged.connect(self._apply_filter)
        self.filter_combo.setMaximumWidth(120)
        header_layout.addWidget(self.filter_combo)

        # Status filter
        status_label = QLabel("Status:")
        status_label.setStyleSheet("font-size: 11px; color: #666;")
        header_layout.addWidget(status_label)

        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["All", "Drafts", "Published"])
        self.status_filter_combo.currentTextChanged.connect(self._apply_filter)
        self.status_filter_combo.setMaximumWidth(100)
        header_layout.addWidget(self.status_filter_combo)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_content)
        refresh_btn.setMaximumWidth(80)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Content list
        self.content_list = QListWidget()
        self.content_list.setAlternatingRowColors(True)
        self.content_list.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.content_list)

        # Action buttons
        button_layout = QHBoxLayout()

        self.open_editor_btn = QPushButton("Open in Editor")
        self.open_editor_btn.clicked.connect(self._open_in_editor)
        self.open_editor_btn.setEnabled(False)
        button_layout.addWidget(self.open_editor_btn)

        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.clicked.connect(self._open_folder)
        self.open_folder_btn.setEnabled(False)
        button_layout.addWidget(self.open_folder_btn)

        # Commit button for uncommitted changes
        self.commit_btn = QPushButton("Commit & Push")
        self.commit_btn.clicked.connect(self._commit_selected_content)
        self.commit_btn.setEnabled(False)
        self.commit_btn.setStyleSheet("QPushButton { background-color: #2563eb; color: white; }")
        button_layout.addWidget(self.commit_btn)

        button_layout.addStretch()

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._delete_content)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; }")
        button_layout.addWidget(self.delete_btn)

        layout.addLayout(button_layout)

    def _refresh_content(self):
        """Refresh the content list."""
        self.content_list.clear()

        if not self.hugo_manager.is_blog_available():
            item = QListWidgetItem("No Hugo blog found")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.content_list.addItem(item)
            return

        # Get all content
        self.all_content = self.hugo_manager.list_all_content()

        if not self.all_content:
            item = QListWidgetItem("No content found")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.content_list.addItem(item)
            return

        # Apply current filter
        self._apply_filter()

    def _apply_filter(self):
        """Apply the selected content type and status filters."""
        self.content_list.clear()

        if not hasattr(self, "all_content") or not self.all_content:
            return

        filter_text = self.filter_combo.currentText().lower()
        status_filter = self.status_filter_combo.currentText().lower()

        filtered_content = []
        for content in self.all_content:
            # Apply content type filter
            type_match = False
            if filter_text == "all":
                type_match = True
            elif filter_text == "posts" and content.content_type == "post":
                type_match = True
            elif filter_text == "conversations" and content.content_type == "conversation":
                type_match = True
            elif filter_text == "microposts" and content.content_type == "micropost":
                type_match = True

            # Apply status filter
            status_match = False
            if status_filter == "all":
                status_match = True
            elif status_filter == "drafts" and content.is_draft:
                status_match = True
            elif status_filter == "published" and not content.is_draft:
                status_match = True

            # Include content only if both filters match
            if type_match and status_match:
                filtered_content.append(content)

        # Populate list with filtered content
        for content in filtered_content:
            # Create list item
            item = QListWidgetItem()
            item.setSizeHint(ContentItem(content).sizeHint())

            # Store content data
            item.setData(Qt.ItemDataRole.UserRole, content)

            # Add to list
            self.content_list.addItem(item)

            # Create and set custom widget
            item_widget = ContentItem(content)
            self.content_list.setItemWidget(item, item_widget)

    def _on_selection_changed(self):
        """Handle selection change."""
        current_item = self.content_list.currentItem()
        has_selection = current_item is not None and current_item.data(Qt.ItemDataRole.UserRole) is not None

        self.open_editor_btn.setEnabled(has_selection)
        self.open_folder_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

        # Enable commit button only if content has uncommitted changes
        commit_enabled = False
        if has_selection and self.git_manager:
            content = current_item.data(Qt.ItemDataRole.UserRole)
            commit_enabled = self._has_uncommitted_changes(content)

        self.commit_btn.setEnabled(commit_enabled)

    def _get_selected_content(self) -> Optional[ContentInfo]:
        """Get the currently selected content."""
        current_item = self.content_list.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None

    def _open_in_editor(self):
        """Open the selected content in external editor."""
        content = self._get_selected_content()
        if not content:
            return

        editor_command = self.settings.get_editor_command()

        if not editor_command:
            QMessageBox.warning(
                self,
                "No Editor Configured",
                "No suitable text editor could be found.\n\n"
                "Please configure an editor in Settings or install one of:\n"
                "• Visual Studio Code (code)\n"
                "• Sublime Text (subl)\n"
                "• Vim (vim)\n"
                "• Nano (nano)",
            )
            return

        try:
            editor_parts = editor_command.split()
            cmd = editor_parts + [str(content.file_path)]

            subprocess.run(
                cmd,
                timeout=10,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired:
            pass
        except FileNotFoundError:
            QMessageBox.warning(
                self,
                "Editor Not Found",
                f"Editor command '{editor_command}' was not found.\n\n"
                "Please check your editor configuration in Settings.",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Editor Error",
                f"Failed to open editor:\n\n{e}",
            )

    def _open_folder(self):
        """Open the content's folder in file manager."""
        content = self._get_selected_content()
        if not content:
            return

        folder_path = content.file_path.parent
        system = platform.system()

        try:
            if system == "Darwin":  # macOS
                result = subprocess.run(
                    ["open", str(folder_path)],
                    timeout=10,
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(result.returncode, "open")
            elif system == "Linux":
                linux_commands = [
                    ["xdg-open", str(folder_path)],
                    ["dolphin", str(folder_path)],
                    ["nautilus", str(folder_path)],
                    ["thunar", str(folder_path)],
                    ["pcmanfm", str(folder_path)],
                ]

                success = False
                last_error = None

                for cmd in linux_commands:
                    try:
                        result = subprocess.run(
                            cmd,
                            timeout=10,
                            capture_output=True,
                            text=True,
                        )

                        # Special handling for xdg-open
                        if cmd[0] == "xdg-open" and hasattr(result, "stderr") and result.stderr:
                            error_indicators = [
                                "kfmclient: command not found",
                                "integer expression expected",
                                "No such file or directory",
                            ]
                            try:
                                if any(indicator in result.stderr for indicator in error_indicators):
                                    last_error = Exception(f"xdg-open failed: {result.stderr.strip()}")
                                    continue
                            except (TypeError, AttributeError):
                                pass

                        success = True
                        break
                    except FileNotFoundError as e:
                        last_error = e
                        continue
                    except subprocess.TimeoutExpired:
                        success = True
                        break

                if not success:
                    raise last_error or FileNotFoundError("No suitable file manager found")

            else:  # Windows
                result = subprocess.run(
                    ["explorer", str(folder_path)],
                    timeout=10,
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(result.returncode, "explorer")

        except subprocess.TimeoutExpired:
            pass
        except FileNotFoundError:
            QMessageBox.warning(
                self,
                "File Manager Not Found",
                f"Could not find a suitable file manager for {system}.\n\n"
                f"Path: {folder_path}\n\n"
                f"Please open this path manually in your file manager.",
            )
        except subprocess.CalledProcessError as e:
            QMessageBox.warning(
                self,
                "File Manager Error",
                f"Failed to open file manager (exit code {e.returncode}).\n\n"
                f"Path: {folder_path}\n\n"
                f"Please open this path manually in your file manager.",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Unexpected Error",
                f"An unexpected error occurred:\n\n{e}\n\nPath: {folder_path}",
            )

    def _delete_content(self):
        """Delete the selected content."""
        content = self._get_selected_content()
        if not content:
            return

        # Confirmation dialog
        content_type_name = content.content_type.title()
        reply = QMessageBox.question(
            self,
            f"Delete {content_type_name}",
            f"Are you sure you want to delete this {content.content_type}?\n\n"
            f"Title: {content.title}\n"
            f"Date: {content.date.strftime('%Y-%m-%d %H:%M')}\n"
            f"Type: {content_type_name} ({content.language.upper()})\n\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # For posts and conversations, delete the entire directory
                if content.content_type in ["post", "conversation"]:
                    import shutil

                    shutil.rmtree(content.file_path.parent)
                else:
                    # For microposts, delete just the file
                    content.file_path.unlink()

                self._refresh_content()
                self.content_updated.emit()
                QMessageBox.information(
                    self,
                    f"{content_type_name} Deleted",
                    f"{content_type_name} has been deleted successfully.",
                )
            except Exception as e:
                QMessageBox.critical(self, "Delete Failed", f"Failed to delete {content.content_type}:\n\n{e}")

    def refresh(self):
        """Public method to refresh the content list."""
        self._refresh_content()

    def _has_uncommitted_changes(self, content: ContentInfo) -> bool:
        """Check if content has uncommitted changes."""
        if not self.git_manager:
            return False

        try:
            # Determine the path to check based on content type
            if content.content_type in ["post", "conversation"]:
                # For posts and conversations, check the entire directory
                relative_path = content.file_path.parent.relative_to(self.hugo_manager.get_blog_path())
            else:
                # For microposts, check just the file
                relative_path = content.file_path.relative_to(self.hugo_manager.get_blog_path())

            # Check git status for this specific path
            result = subprocess.run(
                ["git", "status", "--porcelain", str(relative_path)],
                cwd=self.hugo_manager.get_blog_path(),
                capture_output=True,
                text=True,
                timeout=10,
            )

            # If there's output, there are changes
            return result.returncode == 0 and bool(result.stdout.strip())

        except Exception:
            return False

    def _commit_selected_content(self):
        """Commit and push the selected content item."""
        content = self._get_selected_content()
        if not content or not self.git_manager:
            return

        try:
            # Import here to avoid circular imports
            from .commit_dialog import CommitDialog

            # Determine what files to commit based on content type
            if content.content_type in ["post", "conversation"]:
                # For posts and conversations, commit the entire directory
                relative_path = content.file_path.parent.relative_to(self.hugo_manager.get_blog_path())
            else:
                # For microposts, commit just the file
                relative_path = content.file_path.relative_to(self.hugo_manager.get_blog_path())

            # Create commit dialog with pre-filled message
            content_type_name = content.content_type.title()
            default_message = f"Update {content_type_name.lower()}: {content.title}"

            dialog = CommitDialog(self, self.git_manager)
            # Set the default message
            dialog.message_edit.setPlainText(default_message)

            if dialog.exec():
                # Get the commit message from dialog
                commit_message = dialog.get_commit_message()

                # Commit the specific path
                success, message = self.git_manager.commit_and_push_path(commit_message, str(relative_path))

                if success:
                    # Refresh content list and emit signal
                    self._refresh_content()
                    self.content_updated.emit()
                    QMessageBox.information(
                        self,
                        "Commit Successful",
                        f"{content_type_name} '{content.title}' has been committed and pushed successfully.",
                    )
                else:
                    QMessageBox.critical(
                        self,
                        "Commit Failed",
                        f"Failed to commit {content.content_type}:\n\n{message}",
                    )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Commit Failed",
                f"Failed to commit {content.content_type}:\n\n{e}",
            )
