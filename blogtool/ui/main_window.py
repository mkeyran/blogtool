"""Main window for the Hugo Blog Management Console."""

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from ..core.git import GitManager
from ..core.hugo import HugoManager
from ..core.hugo_server import HugoServerManager
from .commit_dialog import CommitDialog
from .content_browser import ContentBrowser
from .conversation_dialog import ConversationDialog
from .micropost_dialog import MicropostDialog
from .post_dialog import PostDialog
from .settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hugo Blog Management Console")
        self.setGeometry(100, 100, 800, 600)

        # Initialize managers
        self.hugo_manager = HugoManager()
        self.git_manager = GitManager(self.hugo_manager.get_blog_path())
        self.server_manager = HugoServerManager(self.hugo_manager.get_blog_path())

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Create content browser
        self.content_browser = ContentBrowser(self.hugo_manager)
        self.content_browser.content_updated.connect(self._update_git_status)
        layout.addWidget(self.content_browser)

        # Create menu bar
        self._create_menu_bar()

        # Create status bar
        self._create_status_bar()

        # Set up timer for git and server status updates
        self._setup_status_timer()

    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # New Post action
        new_post_action = QAction("New &Post", self)
        new_post_action.setShortcut("Ctrl+P")
        new_post_action.triggered.connect(self._create_new_post)
        file_menu.addAction(new_post_action)

        # New Micropost action
        new_micropost_action = QAction("New &Micropost", self)
        new_micropost_action.setShortcut("Ctrl+M")
        new_micropost_action.triggered.connect(self._create_new_micropost)
        file_menu.addAction(new_micropost_action)

        # New Conversation action
        new_conversation_action = QAction("New &Conversation", self)
        new_conversation_action.setShortcut("Ctrl+Shift+N")
        new_conversation_action.triggered.connect(self._create_new_conversation)
        file_menu.addAction(new_conversation_action)

        file_menu.addSeparator()

        # Commit & Push action
        self.commit_action = QAction("&Commit && Push", self)
        self.commit_action.setShortcut("Ctrl+Shift+C")
        self.commit_action.triggered.connect(self._commit_and_push)
        self.commit_action.setEnabled(False)  # Initially disabled
        file_menu.addAction(self.commit_action)

        file_menu.addSeparator()

        # Settings action
        settings_action = QAction("&Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._show_settings)
        file_menu.addAction(settings_action)

        # Server menu
        server_menu = menubar.addMenu("&Server")

        # Start Server action
        start_server_action = QAction("&Start Server", self)
        start_server_action.setShortcut("Ctrl+Shift+S")
        start_server_action.triggered.connect(self._start_server)
        server_menu.addAction(start_server_action)

        # Stop Server action
        stop_server_action = QAction("St&op Server", self)
        stop_server_action.setShortcut("Ctrl+Shift+T")
        stop_server_action.triggered.connect(self._stop_server)
        server_menu.addAction(stop_server_action)

        # Restart Server action
        restart_server_action = QAction("&Restart Server", self)
        restart_server_action.setShortcut("Ctrl+Shift+R")
        restart_server_action.triggered.connect(self._restart_server)
        server_menu.addAction(restart_server_action)

        server_menu.addSeparator()

        # Preview Site action
        preview_site_action = QAction("&Preview Site", self)
        preview_site_action.setShortcut("Ctrl+Shift+P")
        preview_site_action.triggered.connect(self._preview_site)
        server_menu.addAction(preview_site_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _create_new_post(self):
        """Create a new blog post."""
        if not self.hugo_manager.is_blog_available():
            QMessageBox.warning(
                self,
                "Hugo Blog Not Found",
                "Could not find a Hugo blog in the expected location.\n\n"
                "Please configure your blog path in Settings.",
            )
            return

        dialog = PostDialog(self)
        if dialog.exec() == QDialog.Accepted:
            post_data = dialog.get_post_data()

            # Create the post
            success, message = self.hugo_manager.create_post(
                title=post_data["title"],
                slug=post_data["slug"],
                language=post_data["language"],
                description=post_data["description"],
                tags=post_data["tags"],
                keywords=post_data["keywords"],
            )

            if success:
                QMessageBox.information(
                    self,
                    "Post Created",
                    f"Post created successfully!\n\n{message}\n\n"
                    "You can now open it in your editor to start writing.",
                )
                # Refresh git status after creating content
                self._update_git_status()
            else:
                QMessageBox.critical(
                    self,
                    "Error Creating Post",
                    f"Failed to create post:\n\n{message}",
                )

    def _create_new_micropost(self):
        """Create a new micropost."""
        if not self.hugo_manager.is_blog_available():
            QMessageBox.warning(
                self,
                "Hugo Blog Not Found",
                "Could not find a Hugo blog in the expected location.\n\n"
                "Please ensure you have a Hugo blog in the sibling directory "
                "'mkeyran.github.io' or check your blog configuration.",
            )
            return

        dialog = MicropostDialog(self)
        if dialog.exec() == QDialog.Accepted:
            micropost_data = dialog.get_micropost_data()

            # Create the micropost
            success, message = self.hugo_manager.create_micropost(micropost_data["filename"], micropost_data["content"])

            if success:
                QMessageBox.information(
                    self,
                    "Micropost Created",
                    f"Micropost created successfully!\n\n{message}",
                )
                # Refresh git status and content browser after creating content
                self._update_git_status()
                self.content_browser.refresh()
            else:
                QMessageBox.critical(
                    self,
                    "Error Creating Micropost",
                    f"Failed to create micropost:\n\n{message}",
                )

    def _create_new_conversation(self):
        """Create a new conversation."""
        if not self.hugo_manager.is_blog_available():
            QMessageBox.warning(
                self,
                "Hugo Blog Not Found",
                "Could not find a Hugo blog in the expected location.\n\n"
                "Please configure your blog path in Settings.",
            )
            return

        dialog = ConversationDialog(self)
        if dialog.exec() == QDialog.Accepted:
            conversation_data = dialog.get_conversation_data()

            # Create the conversation
            success, message = self.hugo_manager.create_conversation(
                title=conversation_data["title"],
                slug=conversation_data["slug"],
                language=conversation_data["language"],
                description=conversation_data["description"],
                tags=conversation_data["tags"],
                keywords=conversation_data["keywords"],
            )

            if success:
                QMessageBox.information(
                    self,
                    "Conversation Created",
                    f"Conversation created successfully!\n\n{message}\n\n"
                    "You can now open it in your editor to start writing.",
                )
                # Refresh git status after creating content
                self._update_git_status()
            else:
                QMessageBox.critical(
                    self,
                    "Error Creating Conversation",
                    f"Failed to create conversation:\n\n{message}",
                )

    def _commit_and_push(self):
        """Commit changes and push to remote repository."""
        # Check if this is a git repository
        if not self.git_manager.get_status().is_repo:
            QMessageBox.warning(
                self,
                "Not a Git Repository",
                "The blog directory is not a git repository.\n\n" "Please initialize git in your blog directory first.",
            )
            return

        # Get current git status to show in dialog
        status = self.git_manager.get_status()
        total_changes = status.modified_files + status.staged_files + status.untracked_files

        if total_changes == 0:
            QMessageBox.information(
                self,
                "No Changes",
                "There are no changes to commit.\n\nThe working directory is clean.",
            )
            return

        # Show commit dialog
        dialog = CommitDialog(self, self.git_manager)
        if dialog.exec() == QDialog.Accepted:
            commit_message = dialog.get_commit_message()

            # Perform commit and push
            success, message = self.git_manager.commit_and_push(commit_message)

            if success:
                QMessageBox.information(
                    self,
                    "Commit Successful",
                    f"Changes committed and pushed successfully!\n\n{message}",
                )
                # Refresh git status after successful commit
                self._update_git_status()
            else:
                # Check if this is an authentication error and offer commit-only option
                if "authentication" in message.lower() or "permission denied" in message.lower():
                    reply = QMessageBox.question(
                        self,
                        "Push Failed - Commit Only?",
                        f"{message}\n\nWould you like to commit the changes locally without pushing?\n\n"
                        "You can push later when authentication is resolved.",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes,
                    )

                    if reply == QMessageBox.StandardButton.Yes:
                        commit_success, commit_message = self.git_manager.commit_only(commit_message)
                        if commit_success:
                            QMessageBox.information(
                                self,
                                "Commit Successful",
                                f"Changes committed locally!\n\n{commit_message}",
                            )
                            # Refresh git status after successful commit
                            self._update_git_status()
                        else:
                            QMessageBox.critical(
                                self,
                                "Commit Failed",
                                f"Failed to commit changes:\n\n{commit_message}",
                            )
                else:
                    QMessageBox.critical(
                        self,
                        "Commit Failed",
                        f"Failed to commit and push changes:\n\n{message}",
                    )

    def _show_settings(self):
        """Show the Settings dialog."""
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # Refresh managers in case blog path changed
            self.hugo_manager = HugoManager()
            self.git_manager = GitManager(self.hugo_manager.get_blog_path())
            self.server_manager = HugoServerManager(self.hugo_manager.get_blog_path())

            # Update content browser with new hugo manager
            self.content_browser.hugo_manager = self.hugo_manager
            self.content_browser.refresh()

            # Update status
            self._update_git_status()
            self._update_server_status()

    def _show_about_dialog(self):
        """Show the About dialog."""
        QMessageBox.about(
            self,
            "About Hugo Blog Management Console",
            "Hugo Blog Management Console\n"
            "Version: 0.1.0\n\n"
            "A Qt-based tool for managing Hugo blogs.\n"
            "Simplifies common blog management operations.",
        )

    def _create_status_bar(self):
        """Create and configure the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Create git status label
        self.git_status_label = QLabel("Git: Loading...")
        self.status_bar.addPermanentWidget(self.git_status_label)

        # Create server status label
        self.server_status_label = QLabel("Server: Stopped")
        self.status_bar.addPermanentWidget(self.server_status_label)

        # Update status immediately
        self._update_git_status()
        self._update_server_status()

    def _setup_status_timer(self):
        """Set up timer for periodic git and server status updates."""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_git_status)
        self.status_timer.timeout.connect(self._update_server_status)
        # Update every 30 seconds
        self.status_timer.start(30000)

    def _update_git_status(self):
        """Update git status display."""
        status = self.git_manager.get_status()

        if not status.is_repo:
            self.git_status_label.setText("Git: Not a repository")
            self.commit_action.setEnabled(False)
            return

        status_parts = []

        # Show branch
        if status.current_branch:
            status_parts.append(f"Branch: {status.current_branch}")

        # Show file counts
        total_changes = status.modified_files + status.staged_files + status.untracked_files
        if total_changes > 0:
            status_parts.append(f"Changes: {total_changes}")

        # Show unpushed commits indicator
        if status.has_unpushed_commits:
            status_parts.append("Unpushed commits")

        # If no changes and no unpushed commits, show clean status
        if total_changes == 0 and not status.has_unpushed_commits:
            status_parts.append("Clean")

        self.git_status_label.setText(f"Git: {' | '.join(status_parts)}")
        
        # Enable/disable commit action based on whether there are changes to commit
        self.commit_action.setEnabled(status.is_repo and total_changes > 0)

    def _update_server_status(self):
        """Update Hugo server status display."""
        status = self.server_manager.get_status()

        if status.is_running:
            self.server_status_label.setText(f"Server: Running ({status.url})")
        else:
            self.server_status_label.setText("Server: Stopped")

    def _start_server(self):
        """Start the Hugo development server."""
        if not self.hugo_manager.is_blog_available():
            QMessageBox.warning(
                self,
                "Hugo Blog Not Found",
                "Could not find a Hugo blog in the expected location.\n\n"
                "Please configure your blog path in Settings.",
            )
            return

        if self.server_manager.is_running():
            QMessageBox.information(
                self,
                "Server Already Running",
                f"Hugo server is already running at {self.server_manager.get_server_url()}",
            )
            return

        success, message = self.server_manager.start_server()

        if success:
            QMessageBox.information(
                self,
                "Server Started",
                f"Hugo server started successfully!\n\n{message}",
            )
            self._update_server_status()
        else:
            QMessageBox.critical(
                self,
                "Server Start Failed",
                f"Failed to start Hugo server:\n\n{message}",
            )

    def _stop_server(self):
        """Stop the Hugo development server."""
        if not self.server_manager.is_running():
            QMessageBox.information(
                self,
                "Server Not Running",
                "Hugo server is not currently running.",
            )
            return

        success, message = self.server_manager.stop_server()

        if success:
            QMessageBox.information(
                self,
                "Server Stopped",
                f"Hugo server stopped successfully!\n\n{message}",
            )
            self._update_server_status()
        else:
            QMessageBox.critical(
                self,
                "Server Stop Failed",
                f"Failed to stop Hugo server:\n\n{message}",
            )

    def _restart_server(self):
        """Restart the Hugo development server."""
        if not self.hugo_manager.is_blog_available():
            QMessageBox.warning(
                self,
                "Hugo Blog Not Found",
                "Could not find a Hugo blog in the expected location.\n\n"
                "Please configure your blog path in Settings.",
            )
            return

        success, message = self.server_manager.restart_server()

        if success:
            QMessageBox.information(
                self,
                "Server Restarted",
                f"Hugo server restarted successfully!\n\n{message}",
            )
            self._update_server_status()
        else:
            QMessageBox.critical(
                self,
                "Server Restart Failed",
                f"Failed to restart Hugo server:\n\n{message}",
            )

    def _preview_site(self):
        """Open the site in the default web browser."""
        if not self.server_manager.is_running():
            # Ask if user wants to start server
            reply = QMessageBox.question(
                self,
                "Server Not Running",
                "Hugo server is not currently running.\n\n" "Would you like to start the server first?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )

            if reply == QMessageBox.StandardButton.Yes:
                success, message = self.server_manager.start_server()
                if not success:
                    QMessageBox.critical(
                        self,
                        "Server Start Failed",
                        f"Failed to start Hugo server:\n\n{message}",
                    )
                    return
                self._update_server_status()
            else:
                return

        # Open browser to server URL
        import platform
        import subprocess
        import webbrowser

        server_url = self.server_manager.get_server_url()

        # Try platform-specific browser opening with fallback
        try:
            system = platform.system()

            if system == "Linux":
                # Try multiple approaches for Linux due to xdg-open issues
                linux_commands = [
                    ["xdg-open", server_url],
                    ["vivaldi", server_url],
                    ["firefox", server_url],
                    ["chromium", server_url],
                    ["google-chrome", server_url],
                    ["sensible-browser", server_url],
                ]

                success = False

                for cmd in linux_commands:
                    try:
                        result = subprocess.run(
                            cmd,
                            timeout=10,
                            capture_output=True,
                            text=True,
                        )

                        # Special handling for xdg-open KDE compatibility issues
                        if cmd[0] == "xdg-open" and hasattr(result, "stderr") and result.stderr:
                            error_indicators = [
                                "kfmclient: command not found",
                                "integer expression expected",
                                "No such file or directory",
                            ]
                            try:
                                if any(indicator in result.stderr for indicator in error_indicators):
                                    continue
                            except (TypeError, AttributeError):
                                pass

                        success = True
                        break
                    except FileNotFoundError:
                        continue
                    except subprocess.TimeoutExpired:
                        success = True
                        break

                if not success:
                    # Fall back to webbrowser module
                    webbrowser.open(server_url)
            else:
                # Use webbrowser for other platforms
                webbrowser.open(server_url)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Browser Launch Failed",
                f"Failed to open browser:\n\n{e}\n\n" f"Please manually navigate to: {server_url}",
            )

    def closeEvent(self, event):
        """Handle application close event."""
        # Clean up server manager
        if hasattr(self, "server_manager"):
            self.server_manager.cleanup()
        event.accept()
