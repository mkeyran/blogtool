"""Settings dialog for configuring application preferences."""

import subprocess

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from ..core.settings import get_settings


class SettingsDialog(QDialog):
    """Dialog for configuring application settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(500, 400)

        self.settings = get_settings()
        self._setup_ui()
        self._load_current_settings()

    def _setup_ui(self):
        """Set up the settings dialog UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Editor settings group
        editor_group = QGroupBox("Editor Settings")
        editor_layout = QFormLayout()
        editor_group.setLayout(editor_layout)

        # Editor command input
        editor_row = QHBoxLayout()
        self.editor_input = QLineEdit()
        self.editor_input.setPlaceholderText("Leave empty for auto-detection")
        editor_row.addWidget(self.editor_input)

        # Test editor button
        self.test_editor_btn = QPushButton("Test")
        self.test_editor_btn.clicked.connect(self._test_editor)
        self.test_editor_btn.setMaximumWidth(60)
        editor_row.addWidget(self.test_editor_btn)

        editor_layout.addRow("Editor Command:", editor_row)

        # Available editors dropdown
        self.available_editors = QComboBox()
        self.available_editors.addItem("Auto-detect", "")

        # Populate with platform-specific editors
        default_editors = self.settings.get("editor.available_editors", [])
        for editor in default_editors:
            self.available_editors.addItem(editor, editor)

        self.available_editors.currentTextChanged.connect(self._on_editor_selection_changed)
        editor_layout.addRow("Quick Select:", self.available_editors)

        # Editor status label
        self.editor_status = QLabel()
        self.editor_status.setStyleSheet("color: #666; font-size: 10px;")
        editor_layout.addRow("Status:", self.editor_status)

        layout.addWidget(editor_group)

        # Blog settings group
        blog_group = QGroupBox("Blog Settings")
        blog_layout = QFormLayout()
        blog_group.setLayout(blog_layout)

        # Blog path input
        blog_path_row = QHBoxLayout()
        self.blog_path_input = QLineEdit()
        self.blog_path_input.setPlaceholderText("Leave empty for auto-detection")
        blog_path_row.addWidget(self.blog_path_input)

        # Browse button
        self.browse_blog_btn = QPushButton("Browse")
        self.browse_blog_btn.clicked.connect(self._browse_blog_path)
        self.browse_blog_btn.setMaximumWidth(80)
        blog_path_row.addWidget(self.browse_blog_btn)

        blog_layout.addRow("Blog Path:", blog_path_row)

        # Auto-detect checkbox
        self.auto_detect_blog_cb = QCheckBox("Auto-detect blog path")
        self.auto_detect_blog_cb.stateChanged.connect(self._on_auto_detect_changed)
        blog_layout.addRow(self.auto_detect_blog_cb)

        # Blog status label
        self.blog_status = QLabel()
        self.blog_status.setStyleSheet("color: #666; font-size: 10px;")
        blog_layout.addRow("Status:", self.blog_status)

        layout.addWidget(blog_group)

        # Git settings group
        git_group = QGroupBox("Git Settings")
        git_layout = QFormLayout()
        git_group.setLayout(git_layout)

        # Auto-generate commit messages checkbox
        self.auto_generate_cb = QCheckBox("Auto-generate commit messages using LLM")
        git_layout.addRow(self.auto_generate_cb)

        layout.addWidget(git_group)

        # UI settings group
        ui_group = QGroupBox("Interface Settings")
        ui_layout = QFormLayout()
        ui_group.setLayout(ui_layout)

        # Auto-refresh interval
        self.refresh_interval = QSpinBox()
        self.refresh_interval.setRange(5, 300)  # 5 seconds to 5 minutes
        self.refresh_interval.setSuffix(" seconds")
        self.refresh_interval.setValue(30)
        ui_layout.addRow("Auto-refresh interval:", self.refresh_interval)

        # Show preview checkbox
        self.show_preview_cb = QCheckBox("Show content preview in browser")
        ui_layout.addRow(self.show_preview_cb)

        layout.addWidget(ui_group)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Connect restore defaults button
        restore_btn = button_box.button(QDialogButtonBox.RestoreDefaults)
        restore_btn.clicked.connect(self._restore_defaults)

        layout.addWidget(button_box)

        # Update editor status initially
        self._update_editor_status()
        self._update_blog_status()

    def _load_current_settings(self):
        """Load current settings into the dialog."""
        # Editor settings
        editor_command = self.settings.get("editor.command", "")
        self.editor_input.setText(editor_command)

        # Set combobox selection
        index = self.available_editors.findData(editor_command)
        if index >= 0:
            self.available_editors.setCurrentIndex(index)

        # Blog settings
        blog_path = self.settings.get("blog.path", "")
        self.blog_path_input.setText(blog_path)

        auto_detect_blog = self.settings.get("blog.auto_detect", True)
        self.auto_detect_blog_cb.setChecked(auto_detect_blog)

        # Git settings
        auto_generate = self.settings.get("git.auto_generate_messages", True)
        self.auto_generate_cb.setChecked(auto_generate)

        # UI settings
        refresh_interval = self.settings.get("ui.auto_refresh_interval", 30)
        self.refresh_interval.setValue(refresh_interval)

        show_preview = self.settings.get("ui.show_preview_in_browser", True)
        self.show_preview_cb.setChecked(show_preview)

    def _on_editor_selection_changed(self, text):
        """Handle editor selection change."""
        if text != "Auto-detect":
            self.editor_input.setText(text)
        else:
            self.editor_input.setText("")
        self._update_editor_status()

    def _test_editor(self):
        """Test the current editor command."""
        editor_command = self.editor_input.text().strip()

        if not editor_command:
            # Test auto-detected editor
            detected_editor = self.settings._detect_available_editor(self.settings.get("editor.available_editors", []))
            if detected_editor:
                QMessageBox.information(
                    self,
                    "Editor Test",
                    f"Auto-detected editor: {detected_editor}\n\nThe editor appears to be available.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Editor Test",
                    "No suitable editor could be auto-detected.\n\nPlease specify an editor command manually.",
                )
            return

        # Test specified editor
        try:
            editor_parts = editor_command.split()
            subprocess.run(
                [editor_parts[0], "--help"] if len(editor_parts) == 1 else [editor_parts[0], "--version"],
                capture_output=True,
                timeout=5,
            )
            QMessageBox.information(self, "Editor Test", f"Editor command '{editor_command}' is available and working.")
        except FileNotFoundError:
            QMessageBox.warning(
                self,
                "Editor Test",
                f"Editor command '{editor_command}' was not found.\n\nPlease check the command and try again.",
            )
        except subprocess.TimeoutExpired:
            QMessageBox.warning(
                self,
                "Editor Test",
                f"Editor command '{editor_command}' timed out.\n\nThe command may not support --help or --version.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Editor Test", f"Error testing editor command:\n\n{e}")

    def _update_editor_status(self):
        """Update the editor status label."""
        editor_command = self.editor_input.text().strip()

        if not editor_command:
            detected_editor = self.settings._detect_available_editor(self.settings.get("editor.available_editors", []))
            if detected_editor:
                self.editor_status.setText(f"Auto-detected: {detected_editor}")
                self.editor_status.setStyleSheet("color: green; font-size: 10px;")
            else:
                self.editor_status.setText("No editor auto-detected")
                self.editor_status.setStyleSheet("color: orange; font-size: 10px;")
        else:
            self.editor_status.setText(f"Custom: {editor_command}")
            self.editor_status.setStyleSheet("color: blue; font-size: 10px;")

    def _browse_blog_path(self):
        """Browse for blog directory."""
        current_path = self.blog_path_input.text().strip() or self.settings.get_blog_path() or ""

        directory = QFileDialog.getExistingDirectory(
            self, "Select Hugo Blog Directory", current_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        if directory:
            # Verify it's a Hugo site
            from pathlib import Path

            if self.settings._is_hugo_site(Path(directory)):
                self.blog_path_input.setText(directory)
                self.auto_detect_blog_cb.setChecked(False)
                self._update_blog_status()
            else:
                QMessageBox.warning(
                    self,
                    "Invalid Hugo Site",
                    f"The selected directory does not appear to be a Hugo site.\n\n"
                    f"A Hugo site should contain:\n"
                    f"• A configuration file (hugo.toml, config.toml, etc.)\n"
                    f"• A 'content' directory\n\n"
                    f"Selected: {directory}",
                )

    def _on_auto_detect_changed(self):
        """Handle auto-detect checkbox change."""
        if self.auto_detect_blog_cb.isChecked():
            self.blog_path_input.setText("")
        self._update_blog_status()

    def _update_blog_status(self):
        """Update the blog status label."""
        if self.auto_detect_blog_cb.isChecked() or not self.blog_path_input.text().strip():
            # Auto-detection mode
            detected_path = self.settings.get_blog_path()
            if detected_path:
                self.blog_status.setText(f"Auto-detected: {detected_path}")
                self.blog_status.setStyleSheet("color: green; font-size: 10px;")
            else:
                self.blog_status.setText("No Hugo site auto-detected")
                self.blog_status.setStyleSheet("color: orange; font-size: 10px;")
        else:
            # Manual path mode
            manual_path = self.blog_path_input.text().strip()
            from pathlib import Path

            if manual_path and self.settings._is_hugo_site(Path(manual_path)):
                self.blog_status.setText(f"Valid Hugo site: {manual_path}")
                self.blog_status.setStyleSheet("color: green; font-size: 10px;")
            elif manual_path:
                self.blog_status.setText("Invalid Hugo site")
                self.blog_status.setStyleSheet("color: red; font-size: 10px;")
            else:
                self.blog_status.setText("No path specified")
                self.blog_status.setStyleSheet("color: orange; font-size: 10px;")

    def _restore_defaults(self):
        """Restore all settings to default values."""
        reply = QMessageBox.question(
            self,
            "Restore Defaults",
            "Are you sure you want to restore all settings to their default values?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.settings.reset_to_defaults()
            self._load_current_settings()
            self._update_editor_status()
            self._update_blog_status()

    def accept(self):
        """Save settings and accept the dialog."""
        # Save editor settings
        editor_command = self.editor_input.text().strip()
        self.settings.set("editor.command", editor_command)

        # Save blog settings
        if self.auto_detect_blog_cb.isChecked():
            self.settings.enable_blog_auto_detection()
        else:
            blog_path = self.blog_path_input.text().strip()
            if blog_path:
                self.settings.set_blog_path(blog_path)
            else:
                self.settings.enable_blog_auto_detection()

        # Save git settings
        self.settings.set("git.auto_generate_messages", self.auto_generate_cb.isChecked())

        # Save UI settings
        self.settings.set("ui.auto_refresh_interval", self.refresh_interval.value())
        self.settings.set("ui.show_preview_in_browser", self.show_preview_cb.isChecked())

        super().accept()

    def get_editor_command(self) -> str:
        """Get the configured editor command."""
        return self.settings.get_editor_command() or ""
