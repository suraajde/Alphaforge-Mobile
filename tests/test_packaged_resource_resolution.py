"""Unit tests for Packaged Resource Resolution & Research Radar Universe Discovery (Sprint 14.0.8)."""

import os
import sys
import tempfile
from pathlib import Path
import pytest

from config.path_config import get_base_data_dir, get_data_path, get_resource_path
from services.universe_service import UniverseService


def test_resource_path_in_development_mode():
    """Verify that get_resource_path resolves stock_universe.csv in development mode."""
    csv_path = get_resource_path("data/universe/stock_universe.csv")
    assert csv_path.exists(), f"Resource stock_universe.csv not found at {csv_path}"

    meta_path = get_resource_path("data/universe/universe_metadata.json")
    assert meta_path.exists(), f"Resource universe_metadata.json not found at {meta_path}"


def test_universe_service_loads_production_universe():
    """Verify UniverseService loads enabled production stocks using get_resource_path."""
    svc = UniverseService()
    res = svc.load_universe()
    assert len(res["errors"]) == 0, f"Universe load errors: {res['errors']}"
    assert len(res["stocks"]) == 400, f"Expected 400 stocks, got {len(res['stocks'])}"

    enabled_res = svc.get_enabled_stocks()
    assert len(enabled_res["stocks"]) == 400, f"Expected 400 enabled stocks, got {len(enabled_res['stocks'])}"


def test_simulated_pyinstaller_frozen_mode_resource_resolution(monkeypatch):
    """Simulate PyInstaller frozen execution environment with sys.frozen and sys._MEIPASS."""
    temp_dir = tempfile.mkdtemp()
    try:
        # Create mock bundled universe inside temp_dir
        bundled_univ_dir = Path(temp_dir) / "data" / "universe"
        bundled_univ_dir.mkdir(parents=True, exist_ok=True)

        mock_csv = bundled_univ_dir / "stock_universe.csv"
        mock_csv.write_text(
            "symbol,company,category,enabled,exchange,source,as_of_date\n"
            "MOCKSTOCK,Mock Company,MIDCAP,True,NSE,Mock,2026-08-09\n",
            encoding="utf-8"
        )

        mock_meta = bundled_univ_dir / "universe_metadata.json"
        mock_meta.write_text('{"universe_name": "Mock Universe", "version": "1.0.0", "categories": ["MIDCAP"]}', encoding="utf-8")

        # Set frozen mode flags
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", temp_dir, raising=False)

        res_csv = get_resource_path("data/universe/stock_universe.csv")
        assert res_csv == mock_csv
        assert res_csv.exists()

        svc = UniverseService()
        result = svc.get_enabled_stocks()
        assert len(result["stocks"]) == 1
        assert result["stocks"][0]["symbol"] == "MOCKSTOCK"
    finally:
        pass


def test_cwd_independence_of_resource_resolution(monkeypatch):
    """Verify resource discovery works independently of current working directory."""
    original_cwd = os.getcwd()
    scratch_dir = tempfile.mkdtemp()
    try:
        os.chdir(scratch_dir)
        svc = UniverseService()
        res = svc.get_enabled_stocks()
        assert len(res["stocks"]) == 400
    finally:
        os.chdir(original_cwd)


def test_writable_user_data_separated_from_bundled_resources(monkeypatch):
    """Verify writable data paths resolve to AppData/ALPHAFORGE_DATA_DIR, not bundled resources."""
    temp_data = tempfile.mkdtemp()
    monkeypatch.setenv("ALPHAFORGE_DATA_DIR", temp_data)
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    base_dir = get_base_data_dir()
    assert str(base_dir) == temp_data

    intel_path = get_data_path("intelligence/portfolio_intelligence_history.json")
    assert str(intel_path).startswith(temp_data)
