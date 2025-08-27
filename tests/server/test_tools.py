"""
Tests for server.tools module

This is an example of how you might organize tests for additional tools.
"""

import pytest
from server.tools import mcp


class TestMCPInstance:
    """Test the FastMCP instance configuration."""
    
    def test_mcp_name(self):
        """Test that MCP instance has correct name."""
        assert mcp.name == "CTF_Server"
    
    def test_mcp_tools_registered(self):
        """Test that list_files tool is registered."""
        # This is a placeholder test - you'd expand this as you add more tools
        # For now, just test that mcp object exists
        assert mcp is not None


# Example of future test structure for additional tools:
class TestFutureTools:
    """Placeholder for future tool tests."""
    
    @pytest.mark.skip(reason="Tool not implemented yet")
    def test_read_file_tool(self):
        """Test read_file tool when implemented."""
        pass
    
    @pytest.mark.skip(reason="Tool not implemented yet") 
    def test_write_file_tool(self):
        """Test write_file tool when implemented."""
        pass
