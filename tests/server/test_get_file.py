#!/usr/bin/env python3
"""
Pytest tests for the get_file MCP tool

This test module uses pytest to verify the get_file function works correctly,
enforces security boundaries, handles text/binary detection properly, and
implements proper truncation for large files.
"""

import pytest
import tempfile
import os
from pathlib import Path

from server.tools import get_file_raw as get_file, HOME_DIR


class TestGetFile:
    """Test class for the get_file MCP tool."""
    
    def test_get_simple_text_file(self):
        """Test reading a simple text file."""
        test_file = HOME_DIR / "pytest_temp_text.txt"
        test_content = "This is a test file for pytest.\nIt contains text content."
        
        try:
            test_file.write_text(test_content)
            
            result = get_file(str(test_file))
            
            assert isinstance(result, str)
            assert result == test_content
            
        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()
    
    def test_get_json_file(self):
        """Test reading a JSON file (should be detected as text)."""
        test_file = HOME_DIR / "pytest_temp_test.json"
        json_content = '{\n  "test": true,\n  "number": 42,\n  "array": [1, 2, 3]\n}'
        
        try:
            test_file.write_text(json_content)
            
            result = get_file(str(test_file))
            
            assert result == json_content
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_get_python_file(self):
        """Test reading a Python file."""
        test_file = HOME_DIR / "pytest_temp_test.py"
        python_content = "#!/usr/bin/env python3\nprint('Hello, world!')\n\ndef main():\n    pass\n"
        
        try:
            test_file.write_text(python_content)
            
            result = get_file(str(test_file))
            
            assert result == python_content
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_get_empty_file(self):
        """Test reading an empty file."""
        test_file = HOME_DIR / "pytest_temp_empty.txt"
        
        try:
            test_file.touch()  # Create empty file
            
            result = get_file(str(test_file))
            
            assert result == ""
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_binary_file_rejection(self):
        """Test that binary files are rejected."""
        test_file = HOME_DIR / "pytest_temp_binary.bin"
        binary_content = bytes([0, 1, 2, 3, 255, 254, 253])  # Contains null bytes
        
        try:
            test_file.write_bytes(binary_content)
            
            with pytest.raises(ValueError, match="File appears to be binary"):
                get_file(str(test_file))
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_directory_rejection(self):
        """Test that directories are rejected."""
        test_dir = HOME_DIR / "pytest_temp_dir"
        
        try:
            test_dir.mkdir(exist_ok=True)
            
            with pytest.raises(ValueError, match="Path is not a file"):
                get_file(str(test_dir))
            
        finally:
            if test_dir.exists():
                test_dir.rmdir()
    
    def test_file_truncation_small(self):
        """Test that small files are not truncated."""
        test_file = HOME_DIR / "pytest_temp_small.txt"
        # Create content well under the limit
        content = "A" * 1000  # 1KB, well under 50KB limit
        
        try:
            test_file.write_text(content)
            
            result = get_file(str(test_file))
            
            assert result == content
            assert "[TRUNCATED:" not in result
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_file_truncation_large(self):
        """Test that large files are truncated properly."""
        test_file = HOME_DIR / "pytest_temp_large.txt"
        # Create content over the default limit (50,000 chars)
        content = "A" * 60000  # 60KB, over the limit
        
        try:
            test_file.write_text(content)
            
            result = get_file(str(test_file))
            
            # Should be truncated
            assert len(result) > 50000  # Includes truncation message
            assert "[TRUNCATED:" in result
            assert "60,000 characters" in result  # Should report original size
            assert "showing first 50,000 characters" in result
            assert "10,000 characters were truncated" in result
            
            # Should start with the original content
            assert result.startswith("A" * 50000)
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_custom_truncation_limit(self):
        """Test using custom truncation limit."""
        test_file = HOME_DIR / "pytest_temp_custom_limit.txt"
        content = "B" * 1000  # 1000 characters
        
        try:
            test_file.write_text(content)
            
            # Use a custom limit of 500 characters
            result = get_file(str(test_file), max_chars=500)
            
            # Should be truncated at 500 chars
            assert "[TRUNCATED:" in result
            assert "1,000 characters" in result  # Original size
            assert "showing first 500 characters" in result
            assert "500 characters were truncated" in result
            
            # Should start with first 500 B's
            assert result.startswith("B" * 500)
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_unicode_content(self):
        """Test reading files with Unicode content."""
        test_file = HOME_DIR / "pytest_temp_unicode.txt"
        unicode_content = "Hello, 世界! 🌍 Café naïve résumé"
        
        try:
            test_file.write_text(unicode_content, encoding='utf-8')
            
            result = get_file(str(test_file))
            
            assert result == unicode_content
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_multiline_content(self):
        """Test reading files with multiple lines."""
        test_file = HOME_DIR / "pytest_temp_multiline.txt"
        multiline_content = """Line 1
Line 2
Line 3

Line 5 with empty line above
    Indented line
\tTab-indented line"""
        
        try:
            test_file.write_text(multiline_content)
            
            result = get_file(str(test_file))
            
            assert result == multiline_content
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    @pytest.mark.parametrize("forbidden_path", ["/", "/etc", "/tmp", "/usr", "/var"])
    def test_security_boundaries(self, forbidden_path):
        """Test that accessing paths outside home directory is blocked."""
        with pytest.raises(ValueError, match="Path must be within home directory"):
            get_file(forbidden_path)
    
    def test_nonexistent_file(self):
        """Test handling of non-existent file."""
        fake_path = str(HOME_DIR / "this_file_should_not_exist_12345.txt")
        
        with pytest.raises(ValueError, match="Path does not exist"):
            get_file(fake_path)
    
    def test_relative_path_resolution(self):
        """Test that relative paths are resolved correctly."""
        test_file = HOME_DIR / "pytest_temp_relative.txt"
        content = "relative path test"
        
        try:
            test_file.write_text(content)
            
            import os
            original_cwd = os.getcwd()
            
            try:
                os.chdir(str(HOME_DIR))
                # Use relative path
                result = get_file("pytest_temp_relative.txt")
                assert result == content
            finally:
                os.chdir(original_cwd)
                
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_path_traversal_attack(self):
        """Test that path traversal attacks are blocked."""
        traversal_attempts = [
            str(HOME_DIR) + "/../../../etc/passwd",
            str(HOME_DIR) + "/../../..",
            str(HOME_DIR) + "/../root/.bashrc"
        ]
        
        for attempt in traversal_attempts:
            with pytest.raises(ValueError, match="(Path must be within home directory|Path does not exist)"):
                get_file(attempt)
    
    def test_symlink_outside_home(self):
        """Test that symlinks pointing outside home directory are blocked."""
        symlink_path = HOME_DIR / "pytest_temp_symlink_outside"
        
        try:
            # Create symlink pointing outside home directory
            symlink_path.symlink_to("/etc/passwd")
            
            # Should be blocked
            with pytest.raises(ValueError, match="Path must be within home directory"):
                get_file(str(symlink_path))
        except (OSError, NotImplementedError):
            pytest.skip("Cannot create symlinks for testing")
        finally:
            # Clean up
            if symlink_path.exists() or symlink_path.is_symlink():
                symlink_path.unlink()
    
    def test_symlink_within_home(self):
        """Test that symlinks within home directory work correctly."""
        target_file = HOME_DIR / "pytest_temp_target.txt"
        symlink_path = HOME_DIR / "pytest_temp_symlink_within"
        content = "symlink test content"
        
        try:
            # Create target file
            target_file.write_text(content)
            
            # Create symlink pointing to target within home
            symlink_path.symlink_to(target_file)
            
            # Should work
            result = get_file(str(symlink_path))
            assert result == content
            
        except (OSError, NotImplementedError):
            pytest.skip("Cannot create symlinks for testing")
        finally:
            # Clean up
            if symlink_path.exists() or symlink_path.is_symlink():
                symlink_path.unlink()
            if target_file.exists():
                target_file.unlink()
    
    def test_none_path(self):
        """Test handling of None path."""
        with pytest.raises((ValueError, TypeError)):
            get_file(None)
    
    def test_empty_path(self):
        """Test handling of empty path string."""
        # Empty string behavior depends on current directory
        try:
            result = get_file("")
            # If it succeeds, we're reading a file in current dir
            assert isinstance(result, str)
        except ValueError:
            # Expected if current directory is outside home or path doesn't exist
            pass
    
    def test_encoding_fallback(self):
        """Test handling of files with encoding issues."""
        test_file = HOME_DIR / "pytest_temp_encoding.txt"
        
        try:
            # Write file with mixed encoding (this simulates encoding issues)
            with open(test_file, 'wb') as f:
                f.write(b"Hello\x80World")  # Invalid UTF-8 sequence
            
            # Should still be readable with replacement characters
            result = get_file(str(test_file))
            
            assert isinstance(result, str)
            assert "Hello" in result
            assert "World" in result
            # Invalid bytes might be replaced with replacement character
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_very_long_lines(self):
        """Test handling files with very long lines."""
        test_file = HOME_DIR / "pytest_temp_long_lines.txt"
        # Create a file with very long lines but still under total character limit
        long_line = "X" * 10000  # 10KB line
        content = f"{long_line}\nShort line\n{long_line}"
        
        try:
            test_file.write_text(content)
            
            result = get_file(str(test_file))
            
            assert result == content
            assert result.count("\n") == 2  # Should preserve line breaks
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_special_characters(self):
        """Test handling files with special characters and escape sequences."""
        test_file = HOME_DIR / "pytest_temp_special.txt"
        special_content = 'Quotes: "double" and \'single\'\nTabs:\tspaced\nBackslash: \\ and newline: \\n\nNull-like: \\x00'
        
        try:
            test_file.write_text(special_content)
            
            result = get_file(str(test_file))
            
            assert result == special_content
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_file_with_only_whitespace(self):
        """Test handling files containing only whitespace."""
        test_file = HOME_DIR / "pytest_temp_whitespace.txt"
        # Python's text mode normalizes line endings, so \r\n becomes \n
        whitespace_content = "   \n\t\n  \n    "
        
        try:
            test_file.write_text(whitespace_content)
            
            result = get_file(str(test_file))
            
            assert result == whitespace_content
            
        finally:
            if test_file.exists():
                test_file.unlink()


if __name__ == "__main__":
    # Allow running directly with python for quick testing
    pytest.main([__file__, "-v"])
