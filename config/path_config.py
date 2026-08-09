"""Centralized Production Path Management for AlphaForge.

Provides CWD-independent path resolution for packaged desktop execution,
with full backward compatibility to preserve existing user data and persistence.
"""
from __future__ import annotations

import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_base_data_dir() -> Path:
    """Return the base data directory.
    
    1. First check environment variable override (if set).
    2. Check if project-root relative 'data' directory exists (local development mode).
    3. Fallback to %APPDATA%/AlphaForge/data (or ~/.alphaforge/data) for packaged production desktop environment.
    """
    # Environment variable override check (highest priority for custom/testing setups)
    env_path = os.environ.get("ALPHAFORGE_DATA_DIR")
    if env_path:
        p = Path(env_path)
        p.mkdir(parents=True, exist_ok=True)
        return p

    # Local project-root data folder (backward compatibility for local development)
    local_data = _PROJECT_ROOT / "data"
    if local_data.exists():
        return local_data

    # Standard User AppData directory for packaged desktop execution
    appdata = os.environ.get("APPDATA")
    if appdata:
        prod_data = Path(appdata) / "AlphaForge" / "data"
    else:
        prod_data = Path.home() / ".alphaforge" / "data"

    prod_data.mkdir(parents=True, exist_ok=True)
    return prod_data

def get_data_path(relative_subpath: str) -> Path:
    """Resolve a relative subpath (e.g., 'alerts/portfolio_alerts.json' or 'intelligence/portfolio_intelligence_history.json')
    to an absolute Path, ensuring parent directories are created safely.
    
    Backward compatibility check: if local data file exists at project_root/data/relative_subpath,
    returns that path to preserve existing user data.
    """
    local_target = _PROJECT_ROOT / "data" / relative_subpath
    if local_target.exists():
        return local_target

    base_dir = get_base_data_dir()
    target = base_dir / relative_subpath
    target.parent.mkdir(parents=True, exist_ok=True)
    return target
