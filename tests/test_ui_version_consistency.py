"""Unit tests for UI Version & Release Consistency (Sprint 14.0.6)."""

import pytest
from PySide6.QtWidgets import QApplication

from core.version import APP_NAME, APP_VERSION
from app.screens.dashboard import Dashboard
from app.screens.settings import Settings
from config.path_config import get_base_data_dir


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication(["-platform", "offscreen"])


def test_core_version_is_stable_1_0_0():
    assert APP_NAME == "AlphaForge"
    assert APP_VERSION == "1.0.0"


def test_dashboard_version_display(qapp):
    dashboard = Dashboard()
    assert dashboard is not None
    # Check that dashboard welcome_lbl text contains APP_VERSION and 'Stable'
    welcome_text = dashboard.findChild(object, "").parent().findChildren(object)
    found_stable_welcome = False
    for child in dashboard.findChildren(object):
        if hasattr(child, "text"):
            txt = child.text()
            if "Welcome to AlphaForge" in txt:
                assert "v1.0.0 Stable" in txt
                assert "rc1" not in txt
                found_stable_welcome = True
    assert found_stable_welcome, "Dashboard welcome label with v1.0.0 Stable not found"


def test_settings_version_and_path_display(qapp):
    settings = Settings()
    assert settings is not None

    found_version = False
    found_status = False
    found_base_dir = False
    base_dir_str = str(get_base_data_dir())

    for child in settings.findChildren(object):
        if hasattr(child, "text"):
            txt = child.text()
            if "Release Version:" in txt:
                assert "v1.0.0 (Stable Release)" in txt
                found_version = True
            if "Release Status:" in txt:
                assert "Version 1.0.0 Stable Release (Chapter 20 Completed)" in txt
                found_status = True
            if "Base Data Directory:" in txt:
                assert base_dir_str in txt
                found_base_dir = True

    assert found_version, "Settings release version text not found"
    assert found_status, "Settings release status text not found"
    assert found_base_dir, "Settings base data directory path not found"
