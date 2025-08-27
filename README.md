# MCP Capture The Flag

Interactive Capture the Flag game built with Model Context Protocol to demonstrate Digital Affordance Discovery pattern.

## Overview

This project demonstrates how an AI agent can explore a filesystem using low-level, primitive tools to find hidden flags - showcasing the Digital Affordance Discovery pattern where complex behaviors emerge from simple tools.

## Components

### MCP Server (`server/`)
- **FastMCP-based server** that provides filesystem exploration tools
- **`list_files` tool** - Lists contents of directories (scoped to home directory for security)
- **Stdio transport** - Communicates via standard input/output

### AWS Strands Client (`client/`)
- **Strands Agents framework** for AI agent functionality  
- **AWS Bedrock integration** using Claude Sonnet 3.7
- **MCP client** that connects to the local server via stdio
- **Interactive testing** of the `list_files` tool

## Installation

1. Install dependencies using `uv`:
```bash
uv sync
```

2. Set up AWS authentication (required for the client):
```bash
export AWS_PROFILE="your_aws_profile_name"
```

## Usage

### Running the Server (for development)
```bash
uv run python server/main.py
```

### Running the Client
```bash
export AWS_PROFILE="your_aws_profile_name"
uv run python client/main.py
```

The client will:
1. Connect to the MCP server using stdio transport
2. Discover available tools (should find `list_files`)
3. Create a Strands agent with AWS Bedrock
4. Test the `list_files` tool functionality
5. Demonstrate CTF exploration capabilities

## Development

### Adding New Tools
1. Add tool function to `server/tools.py`
2. Register with `@mcp.tool` decorator
3. Follow security boundaries (home directory scoped)
4. Include comprehensive docstrings
5. Expose raw function for testing (e.g., `tool_name_raw = _tool_impl`)

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/server/test_tools.py
```

### Project Structure
```
├── client/          # AWS Strands client implementation
├── server/          # MCP server with tools
├── tests/           # Test suite
│   ├── server/      # Tool implementation tests
│   ├── client/      # Client functionality tests
│   └── integration/ # End-to-end tests
└── spec.md          # Detailed specification
```

## CTF Game Setup

To create a full CTF environment (as described in `spec.md`), create this structure in your home directory:

```
ctf_root/
├── home/
│   └── user.txt
├── puzzles/
│   ├── hint.txt
│   └── flag.b64  # Base64 encoded flag
└── etc/
    └── config.txt
```

The agent's goal is to find and decode the hidden flag using only the provided exploration tools.

## Architecture

This project demonstrates the **Digital Affordance Discovery Pattern**:
- **Simple, primitive tools** (like `list_files`) are provided
- **No high-level abstractions** (no `find_flag()` function)
- **Agent must reason** about how to combine tools to achieve complex goals
- **Emergent behavior** arises from tool composition

## Dependencies

- **FastMCP** - MCP server implementation
- **Strands Agents** - AI agent framework
- **AWS Boto3** - AWS service integration
- **pytest** - Testing framework