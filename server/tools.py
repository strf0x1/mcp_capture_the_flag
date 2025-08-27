"""
CTF MCP Server Tools

This module implements the tools for the Capture the Flag MCP server.
Following the Digital Affordance Discovery pattern, these are low-level,
primitive tools that allow agents to explore and interact with the filesystem.
"""

import os
from pathlib import Path
from typing import List
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
