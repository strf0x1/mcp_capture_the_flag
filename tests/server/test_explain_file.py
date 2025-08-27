#!/usr/bin/env python3
"""
Pytest tests for the explain_file MCP tool

This test module uses pytest to verify the explain_file function works correctly
and enforces security boundaries properly.
"""

import pytest
import tempfile
import os
from pathlib import Path

from server.tools import explain_file_raw as explain_file, HOME_DIR


class TestExplainFile:
    """Test class for the explain_file MCP tool."""
    
    def test_explain_home_directory(self):
        """Test explaining the home directory itself."""
        result = explain_file(str(HOME_DIR))
        
        # Should return a dictionary
        assert isinstance(result, dict)
        
        # Should have expected keys
        expected_keys = {'type', 'size', 'mime_type', 'is_text', 'is_binary', 
                        'last_modified', 'permissions', 'item_count'}
        assert all(key in result for key in expected_keys)
        
        # Home directory should be type 'directory'
        assert result['type'] == 'directory'
        
        # Directory size should be 0 or positive
        assert result['size'] >= 0
        
        # MIME type should be None for directories
        assert result['mime_type'] is None
        
        # Directories are not text or binary files
        assert result['is_text'] is False
        assert result['is_binary'] is False
        
        # Should have permissions info
        assert isinstance(result['permissions'], dict)
        assert 'readable' in result['permissions']
        assert 'writable' in result['permissions']
        assert 'executable' in result['permissions']
        
        # Should have item count for directory
        assert 'item_count' in result
        assert isinstance(result['item_count'], int) or result['item_count'] is None
    
    def test_explain_text_file(self):
        """Test explaining a text file."""
        # Create a temporary text file
        test_file = HOME_DIR / "pytest_temp_text.txt"
        test_content = "This is a test file for pytest.\nIt contains text content."
        
        try:
            test_file.write_text(test_content)
            
            result = explain_file(str(test_file))
            
            # Should return a dictionary with expected structure
            assert isinstance(result, dict)
            assert result['type'] == 'file'
            assert result['size'] == len(test_content.encode('utf-8'))
            assert result['is_text'] is True
            assert result['is_binary'] is False
            assert result['mime_type'] == 'text/plain'
            assert 'item_count' not in result  # Files don't have item count
            
        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()
    
    def test_explain_binary_file(self):
        """Test explaining a binary file."""
        # Create a temporary binary file
        test_file = HOME_DIR / "pytest_temp_binary.bin"
        binary_content = bytes([0, 1, 2, 3, 255, 254, 253])  # Contains null bytes
        
        try:
            test_file.write_bytes(binary_content)
            
            result = explain_file(str(test_file))
            
            assert isinstance(result, dict)
            assert result['type'] == 'file'
            assert result['size'] == len(binary_content)
            assert result['is_text'] is False
            assert result['is_binary'] is True
            # Binary file might not have a detectable MIME type
            
        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()
    
    def test_explain_json_file(self):
        """Test explaining a JSON file (should be detected as text)."""
        test_file = HOME_DIR / "pytest_temp_test.json"
        json_content = '{"test": true, "number": 42}'
        
        try:
            test_file.write_text(json_content)
            
            result = explain_file(str(test_file))
            
            assert result['type'] == 'file'
            assert result['is_text'] is True
            assert result['is_binary'] is False
            assert result['mime_type'] == 'application/json'
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_explain_python_file(self):
        """Test explaining a Python file."""
        test_file = HOME_DIR / "pytest_temp_test.py"
        python_content = "#!/usr/bin/env python3\nprint('Hello, world!')\n"
        
        try:
            test_file.write_text(python_content)
            
            result = explain_file(str(test_file))
            
            assert result['type'] == 'file'
            assert result['is_text'] is True
            assert result['is_binary'] is False
            assert result['mime_type'] == 'text/x-python'
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_explain_subdirectory(self):
        """Test explaining a subdirectory."""
        # Create a temporary subdirectory
        test_dir = HOME_DIR / "pytest_temp_subdir"
        
        try:
            test_dir.mkdir(exist_ok=True)
            
            # Add some files to it
            (test_dir / "file1.txt").write_text("content1")
            (test_dir / "file2.txt").write_text("content2")
            
            result = explain_file(str(test_dir))
            
            assert result['type'] == 'directory'
            assert result['size'] >= 0  # Directory size varies by filesystem
            assert result['mime_type'] is None
            assert result['is_text'] is False
            assert result['is_binary'] is False
            assert result['item_count'] == 2
            
        finally:
            # Clean up
            if test_dir.exists():
                for file in test_dir.iterdir():
                    if file.is_file():
                        file.unlink()
                test_dir.rmdir()
    
    def test_explain_symlink(self):
        """Test explaining a symlink."""
        test_file = HOME_DIR / "pytest_temp_target.txt"
        test_symlink = HOME_DIR / "pytest_temp_symlink.txt"
        
        try:
            # Create target file
            test_file.write_text("target content")
            
            # Create symlink pointing to the target file
            test_symlink.symlink_to(test_file)
            
            result = explain_file(str(test_symlink))
            
            assert result['type'] == 'symlink'
            # Other properties depend on the symlink behavior
            
        except (OSError, NotImplementedError):
            pytest.skip("Cannot create symlinks for testing")
        finally:
            # Clean up
            if test_symlink.exists() or test_symlink.is_symlink():
                test_symlink.unlink()
            if test_file.exists():
                test_file.unlink()
    
    @pytest.mark.parametrize("forbidden_path", ["/", "/etc", "/tmp", "/usr", "/var"])
    def test_security_boundaries(self, forbidden_path):
        """Test that accessing paths outside home directory is blocked."""
        with pytest.raises(ValueError, match="Path must be within home directory"):
            explain_file(forbidden_path)
    
    def test_nonexistent_path(self):
        """Test handling of non-existent path."""
        fake_path = str(HOME_DIR / "this_path_should_not_exist_12345")
        
        with pytest.raises(ValueError, match="Path does not exist"):
            explain_file(fake_path)
    
    def test_relative_path_resolution(self):
        """Test that relative paths are resolved correctly."""
        import os
        original_cwd = os.getcwd()
        
        try:
            os.chdir(str(HOME_DIR))
            # "." should resolve to HOME_DIR
            result = explain_file(".")
            assert result['type'] == 'directory'
        finally:
            os.chdir(original_cwd)
    
    def test_path_traversal_attack(self):
        """Test that path traversal attacks are blocked."""
        traversal_attempts = [
            str(HOME_DIR) + "/../../../etc",
            str(HOME_DIR) + "/../../..",
            str(HOME_DIR) + "/../root"
        ]
        
        for attempt in traversal_attempts:
            with pytest.raises(ValueError, match="(Path must be within home directory|Path does not exist)"):
                explain_file(attempt)
    
    def test_symlink_outside_home(self):
        """Test that symlinks pointing outside home directory are blocked."""
        symlink_path = HOME_DIR / "pytest_temp_symlink_outside"
        
        try:
            # Create symlink pointing outside home directory
            symlink_path.symlink_to("/")
            
            # Should be blocked
            with pytest.raises(ValueError, match="Path must be within home directory"):
                explain_file(str(symlink_path))
        except (OSError, NotImplementedError):
            pytest.skip("Cannot create symlinks for testing")
        finally:
            # Clean up
            if symlink_path.exists() or symlink_path.is_symlink():
                symlink_path.unlink()
    
    def test_large_file_size_reporting(self):
        """Test that file sizes are reported correctly."""
        test_file = HOME_DIR / "pytest_temp_large.txt"
        # Create content of known size
        content = "A" * 1000  # 1000 characters
        
        try:
            test_file.write_text(content)
            
            result = explain_file(str(test_file))
            
            assert result['size'] == len(content.encode('utf-8'))
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_permissions_detection(self):
        """Test that file permissions are detected correctly."""
        test_file = HOME_DIR / "pytest_temp_perms.txt"
        
        try:
            test_file.write_text("test content")
            
            result = explain_file(str(test_file))
            
            permissions = result['permissions']
            
            # Should be able to read our own file
            assert permissions['readable'] is True
            
            # Should be able to write our own file  
            assert permissions['writable'] is True
            
            # Executable depends on file type and permissions
            assert isinstance(permissions['executable'], bool)
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_empty_file(self):
        """Test explaining an empty file."""
        test_file = HOME_DIR / "pytest_temp_empty.txt"
        
        try:
            test_file.touch()  # Create empty file
            
            result = explain_file(str(test_file))
            
            assert result['type'] == 'file'
            assert result['size'] == 0
            assert result['is_text'] is True  # Empty files default to text
            assert result['is_binary'] is False
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_last_modified_timestamp(self):
        """Test that last modified timestamp is included and properly formatted."""
        test_file = HOME_DIR / "pytest_temp_timestamp.txt"
        
        try:
            test_file.write_text("test")
            
            result = explain_file(str(test_file))
            
            assert 'last_modified' in result
            # Should be a valid ISO timestamp string
            import datetime
            # This should not raise an exception
            parsed_time = datetime.datetime.fromisoformat(result['last_modified'])
            assert isinstance(parsed_time, datetime.datetime)
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_none_path(self):
        """Test handling of None path."""
        with pytest.raises((ValueError, TypeError)):
            explain_file(None)
    
    def test_empty_path(self):
        """Test handling of empty path string."""
        # Similar to list_files, empty string behavior depends on current directory
        try:
            result = explain_file("")
            assert isinstance(result, dict)
        except ValueError:
            # Expected if current directory is outside home
            pass


if __name__ == "__main__":
    # Allow running directly with python for quick testing
    pytest.main([__file__, "-v"])
