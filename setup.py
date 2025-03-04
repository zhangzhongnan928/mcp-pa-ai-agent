#!/usr/bin/env python3
"""
MCP Personal Assistant - Setup Script
This script helps install and configure the MCP Personal Assistant server.
"""
import argparse
import os
import json
import shutil
import sys
import platform

def check_python_version():
    """Check if the Python version is sufficient."""
    if sys.version_info < (3, 10):
        print("Error: Python 3.10 or higher is required.")
        print(f"Current Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        return False
    return True

def setup_claude_desktop():
    """Configure the Claude Desktop application."""
    print("Setting up Claude Desktop configuration...")
    
    # Determine the config file path based on platform
    if platform.system() == 'Darwin':  # macOS
        config_dir = os.path.expanduser("~/Library/Application Support/Claude")
    elif platform.system() == 'Windows':
        config_dir = os.path.join(os.environ.get('APPDATA', ''), 'Claude')
    else:
        print("Warning: Claude Desktop is not currently supported on Linux.")
        if input("Continue anyway? (y/n): ").lower() != 'y':
            return False
        config_dir = os.path.expanduser("~/.config/Claude")
    
    # Create directory if it doesn't exist
    os.makedirs(config_dir, exist_ok=True)
    
    config_file = os.path.join(config_dir, 'claude_desktop_config.json')
    
    # Get the absolute path of the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    mcp_server_path = os.path.join(current_dir, 'mcp_server.py')
    
    # Create or update the config
    config = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError:
            print("Warning: Existing config file is invalid, creating a new one.")
            config = {}
    
    # Ensure mcpServers exists
    if 'mcpServers' not in config:
        config['mcpServers'] = {}
    
    # Add our server
    python_path = sys.executable
    
    config['mcpServers']['personal-assistant'] = {
        'command': python_path,
        'args': [mcp_server_path]
    }
    
    # Write the updated config
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Claude Desktop configuration updated at: {config_file}")
    print("Please restart Claude Desktop to apply the changes.")
    return True

def setup_env():
    """Create a .env file from the template."""
    if not os.path.exists('.env') and os.path.exists('.env.example'):
        shutil.copy('.env.example', '.env')
        print("Created .env file from .env.example")
        print("Please edit .env to add your API credentials")
        return True
    elif os.path.exists('.env'):
        print(".env file already exists, skipping")
        return True
    else:
        print("Error: .env.example not found")
        return False

def install_dependencies():
    """Install Python dependencies."""
    print("Installing Python dependencies...")
    
    try:
        if shutil.which('uv'):
            # Use uv if available
            os.system('uv pip install -r requirements.txt')
        else:
            # Fall back to pip
            os.system(f'{sys.executable} -m pip install -r requirements.txt')
        
        print("Dependencies installed successfully.")
        return True
    except Exception as e:
        print(f"Error installing dependencies: {str(e)}")
        return False

def test_installation():
    """Run a simple test to verify the installation."""
    print("Testing installation...")
    
    try:
        # Import MCP
        from mcp.server.fastmcp import FastMCP
        print("MCP package imported successfully.")
        
        # Try to import our server modules
        import mcp_server
        print("Server module imported successfully.")
        
        return True
    except ImportError as e:
        print(f"Import error: {str(e)}")
        print("Installation may not be complete.")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False

def main():
    """Main function for the setup script."""
    parser = argparse.ArgumentParser(description="Setup Personal Assistant MCP Server")
    parser.add_argument('--claude', action='store_true', help="Configure Claude Desktop")
    parser.add_argument('--env', action='store_true', help="Create .env file from template")
    parser.add_argument('--deps', action='store_true', help="Install dependencies")
    parser.add_argument('--test', action='store_true', help="Test the installation")
    parser.add_argument('--all', action='store_true', help="Perform all setup steps")
    
    args = parser.parse_args()
    
    # If no options, show help
    if not (args.claude or args.env or args.deps or args.test or args.all):
        parser.print_help()
        return
    
    # Check Python version first
    if not check_python_version():
        print("Setup cannot continue due to insufficient Python version.")
        return
    
    # Perform requested actions
    if args.all or args.deps:
        install_dependencies()
    
    if args.all or args.env:
        setup_env()
    
    if args.all or args.claude:
        setup_claude_desktop()
    
    if args.all or args.test:
        test_installation()
    
    print("\nSetup complete. To run the server, use: python mcp_server.py")

if __name__ == "__main__":
    main() 