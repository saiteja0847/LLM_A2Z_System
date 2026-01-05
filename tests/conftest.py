"""Pytest fixtures for LLM_A2Z_System."""
import pytest
from pathlib import Path

@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"
