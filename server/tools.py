"""
CTF MCP Server Tools

This module implements the tools for the Capture the Flag MCP server.
Following the Digital Affordance Discovery pattern, these are low-level,
primitive tools that allow agents to explore and interact with the filesystem.
"""

import os
import mimetypes
import stat
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from fastmcp import FastMCP

# Create the FastMCP instance
mcp = FastMCP(name="CTF_Server")

# Get the user's home directory for scoping
HOME_DIR = Path.home()


def _list_files_impl(path: str) -> List[str]:
    """
    Takes a real directory path on the local filesystem as a string and returns a 
    list of files and directories inside it. Use this to explore the filesystem.
    
    This tool is scoped to only work within your home directory for security.
    
    Args:
        path: Directory path to list contents of
        
    Returns:
        List of file and directory names in the specified path
        
    Raises:
        ValueError: If path is outside home directory or doesn't exist
        PermissionError: If access to directory is denied
    """
    try:
        # Convert to Path object for easier manipulation
        target_path = Path(path).resolve()
        
        # Security check: ensure path is within home directory
        if not str(target_path).startswith(str(HOME_DIR)):
            raise ValueError(f"Path must be within home directory ({HOME_DIR})")
        
        # Check if path exists and is a directory
        if not target_path.exists():
            raise ValueError(f"Path does not exist: {target_path}")
            
        if not target_path.is_dir():
            raise ValueError(f"Path is not a directory: {target_path}")
        
        # List directory contents
        contents = []
        for item in target_path.iterdir():
            contents.append(item.name)
        
        # Sort for consistent output
        contents.sort()
        
        return contents
        
    except PermissionError as e:
        raise PermissionError(f"Permission denied accessing: {path}")
    except Exception as e:
        raise ValueError(f"Error listing directory {path}: {str(e)}")


# Expose the raw function for testing
list_files_raw = _list_files_impl

# Register the tool with MCP
@mcp.tool
def list_files(path: str) -> List[str]:
    """
    Takes a real directory path on the local filesystem as a string and returns a 
    list of files and directories inside it. Use this to explore the filesystem.
    
    This tool is scoped to only work within your home directory for security.
    
    Args:
        path: Directory path to list contents of
        
    Returns:
        List of file and directory names in the specified path
        
    Raises:
        ValueError: If path is outside home directory or doesn't exist
        PermissionError: If access to directory is denied
    """
    return _list_files_impl(path)


def _explain_file_impl(path: str) -> Dict[str, Any]:
    """
    Takes a full path to a real file or directory as a string and returns metadata 
    about it, such as its type (file/directory) and size. Use this to understand 
    what a file is before reading it.
    
    This tool is scoped to only work within your home directory for security.
    
    Args:
        path: File or directory path to get metadata for
        
    Returns:
        Dict containing metadata about the file/directory:
        - type: 'file', 'directory', or 'symlink'
        - size: Size in bytes (0 for directories)
        - mime_type: MIME type of the file (None for directories)
        - is_text: Boolean indicating if file appears to be text-based
        - is_binary: Boolean indicating if file appears to be binary
        - last_modified: ISO timestamp of last modification
        - permissions: Dict with 'readable', 'writable', 'executable' flags
        - item_count: Number of items in directory (only for directories)
        
    Raises:
        ValueError: If path is outside home directory or doesn't exist
        PermissionError: If access to file/directory is denied
    """
    try:
        # Convert to Path object for easier manipulation
        # Don't resolve yet - we need to check for symlinks first
        original_path = Path(path)
        
        # Check if path exists
        if not original_path.exists():
            raise ValueError(f"Path does not exist: {original_path}")
        
        # Check for symlink BEFORE resolving
        is_symlink = original_path.is_symlink()
        
        # Now resolve for security check
        target_path = original_path.resolve()
        
        # Security check: ensure resolved path is within home directory
        if not str(target_path).startswith(str(HOME_DIR)):
            raise ValueError(f"Path must be within home directory ({HOME_DIR})")
        
        # Get file stats (use original path to preserve symlink info if needed)
        file_stats = original_path.stat()
        
        # Determine file type
        if is_symlink:
            file_type = "symlink"
        elif original_path.is_dir():
            file_type = "directory"
        elif original_path.is_file():
            file_type = "file"
        else:
            file_type = "other"
        
        # Get MIME type for files
        mime_type = None
        is_text = False
        is_binary = False
        
        if file_type == "file" or (file_type == "symlink" and original_path.is_file()):
            # Get MIME type (use original path)
            mime_type, _ = mimetypes.guess_type(str(original_path))
            
            # Determine if it's likely text or binary
            if mime_type:
                is_text = mime_type.startswith('text/') or mime_type in [
                    'application/json', 'application/xml', 'application/javascript',
                    'application/x-yaml', 'application/x-sh'
                ]
                is_binary = not is_text
            else:
                # If no MIME type detected, try to read a small sample
                try:
                    with open(original_path, 'rb') as f:
                        sample = f.read(1024)  # Read first 1KB
                    # Simple heuristic: if sample contains null bytes, it's likely binary
                    is_binary = b'\x00' in sample
                    is_text = not is_binary
                except (PermissionError, OSError):
                    # If we can't read it, mark as unknown
                    is_text = False
                    is_binary = False
        
        # Get permissions (use original path)
        permissions = {
            'readable': os.access(original_path, os.R_OK),
            'writable': os.access(original_path, os.W_OK),
            'executable': os.access(original_path, os.X_OK)
        }
        
        # Get item count for directories
        item_count = None
        if file_type == "directory" or (file_type == "symlink" and original_path.is_dir()):
            try:
                item_count = len(list(original_path.iterdir()))
            except PermissionError:
                item_count = None  # Can't read directory contents
        
        # Format last modified time
        last_modified = datetime.fromtimestamp(file_stats.st_mtime).isoformat()
        
        result = {
            'type': file_type,
            'size': file_stats.st_size,
            'mime_type': mime_type,
            'is_text': is_text,
            'is_binary': is_binary,
            'last_modified': last_modified,
            'permissions': permissions
        }
        
        # Add item count for directories
        if item_count is not None:
            result['item_count'] = item_count
        
        return result
        
    except PermissionError as e:
        raise PermissionError(f"Permission denied accessing: {path}")
    except Exception as e:
        raise ValueError(f"Error getting file info for {path}: {str(e)}")


# Expose the raw function for testing
explain_file_raw = _explain_file_impl

# Register the tool with MCP
@mcp.tool
def explain_file(path: str) -> Dict[str, Any]:
    """
    Takes a full path to a real file or directory as a string and returns metadata 
    about it, such as its type (file/directory) and size. Use this to understand 
    what a file is before reading it.
    
    This tool is scoped to only work within your home directory for security.
    
    Args:
        path: File or directory path to get metadata for
        
    Returns:
        Dict containing metadata about the file/directory:
        - type: 'file', 'directory', or 'symlink'
        - size: Size in bytes (0 for directories)
        - mime_type: MIME type of the file (None for directories)
        - is_text: Boolean indicating if file appears to be text-based
        - is_binary: Boolean indicating if file appears to be binary
        - last_modified: ISO timestamp of last modification
        - permissions: Dict with 'readable', 'writable', 'executable' flags
        - item_count: Number of items in directory (only for directories)
        
    Raises:
        ValueError: If path is outside home directory or doesn't exist
        PermissionError: If access to file/directory is denied
    """
    return _explain_file_impl(path)
