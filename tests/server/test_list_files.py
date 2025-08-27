#!/usr/bin/env python3
"""
Pytest tests for the list_files MCP tool

This test module uses pytest to verify the list_files function works correctly
and enforces security boundaries properly.
"""

import pytest
from pathlib import Path

from server.tools import list_files_raw as list_files, HOME_DIR


class TestListFiles:
    """Test class for the list_files MCP tool."""
    
    def test_list_home_directory(self):
        """Test listing home directory contents."""
        # Should not raise an exception
        home_contents = list_files(str(HOME_DIR))
        
        # Should return a list
        assert isinstance(home_contents, list)
        
        # Should contain some items (home directory is rarely empty)
        # We don't assert a minimum count since some systems might have minimal home dirs
        
        # Should be sorted (per implementation)
        assert home_contents == sorted(home_contents)
    
    def test_list_subdirectory_if_exists(self):
        """Test listing a subdirectory if one exists."""
        test_subdirs = ["Documents", "Desktop", "Downloads", ".ssh"]
        found_subdir = None
        
        for subdir in test_subdirs:
            subdir_path = HOME_DIR / subdir
            if subdir_path.exists() and subdir_path.is_dir():
                found_subdir = str(subdir_path)
                break
        
        if found_subdir:
            # Should not raise an exception
            subdir_contents = list_files(found_subdir)
            
            # Should return a list
            assert isinstance(subdir_contents, list)
            
            # Should be sorted
            assert subdir_contents == sorted(subdir_contents)
        else:
            # Skip test if no common subdirectories found
            pytest.skip("No common subdirectories found to test")
    
    @pytest.mark.parametrize("forbidden_path", ["/", "/etc", "/tmp", "/usr", "/var"])
    def test_security_boundaries(self, forbidden_path):
        """Test that accessing paths outside home directory is blocked."""
        with pytest.raises(ValueError, match="Path must be within home directory"):
            list_files(forbidden_path)
    
    def test_nonexistent_directory(self):
        """Test handling of non-existent directory."""
        fake_path = str(HOME_DIR / "this_directory_should_not_exist_12345")
        
        with pytest.raises(ValueError, match="Path does not exist"):
            list_files(fake_path)
    
    def test_file_instead_of_directory(self):
        """Test handling when a file path is provided instead of directory."""
        # Find a file in the home directory to test with
        test_files = [".bashrc", ".zshrc", ".profile", ".gitconfig"]
        found_file = None
        
        for filename in test_files:
            file_path = HOME_DIR / filename
            if file_path.exists() and file_path.is_file():
                found_file = str(file_path)
                break
        
        if found_file:
            with pytest.raises(ValueError, match="Path is not a directory"):
                list_files(found_file)
        else:
            # Create a temporary file for testing
            test_file = HOME_DIR / "pytest_temp_file"
            try:
                test_file.touch()
                with pytest.raises(ValueError, match="Path is not a directory"):
                    list_files(str(test_file))
            finally:
                # Clean up the test file
                if test_file.exists():
                    test_file.unlink()
    
    def test_relative_path_resolution(self):
        """Test that relative paths are resolved correctly."""
        # Test with relative path that should resolve to within home directory
        # Using "." should resolve to current working directory
        # We'll change to home dir first to ensure it's within bounds
        import os
        original_cwd = os.getcwd()
        
        try:
            os.chdir(str(HOME_DIR))
            # "." should resolve to HOME_DIR and work
            contents = list_files(".")
            assert isinstance(contents, list)
        finally:
            os.chdir(original_cwd)
    
    def test_path_traversal_attack(self):
        """Test that path traversal attacks are blocked."""
        # Try various path traversal attempts
        traversal_attempts = [
            str(HOME_DIR) + "/../../../etc",
            str(HOME_DIR) + "/../../..",
            str(HOME_DIR) + "/../root"
        ]
        
        for attempt in traversal_attempts:
            with pytest.raises(ValueError, match="Path must be within home directory"):
                list_files(attempt)
    
    def test_symlink_outside_home(self):
        """Test that symlinks pointing outside home directory are blocked."""
        # Create a symlink pointing outside home directory
        symlink_path = HOME_DIR / "pytest_temp_symlink"
        
        try:
            # Create symlink pointing to root directory
            symlink_path.symlink_to("/")
            
            # Should be blocked even though the symlink is in home directory
            with pytest.raises(ValueError, match="Path must be within home directory"):
                list_files(str(symlink_path))
        except (OSError, NotImplementedError):
            # Skip if symlinks aren't supported or can't be created
            pytest.skip("Cannot create symlinks for testing")
        finally:
            # Clean up the test symlink
            if symlink_path.exists() or symlink_path.is_symlink():
                symlink_path.unlink()
    
    def test_empty_path(self):
        """Test handling of empty path string."""
        # Empty string resolves to current directory, which may or may not be in home dir
        # So we need to be more flexible about what error we expect
        try:
            result = list_files("")
            # If it succeeds, we're in home dir and that's fine
            assert isinstance(result, list)
        except ValueError:
            # If it fails, that's also acceptable (likely outside home dir)
            pass
    
    def test_none_path(self):
        """Test handling of None path."""
        with pytest.raises(ValueError):
            list_files(None)


if __name__ == "__main__":
    # Allow running directly with python for quick testing
    pytest.main([__file__, "-v"])
