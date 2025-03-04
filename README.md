# MCP Personal Assistant Agent

A versatile personal assistant AI agent built with the Model Context Protocol (MCP) that helps with calendar, tasks, emails, and more.

## Overview

This project is a Model Context Protocol (MCP) server that provides a set of tools for a personal assistant agent. It can be integrated with MCP clients like Claude for Desktop to give AI assistants the ability to:

- Manage calendar events
- Track tasks and to-dos
- Read and send emails
- Search the web and retrieve information
- Control smart home devices

## Requirements

⚠️ **IMPORTANT:** Python 3.10 or higher is required for the MCP SDK. The server will not work with earlier Python versions.

- Python 3.10+ 
- MCP SDK 1.2.0+
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mcp-pa-ai-agent.git
cd mcp-pa-ai-agent
```

2. Ensure you have Python 3.10+:
```bash
python --version
```

3. If your system Python is older than 3.10, set up a compatible environment:
```bash
# Using conda
conda create -n mcp-env python=3.10
conda activate mcp-env

# OR using venv (if Python 3.10+ is installed elsewhere)
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Configure environment variables by copying the example file:
```bash
cp .env.example .env
```

6. Edit the `.env` file with your API credentials and settings.

## Running the Server

Start the MCP server with:

```bash
python mcp_server.py
```

The server will start and listen for MCP client connections.

## Connecting to Claude for Desktop

1. Install [Claude for Desktop](https://claude.ai/desktop)

2. Configure Claude for Desktop to use this MCP server by editing the configuration file at:
   - MacOS/Linux: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

3. Add the following configuration:
```json
{
  "mcpServers": {
    "personal-assistant": {
      "command": "/path/to/python",
      "args": [
        "/absolute/path/to/mcp-pa-ai-agent/mcp_server.py"
      ]
    }
  }
}
```

If you're using a virtual environment, make sure to point to the Python executable in that environment.

4. Restart Claude for Desktop

## Available Tools

### Calendar
- `get_events`: Retrieve upcoming calendar events
- `create_event`: Schedule a new calendar event

### Tasks
- `list_tasks`: View all tasks or filter by status
- `add_task`: Create a new task
- `update_task_status`: Mark tasks as pending, in-progress, or completed

### Email
- `get_emails`: List recent emails from your inbox
- `read_email`: View the full content of a specific email
- `send_email`: Compose and send a new email

### Knowledge
- `web_search`: Search the web for information
- `get_weather`: Get current weather information
- `get_news`: Retrieve latest news articles

### Smart Home
- `list_devices`: View all smart home devices
- `control_device`: Control smart home devices (lights, thermostats, etc.)
- `get_device_state`: Get detailed information about a device's current state

## Configuration

The server requires various API keys and credentials to access different services:

- **Google API**: For calendar and email functionality (OAuth2 credentials)
- **Weather API**: For weather information
- **News API**: For news retrieval
- **Home Assistant**: For smart home control

Refer to the `.env.example` file for all configurable options.

## Troubleshooting

### Python Version Issues

If you see an error like:
```
Error: Python 3.10 or higher is required for the MCP server.
```

You need to upgrade your Python version or use a virtual environment with Python 3.10+.

### MCP SDK Installation Issues

If you encounter problems installing the MCP SDK:
```
ERROR: Could not find a version that satisfies the requirement mcp>=1.2.0
```

Make sure you're using Python 3.10+ and pip is updated:
```bash
pip install --upgrade pip
```

## Development

To add new functionality to the server, you can:

1. Create a new module in the `modules/` directory
2. Implement functions with the `@mcp.tool()` decorator
3. Import your module in `mcp_server.py`

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
