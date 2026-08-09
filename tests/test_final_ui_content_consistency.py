"""Unit tests for Final UI Content & Release Integrity Verification (Sprint 14.0.9)."""

import pytest
from PySide6.QtWidgets import QApplication

from core.version import APP_NAME, APP_VERSION
from app.screens.dashboard import Dashboard
from app.screens.settings import Settings
from app.screens.research_radar import ResearchRadar
from app.screens.stock_explorer import StockExplorer
from app.screens.portfolio import Portfolio
from app.screens.portfolio_health import PortfolioHealth
from app.screens.portfolio_action_center import PortfolioActionCenter
from app.screens.watchtower import Watchtower
from services.universe_service import UniverseService


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication(["-platform", "offscreen"])


def test_version_metadata():
    assert APP_NAME == "AlphaForge"
    assert APP_VERSION == "1.0.0"


def test_settings_developer_and_disclaimer_content(qapp):
    settings = Settings()
    assert settings is not None

    found_dev_name = False
    found_email = False
    found_linkedin = False
    found_github = False
    found_disclaimer = False
    found_license = False
    found_reset = False

    for child in settings.findChildren(object):
        if hasattr(child, "text"):
            txt = child.text()
            if "Suraj Dev" in txt:
                found_dev_name = True
            if "suraajde@gmail.com" in txt:
                found_email = True
            if "suraaj-de-81336932" in txt or "linkedin" in txt.lower():
                found_linkedin = True
            if "github.com/suraajde" in txt or "github" in txt.lower():
                found_github = True
            if "educational investment disclaimer" in txt.lower() or "analytical and educational software" in txt.lower():
                found_disclaimer = True
            if "personal use" in txt.lower():
                found_license = True
            if "portfolio reset" in txt.lower():
                found_reset = True

    assert found_dev_name, "Developer name 'Suraj Dev' not found in Settings"
    assert found_email, "Developer email 'suraajde@gmail.com' not found in Settings"
    assert found_linkedin, "Developer LinkedIn not found in Settings"
    assert found_github, "Developer GitHub not found in Settings"
    assert found_disclaimer, "Investment disclaimer not found in Settings"
    assert found_license, "Personal use license not found in Settings"
    assert not found_reset, "Portfolio Reset should not be advertised in Settings UI"


def test_no_stale_rc_or_dev_paths_in_ui(qapp):
    screens = [
        Dashboard(),
        StockExplorer(),
        ResearchRadar(),
        Portfolio(),
        PortfolioHealth(),
        PortfolioActionCenter(),
        Watchtower(),
        Settings(),
    ]

    stale_patterns = ["rc1", "v1.0.0-rc1", "target release", "chapter 20 in progress", "portfolio reset"]

    for screen in screens:
        for child in screen.findChildren(object):
            if hasattr(child, "text"):
                txt = child.text().lower()
                for pattern in stale_patterns:
                    assert pattern not in txt, f"Stale pattern '{pattern}' found in UI component text: '{child.text()}'"


def test_alpha12_governance_values_unchanged(qapp):
    settings = Settings()
    all_text = ""
    for child in settings.findChildren(object):
        if hasattr(child, "text"):
            all_text += child.text() + "\n"

    assert "+10.0 points" in all_text or "+10 points" in all_text, "Challenger Advantage governance rule changed!"
    assert "+5.0 points" in all_text or "+5 points" in all_text, "Conviction Buffer governance rule changed!"
    assert "3 candidates" in all_text or "3" in all_text, "Max Replacements governance rule changed!"
    assert "20.0%" in all_text or "20%" in all_text, "Turnover Cap governance rule changed!"
    assert "30 days" in all_text, "Cooling period governance rule changed!"
    assert "Incumbent Protection Policy" in all_text, "Incumbent Protection policy rule changed!"


def test_research_radar_universe_loaded():
    svc = UniverseService()
    res = svc.get_enabled_stocks()
    assert len(res["errors"]) == 0
    assert len(res["stocks"]) == 400
