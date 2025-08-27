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


def test_list_files_tool(agent: Agent, test_directory: str = None) -> None:
    """
    Test the list_files tool functionality.
    
    Args:
        agent: The Strands agent instance
        test_directory: Optional directory path to test (defaults to home directory)
    """
    if test_directory is None:
        test_directory = str(Path.home())
    
    print(f"\n🧪 Testing list_files tool with directory: {test_directory}")
    print("=" * 60)
    
    test_prompt = f"""
    Please use the list_files tool to list the contents of the directory: {test_directory}
    
    After listing the files, please:
    1. Tell me how many items are in the directory
    2. Identify if there are any directories vs files
    3. Give me a brief summary of what you found
    """
    
    try:
        response = agent(test_prompt)
        print(f"\n🤖 Agent Response:")
        print(response)
    except Exception as e:
        print(f"❌ Error testing list_files tool: {e}")


def demonstrate_ctf_exploration(agent: Agent) -> None:
    """
    Demonstrate CTF-style exploration using the agent.
    This shows how an agent would explore to find a flag.
    """
    print(f"\n🎯 Demonstrating CTF exploration capabilities")
    print("=" * 60)
    
    exploration_prompt = """
    I'm playing a Capture the Flag (CTF) game where I need to find a hidden flag.
    
    Please help me explore the filesystem starting from my home directory.
    Use the list_files tool to:
    1. First, list the contents of my home directory
    2. Look for any interesting directories that might contain a CTF setup
    3. If you find directories with names like 'ctf', 'ctf_root', 'puzzles', or similar, explore those
    4. Pay attention to any files with extensions like .txt, .b64, or other suspicious files
    
    Start your exploration and tell me what you discover!
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
    print("Connecting to local MCP server and testing list_files tool...")
    print(f"Using AWS profile: {os.environ.get('AWS_PROFILE', 'default')}")
    
    try:
        # Set up the Bedrock model
        print("\n🧠 Setting up AWS Bedrock Claude model...")
        model = setup_bedrock_model()
        
        # Create MCP client
        print("🔗 Creating MCP client connection...")
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
            agent = Agent(
                tools=tools,
                model=model,
                system_prompt="""
                You are an AI assistant helping with a Capture the Flag (CTF) game.
                You have access to filesystem exploration tools.
                
                Your goal is to help explore the filesystem to find hidden flags.
                Use the available tools strategically and methodically.
                
                When using the list_files tool:
                - Always provide the full path as a string
                - Be systematic in your exploration
                - Pay attention to interesting filenames and directory structures
                - Report back clearly on what you find
                """
            )
            
            # Test the list_files tool with a simple directory
            test_list_files_tool(agent)
            
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
