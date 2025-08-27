"""
Shared pytest fixtures and configuration
"""

import pytest
from pathlib import Path
from server.tools import HOME_DIR


@pytest.fixture
def home_dir():
    """Fixture providing the home directory path."""
    return HOME_DIR


@pytest.fixture
def temp_test_file(tmp_path):
    """Create a temporary test file for testing."""
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("test content")
    return test_file


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary test directory with some contents."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "file1.txt").write_text("content1")
    (test_dir / "file2.txt").write_text("content2")
    return test_dir
