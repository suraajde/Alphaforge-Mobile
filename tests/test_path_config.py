"""Unit tests for Centralized Path Management (config/path_config.py)."""
from pathlib import Path
import tempfile
import os

from config.path_config import get_base_data_dir, get_data_path

def test_get_base_data_dir_returns_valid_path():
    base_dir = get_base_data_dir()
    assert isinstance(base_dir, Path)
    assert base_dir.exists()

def test_get_data_path_resolves_and_creates_parents(tmp_path):
    subpath = "test_subfolder/test_file.json"
    data_path = get_data_path(subpath)
    assert isinstance(data_path, Path)
    assert data_path.parent.exists()

def test_env_variable_override(monkeypatch, tmp_path):
    custom_dir = tmp_path / "custom_data"
    monkeypatch.setenv("ALPHAFORGE_DATA_DIR", str(custom_dir))
    base_dir = get_base_data_dir()
    assert base_dir == custom_dir
    assert custom_dir.exists()
