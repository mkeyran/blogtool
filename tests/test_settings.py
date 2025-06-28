"""Tests for settings management functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from blogtool.core.settings import Settings, get_settings


class TestSettings:
    """Test settings management functionality."""

    def test_settings_initialization(self):
        """Test settings initialization with defaults."""
        with patch("blogtool.core.settings.Settings._get_config_dir") as mock_config_dir:
            temp_dir = Path(tempfile.mkdtemp())
            mock_config_dir.return_value = temp_dir

            settings = Settings()

            # Should have default values
            assert settings.get("editor.command") == ""
            assert settings.get("git.auto_generate_messages") is True
            assert settings.get("ui.auto_refresh_interval") == 30
            assert isinstance(settings.get("editor.available_editors"), list)

    def test_settings_persistence(self):
        """Test that settings are saved and loaded correctly."""
        with patch("blogtool.core.settings.Settings._get_config_dir") as mock_config_dir:
            temp_dir = Path(tempfile.mkdtemp())
            mock_config_dir.return_value = temp_dir

            # Create settings and modify values
            settings1 = Settings()
            settings1.set("editor.command", "vim")
            settings1.set("git.auto_generate_messages", False)
            settings1.set("ui.auto_refresh_interval", 60)

            # Create new settings instance (should load from file)
            settings2 = Settings()
            assert settings2.get("editor.command") == "vim"
            assert settings2.get("git.auto_generate_messages") is False
            assert settings2.get("ui.auto_refresh_interval") == 60

    def test_settings_file_corruption_handling(self):
        """Test handling of corrupted settings file."""
        with patch("blogtool.core.settings.Settings._get_config_dir") as mock_config_dir:
            temp_dir = Path(tempfile.mkdtemp())
            mock_config_dir.return_value = temp_dir

            # Create corrupted settings file
            settings_file = temp_dir / "blogtool_settings.json"
            settings_file.write_text("{ invalid json content")

            # Should fall back to defaults
            settings = Settings()
            assert settings.get("editor.command") == ""
            assert settings.get("git.auto_generate_messages") is True

    def test_deep_update_functionality(self):
        """Test deep update of nested settings."""
        with patch("blogtool.core.settings.Settings._get_config_dir") as mock_config_dir:
            temp_dir = Path(tempfile.mkdtemp())
            mock_config_dir.return_value = temp_dir

            settings = Settings()

            # Test nested setting update
            settings.set("editor.command", "code")
            settings.set("editor.new_setting", "value")

            assert settings.get("editor.command") == "code"
            assert settings.get("editor.new_setting") == "value"
            # Should preserve other editor settings
            assert isinstance(settings.get("editor.available_editors"), list)

    def test_get_editor_command_auto_detection(self):
        """Test editor command auto-detection."""
        with patch("blogtool.core.settings.Settings._get_config_dir") as mock_config_dir:
            temp_dir = Path(tempfile.mkdtemp())
            mock_config_dir.return_value = temp_dir

            settings = Settings()

            # Mock successful editor detection
            with patch.object(settings, "_detect_available_editor") as mock_detect:
                mock_detect.return_value = "code"

                # Should return detected editor when none configured
                editor = settings.get_editor_command()
                assert editor == "code"
                mock_detect.assert_called_once()

    def test_get_editor_command_configured(self):
        """Test editor command when explicitly configured."""
        with patch("blogtool.core.settings.Settings._get_config_dir") as mock_config_dir:
            temp_dir = Path(tempfile.mkdtemp())
            mock_config_dir.return_value = temp_dir

            settings = Settings()
            settings.set("editor.command", "vim")

            # Should return configured editor without auto-detection
            with patch.object(settings, "_detect_available_editor") as mock_detect:
                editor = settings.get_editor_command()
                assert editor == "vim"
                mock_detect.assert_not_called()

    @patch("subprocess.run")
    def test_detect_available_editor_success(self, mock_subprocess):
        """Test successful editor detection."""
        with patch("blogtool.core.settings.Settings._get_config_dir") as mock_config_dir:
            temp_dir = Path(tempfile.mkdtemp())
            mock_config_dir.return_value = temp_dir

            settings = Settings()
            mock_subprocess.return_value = Mock(returncode=0)

            # Should return first available editor
            available_editors = ["nonexistent", "code", "vim"]
            with patch.object(settings, "get") as mock_get:
                mock_get.return_value = available_editors
                mock_subprocess.side_effect = [
                    FileNotFoundError(),  # nonexistent fails
                    Mock(returncode=0),  # code succeeds
                ]

                editor = settings._detect_available_editor(available_editors)
                assert editor == "code"

    @patch("subprocess.run")
    def test_detect_available_editor_none_found(self, mock_subprocess):
        """Test editor detection when no editors are available."""
        with patch("blogtool.core.settings.Settings._get_config_dir") as mock_config_dir:
            temp_dir = Path(tempfile.mkdtemp())
            mock_config_dir.return_value = temp_dir

            settings = Settings()
            mock_subprocess.side_effect = FileNotFoundError()

            # Should return None when no editors found
            available_editors = ["nonexistent1", "nonexistent2"]
            editor = settings._detect_available_editor(available_editors)
            assert editor is None

    def test_reset_to_defaults(self):
        """Test resetting settings to default values."""
        with patch("blogtool.core.settings.Settings._get_config_dir") as mock_config_dir:
            temp_dir = Path(tempfile.mkdtemp())
            mock_config_dir.return_value = temp_dir

            # Create a fresh settings file for this test
            config_file = temp_dir / "blogtool_settings.json"
            if config_file.exists():
                config_file.unlink()

            settings = Settings()

            # Modify settings
            settings.set("editor.command", "vim")
            settings.set("git.auto_generate_messages", False)

            # Verify changes were made
            assert settings.get("editor.command") == "vim"
            assert settings.get("git.auto_generate_messages") is False

            # Reset to defaults
            settings.reset_to_defaults()

            # Should have default values
            assert settings.get("editor.command") == ""
            assert settings.get("git.auto_generate_messages") is True

    def test_global_settings_instance(self):
        """Test global settings instance functionality."""
        # Should return same instance on multiple calls
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_config_dir_creation(self):
        """Test that config directory is created if it doesn't exist."""
        with patch("blogtool.core.settings.Path.home") as mock_home:
            temp_dir = Path(tempfile.mkdtemp())
            mock_home.return_value = temp_dir

            with patch("platform.system", return_value="Linux"):
                settings = Settings()
                expected_dir = temp_dir / ".config" / "blogtool"
                assert expected_dir.exists()
                assert settings.config_dir == expected_dir

    def test_platform_specific_defaults(self):
        """Test platform-specific default values."""
        with patch("blogtool.core.settings.Settings._get_config_dir") as mock_config_dir:
            temp_dir = Path(tempfile.mkdtemp())
            mock_config_dir.return_value = temp_dir

            # Test macOS defaults
            with patch("platform.system", return_value="Darwin"):
                settings = Settings()
                editors = settings.get("editor.available_editors")
                assert "open -t" in editors

            # Test Linux defaults
            with patch("platform.system", return_value="Linux"):
                settings = Settings()
                editors = settings.get("editor.available_editors")
                assert "gedit" in editors
                assert "open -t" not in editors
