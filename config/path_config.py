"""Centralized Production Path Management for AlphaForge.

Provides CWD-independent path resolution for packaged desktop execution,
with full backward compatibility to preserve existing user data and persistence.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_resource_path(relative_subpath: str) -> Path:
    """Resolve a read-only bundled application resource (e.g. 'data/universe/stock_universe.csv' or 'VERSION.md').

    1. When running inside a PyInstaller frozen bundle (sys.frozen is True),
       check sys._MEIPASS / relative_subpath.
    2. Fall back to _PROJECT_ROOT / relative_subpath for local development.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        meipass_path = Path(sys._MEIPASS) / relative_subpath
        if meipass_path.exists():
            return meipass_path

    return _PROJECT_ROOT / relative_subpath


def get_base_data_dir() -> Path:
    """Return the writable base data directory for user runtime persistence.

    1. First check environment variable override ALPHAFORGE_DATA_DIR (highest priority).
    2. In non-frozen local development mode, use local _PROJECT_ROOT / 'data' if it exists.
    3. In packaged production desktop execution (or fallback), use %APPDATA%/AlphaForge/data (or ~/.alphaforge/data).
    """
    env_path = os.environ.get("ALPHAFORGE_DATA_DIR")
    if env_path:
        p = Path(env_path)
        p.mkdir(parents=True, exist_ok=True)
        return p

    if not getattr(sys, "frozen", False):
        local_data = _PROJECT_ROOT / "data"
        if local_data.exists():
            return local_data

    appdata = os.environ.get("APPDATA")
    if appdata:
        prod_data = Path(appdata) / "AlphaForge" / "data"
    else:
        prod_data = Path.home() / ".alphaforge" / "data"

    prod_data.mkdir(parents=True, exist_ok=True)
    return prod_data


def get_data_path(relative_subpath: str) -> Path:
    """Resolve a relative subpath for writable user data (e.g., 'alerts/portfolio_alerts.json'),
    ensuring parent directories are created safely.
    """
    if not getattr(sys, "frozen", False):
        local_target = _PROJECT_ROOT / "data" / relative_subpath
        if local_target.exists():
            return local_target

    base_dir = get_base_data_dir()
    target = base_dir / relative_subpath
    target.parent.mkdir(parents=True, exist_ok=True)
    return target
