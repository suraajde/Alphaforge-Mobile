"""Root pytest configuration for AlphaForge.

Overrides tmp_path fixture to use isolated tempfile.TemporaryDirectory(),
preventing Windows file lock / permission errors during automated testing.
"""
from pathlib import Path
import tempfile
import pytest


@pytest.fixture
def tmp_path():
    """Override default pytest tmp_path fixture using tempfile.TemporaryDirectory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)
