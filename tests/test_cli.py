"""Tests for the CLI module."""

from unittest.mock import MagicMock, patch

from blogtool.cli import main


def test_main_prints_version_and_starts_app():
    """Test that main function prints version information and starts Qt app."""
    with (
        patch("builtins.print") as mock_print,
        patch("sys.exit") as mock_exit,
        patch("blogtool.cli.BlogToolApp") as mock_app_class,
    ):

        # Setup mock app instance
        mock_app = MagicMock()
        mock_app.run.return_value = 0
        mock_app_class.return_value = mock_app

        main()

        # Verify print calls
        assert mock_print.call_count == 3
        mock_print.assert_any_call("Hugo Blog Management Console")
        mock_print.assert_any_call("Version: 0.1.0")
        mock_print.assert_any_call("Starting GUI application...")

        # Verify app creation and run
        mock_app_class.assert_called_once()
        mock_app.run.assert_called_once()
        mock_exit.assert_called_once_with(0)
