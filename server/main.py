#!/usr/bin/env python3
"""
CTF MCP Server Main Entry Point

This is the main entry point for the Capture the Flag MCP server.
It sets up a stdio-based MCP server using FastMCP.

To run this server:
    python server/main.py

The server will communicate via stdio, making it suitable for use with
MCP clients that can spawn and communicate with stdio-based servers.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path so we can import server modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from server.tools import mcp


def main():
    """Main entry point for the CTF MCP server."""
    try:
        # Run the FastMCP server with stdio transport
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        print("Server interrupted by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
