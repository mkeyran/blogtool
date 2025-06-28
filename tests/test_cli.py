"""Tests for the CLI module."""

from unittest.mock import patch

from blogtool.cli import main


def test_main_prints_version():
    """Test that main function prints version information."""
    with patch("builtins.print") as mock_print, patch("sys.exit") as mock_exit:

        main()

        # Verify print calls
        assert mock_print.call_count == 3
        mock_print.assert_any_call("Hugo Blog Management Console")
        mock_print.assert_any_call("Version: 0.1.0")
        mock_print.assert_any_call("Starting GUI application...")

        # Verify exit is called
        mock_exit.assert_called_once_with(0)
