"""Tests for the main window functionality."""

import pytest
from PySide6.QtWidgets import QApplication

from blogtool.ui.main_window import MainWindow


@pytest.fixture
def qt_app():
    """Fixture to provide a QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app if it was already running


def test_main_window_creation(qt_app):
    """Test that MainWindow can be created."""
    window = MainWindow()
    assert window.windowTitle() == "Hugo Blog Management Console"
    assert window.size().width() == 800
    assert window.size().height() == 600


def test_main_window_has_menu_bar(qt_app):
    """Test that MainWindow has a menu bar with expected menus."""
    window = MainWindow()
    menubar = window.menuBar()

    # Check that menu bar exists
    assert menubar is not None

    # Check that expected menus exist
    menu_titles = [action.text() for action in menubar.actions()]
    assert "&File" in menu_titles
    assert "&Help" in menu_titles
