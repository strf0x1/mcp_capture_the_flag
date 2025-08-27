#!/usr/bin/env python3
"""
CTF MCP Client

This is the CLI client for the Capture the Flag MCP game.
It will connect to the MCP server using AWS Strands and provide an interactive
interface for agents to play the CTF game.

The client uses AWS Bedrock with Sonnet 3.7 for LLM functionality.
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import List

# Add project root to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient
from strands.models import BedrockModel
import boto3


def setup_bedrock_model() -> BedrockModel:
    """
    Set up AWS Bedrock Claude model for the agent.
    Uses Claude Sonnet 3.5 as specified in the requirements.
    """
    # The user should have set AWS_PROFILE="assumed-nextgen-gov" before running
    session = boto3.Session()
    
    return BedrockModel(
        boto_session=session,
        model_id="anthropic.claude-3-7-sonnet-20250219-v1:0",
        temperature=0.3,
        streaming=True
    )


def create_mcp_client() -> MCPClient:
    """
    Create an MCP client that connects to our CTF server using stdio transport.
    """
    def create_stdio_transport():
        # Get the path to the server script
        server_path = Path(__file__).parent.parent / "server" / "main.py"
        
        return stdio_client(StdioServerParameters(
            command="python",
            args=[str(server_path)]
        ))
    
    return MCPClient(create_stdio_transport)


def demonstrate_ctf_exploration(agent: Agent) -> None:
    """
    Demonstrate CTF-style exploration using the agent.
    This shows how an agent would explore to find a flag.
    """
    print(f"\n🎯 Demonstrating CTF exploration capabilities")
    print("=" * 60)
    
    # Get the home directory to pass to the agent
    home_dir = str(Path.home())
    print(f"🔍 Starting exploration from: {home_dir}")
    
    exploration_prompt = f"""
    I'm playing a Capture the Flag (CTF) game where I need to find a hidden flag.
    
    Please help me explore the filesystem starting from the home directory: {home_dir}
    
    Use your tools strategically:
    1. First, use list_files with the path "{home_dir}" to see what's in the home directory
    2. Look for any interesting directories that might contain a CTF setup
    3. Use explain_file to inspect promising files/directories before exploring further
    4. If you find directories with names like 'ctf', 'ctf_root', 'puzzles', or similar, explore those
    5. Pay attention to any files with extensions like .txt, .b64, or other suspicious files
    6. Use explain_file to check if files are text or binary before attempting to read them
    
    Remember: explain_file is crucial for avoiding binary file overflow! 
    Always inspect files before reading them.
    
    Start your exploration from {home_dir} and tell me what you discover!
    """
    
    try:
        response = agent(exploration_prompt)
        print(f"\n🤖 Agent Response:")
        print(response)
    except Exception as e:
        print(f"❌ Error during CTF exploration: {e}")


def main():
    """Main entry point for the CTF MCP client."""
    print("🚀 CTF MCP Client - AWS Strands Edition")
    
    try:
        model = setup_bedrock_model()
        mcp_client = create_mcp_client()
        
        # Use the MCP client within a context manager
        with mcp_client:
            print("📋 Discovering available tools from MCP server...")
            
            # Get tools from the MCP server
            try:
                tools = mcp_client.list_tools_sync()
                print(f"✅ Found {len(tools)} MCP tools from server")
                
                # Try to get tool names safely
                try:
                    tool_names = []
                    for tool in tools:
                        if hasattr(tool, 'name'):
                            tool_names.append(tool.name)
                        elif hasattr(tool, '_name'):
                            tool_names.append(tool._name)
                        elif hasattr(tool, 'tool_name'):
                            tool_names.append(tool.tool_name)
                        else:
                            tool_names.append(str(type(tool).__name__))
                    
                    if tool_names:
                        print(f"📋 Available tools: {tool_names}")
                except Exception as attr_e:
                    print(f"⚠️  Could not list tool names: {attr_e}")
                    
            except Exception as e:
                print(f"❌ Error listing tools: {e}")
                return
            
            # Create agent with the MCP tools and Bedrock model
            print("🤖 Creating Strands agent with MCP tools and Bedrock model...")
            # Get the actual home directory path
            home_dir = str(Path.home())
            print(f"🏠 Home directory: {home_dir}")
            
            agent = Agent(
                tools=tools,
                model=model,
                system_prompt=f"""
                You are an AI assistant helping with a Capture the Flag (CTF) game.
                You have access to filesystem exploration tools that are scoped to the home directory.
                
                IMPORTANT: The home directory path is: {home_dir}
                All your file operations must use this path as the starting point.
                
                Your goal is to help explore the filesystem to find hidden flags.
                Use the available tools strategically and methodically.
                
                Available tools:
                - list_files: List contents of directories
                - explain_file: Get metadata about files/directories (type, size, text vs binary). Don't overuse this, but rather, use it when you want to open a file to learn more about it. For example, you might want to check its not a binary file. Or you might want to check the size.
                - get_file: Use this when you want to read the contents of a file.

                Best practices:
                - Always provide full paths as strings starting from {home_dir}
                - Use explain_file to inspect files before reading them (prevents binary overflow)
                - Be systematic in your exploration
                - Pay attention to interesting filenames and directory structures
                - Use explain_file to identify text files vs binary files
                - Report back clearly on what you find. When you've found the flag, your task is complete.
                """
            )
            
            # Demonstrate CTF exploration capabilities
            demonstrate_ctf_exploration(agent)
            
            print("\n✅ Testing completed successfully!")
            
    except Exception as e:
        print(f"❌ Error running CTF MCP client: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
