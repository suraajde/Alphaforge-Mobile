import pytest
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.screens.settings import Settings


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_settings_screen_registration(qapp):
    win = MainWindow()

    # Verify settings is instantiated on MainWindow
    assert hasattr(win, "settings")
    assert isinstance(win.settings, Settings)

    # Verify settings is added to QStackedWidget
    assert win.pages.indexOf(win.settings) != -1


def test_settings_sidebar_navigation(qapp):
    win = MainWindow()

    # Verify sidebar button exists
    assert hasattr(win.sidebar, "settings_btn")

    # Simulate sidebar click for Settings
    win.sidebar.settings_btn.click()

    # Verify current widget switched to settings
    assert win.pages.currentWidget() == win.settings
