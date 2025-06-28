"""Settings management for the blog tool."""

import json
import platform
from pathlib import Path
from typing import Any, Dict, Optional


class Settings:
    """Manages application settings with persistent storage."""

    def __init__(self):
        """Initialize settings with default values."""
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "blogtool_settings.json"
        self._defaults = self._get_default_settings()
        self._settings = self._load_settings()

    def _get_config_dir(self) -> Path:
        """Get the configuration directory based on the platform."""
        if platform.system() == "Darwin":  # macOS
            config_dir = Path.home() / "Library" / "Application Support" / "BlogTool"
        elif platform.system() == "Linux":
            # Follow XDG Base Directory Specification
            xdg_config = Path.home() / ".config"
            config_dir = xdg_config / "blogtool"
        else:  # Windows fallback
            config_dir = Path.home() / ".blogtool"

        # Create directory if it doesn't exist
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings based on platform."""
        system = platform.system()

        # Default editors by platform
        if system == "Darwin":  # macOS
            default_editors = ["code", "subl", "atom", "vim", "nano", "open -t"]
        elif system == "Linux":
            default_editors = ["code", "subl", "atom", "vim", "nano", "gedit"]
        else:  # Windows fallback
            default_editors = ["code", "notepad++", "notepad"]

        return {
            "editor": {
                "command": "",  # Empty means use auto-detection
                "available_editors": default_editors,
            },
            "git": {
                "auto_generate_messages": True,
                "default_templates": [
                    "Add new micropost",
                    "Update existing content",
                    "Fix content issues",
                    "Add new blog post",
                    "Update blog configuration",
                ],
            },
            "ui": {
                "auto_refresh_interval": 30,  # seconds
                "show_preview_in_browser": True,
            },
        }

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file, falling back to defaults."""
        import copy

        if not self.config_file.exists():
            return copy.deepcopy(self._defaults)

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                saved_settings = json.load(f)

            # Merge with defaults to ensure all keys exist
            settings = copy.deepcopy(self._defaults)
            self._deep_update(settings, saved_settings)
            return settings
        except (json.JSONDecodeError, OSError):
            # If file is corrupted, use defaults
            return copy.deepcopy(self._defaults)

    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> None:
        """Recursively update base_dict with values from update_dict."""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    def save(self) -> None:
        """Save current settings to file."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except OSError:
            # Silently fail if we can't save settings
            pass

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get a setting value using dot notation (e.g., 'editor.command')."""
        keys = key_path.split(".")
        value = self._settings

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any) -> None:
        """Set a setting value using dot notation (e.g., 'editor.command')."""
        keys = key_path.split(".")
        settings_ref = self._settings

        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in settings_ref:
                settings_ref[key] = {}
            settings_ref = settings_ref[key]

        # Set the value
        settings_ref[keys[-1]] = value
        self.save()

    def get_editor_command(self) -> Optional[str]:
        """Get the configured editor command, with auto-detection fallback."""
        configured_editor = self.get("editor.command", "").strip()

        if configured_editor:
            return configured_editor

        # Auto-detect available editor
        available_editors = self.get("editor.available_editors", [])
        return self._detect_available_editor(available_editors)

    def _detect_available_editor(self, editors: list) -> Optional[str]:
        """Detect the first available editor from the list."""
        import subprocess

        for editor in editors:
            try:
                # Handle complex commands like "open -t"
                editor_parts = editor.split()
                subprocess.run(
                    [editor_parts[0], "--help"] if len(editor_parts) == 1 else [editor_parts[0], "--version"],
                    capture_output=True,
                    timeout=3,
                )
                return editor
            except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
                continue

        return None

    def set_editor(self, editor_command: str) -> None:
        """Set the preferred editor command."""
        self.set("editor.command", editor_command)

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all current settings."""
        return self._settings.copy()

    def reset_to_defaults(self) -> None:
        """Reset all settings to default values."""
        import copy

        self._settings = copy.deepcopy(self._defaults)
        self.save()


# Global settings instance
_settings_instance = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
