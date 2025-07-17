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
            "blog": {
                "path": "",  # Empty means use auto-detection (playground or sibling directory)
                "auto_detect": True,
            },
            "hugo": {
                "executable_path": "",  # Empty means use auto-detection
                "auto_detect": True,
            },
            "go": {
                "executable_path": "",  # Empty means use auto-detection
                "auto_detect": True,
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

    def get_blog_path(self) -> Optional[str]:
        """Get the configured blog path, with auto-detection fallback."""
        configured_path = self.get("blog.path", "").strip()
        auto_detect = self.get("blog.auto_detect", True)

        if configured_path and Path(configured_path).exists():
            return configured_path

        if auto_detect:
            # Use the same logic as HugoManager for auto-detection

            current_dir = Path.cwd()

            # Look in playground directory (for testing/development)
            playground_blog = current_dir / "playground"
            if self._is_hugo_site(playground_blog):
                return str(playground_blog)

            # Look in sibling directory as mentioned in requirements
            sibling_blog = current_dir.parent / "mkeyran.github.io"
            if self._is_hugo_site(sibling_blog):
                return str(sibling_blog)

        return None

    def set_blog_path(self, blog_path: str) -> None:
        """Set the blog path and disable auto-detection."""
        self.set("blog.path", blog_path)
        self.set("blog.auto_detect", False)

    def enable_blog_auto_detection(self) -> None:
        """Enable blog path auto-detection and clear manual path."""
        self.set("blog.path", "")
        self.set("blog.auto_detect", True)

    def get_hugo_executable(self) -> Optional[str]:
        """Get the configured Hugo executable path, with auto-detection fallback."""
        configured_hugo = self.get("hugo.executable_path", "").strip()
        auto_detect = self.get("hugo.auto_detect", True)

        if configured_hugo and Path(configured_hugo).exists():
            return configured_hugo

        if auto_detect:
            return self._detect_hugo_executable()

        return None

    def set_hugo_executable(self, hugo_path: str) -> None:
        """Set the Hugo executable path and disable auto-detection."""
        self.set("hugo.executable_path", hugo_path)
        self.set("hugo.auto_detect", False)

    def enable_hugo_auto_detection(self) -> None:
        """Enable Hugo executable auto-detection and clear manual path."""
        self.set("hugo.executable_path", "")
        self.set("hugo.auto_detect", True)

    def _detect_hugo_executable(self) -> Optional[str]:
        """Detect Hugo executable in common locations."""
        import subprocess
        
        # Common locations where Hugo might be installed
        common_paths = [
            "hugo",  # Try PATH first
            "/usr/local/bin/hugo",
            "/opt/homebrew/bin/hugo",
            "/usr/bin/hugo",
        ]
        
        for hugo_path in common_paths:
            try:
                result = subprocess.run(
                    [hugo_path, "version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return hugo_path
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        return None

    def get_go_executable(self) -> Optional[str]:
        """Get the configured Go executable path, with auto-detection fallback."""
        configured_go = self.get("go.executable_path", "").strip()
        auto_detect = self.get("go.auto_detect", True)

        if configured_go and Path(configured_go).exists():
            return configured_go

        if auto_detect:
            return self._detect_go_executable()

        return None

    def set_go_executable(self, go_path: str) -> None:
        """Set the Go executable path and disable auto-detection."""
        self.set("go.executable_path", go_path)
        self.set("go.auto_detect", False)

    def enable_go_auto_detection(self) -> None:
        """Enable Go executable auto-detection and clear manual path."""
        self.set("go.executable_path", "")
        self.set("go.auto_detect", True)

    def _detect_go_executable(self) -> Optional[str]:
        """Detect Go executable in common locations."""
        import subprocess
        
        # Common locations where Go might be installed
        common_paths = [
            "go",  # Try PATH first
            "/usr/local/go/bin/go",
            "/opt/homebrew/bin/go",
            "/usr/bin/go",
            "/usr/local/bin/go",
        ]
        
        for go_path in common_paths:
            try:
                result = subprocess.run(
                    [go_path, "version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return go_path
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        return None

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
