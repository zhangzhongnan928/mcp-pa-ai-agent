# MCP Personal Assistant AI Agent

A powerful personal assistant AI agent built with the Model Context Protocol (MCP) that helps you manage your tasks, schedule, communications, and more.

## Overview

This project implements a personal assistant using the Model Context Protocol (MCP), allowing AI assistants like Claude to extend their capabilities through external tools and services. The PA agent can:

- Manage your calendar and schedule
- Track tasks and to-dos
- Search and retrieve information from various sources
- Manage emails and communications
- Control smart home devices
- And more!

## Features

- **Calendar Management**: Create, edit, and manage calendar events
- **Task Management**: Create, track, and prioritize tasks
- **Email Integration**: Read, search, and draft emails
- **Information Retrieval**: Search the web, local files, and knowledge bases
- **Smart Home Control**: Manage compatible smart home devices
- **Personalization**: Learn preferences and adapt to your needs

## Getting Started

### Prerequisites

- Node.js (v16+)
- Claude Desktop or another MCP-compatible assistant
- API credentials for integrated services (calendar, email, etc.)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/zhangzhongnan928/mcp-pa-ai-agent.git
   cd mcp-pa-ai-agent
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure your environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and credentials
   ```

4. Start the MCP server:
   ```bash
   npm start
   ```

### Adding to Claude Desktop

1. Open Claude Desktop
2. Add the following to your `claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "pa-agent": {
         "command": "npx",
         "args": ["-y", "mcp-pa-ai-agent"]
       }
     }
   }
   ```
3. Restart Claude Desktop

## Architecture

The PA agent is built on several MCP capabilities:

- **Calendar Module**: Interfaces with Google Calendar, Apple Calendar, Outlook, etc.
- **Task Module**: Manages task tracking systems (Todoist, local tasks, etc.)
- **Communication Module**: Handles email and messaging platforms
- **Knowledge Module**: Searches and retrieves information
- **Device Control Module**: Interfaces with smart home devices

## Configuration

Configuration options are available in `config.js`. You can customize:

- Available modules
- Service preferences
- Authentication methods
- User preferences

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Model Context Protocol](https://github.com/modelcontextprotocol) for the MCP framework
- Anthropic for Claude and supporting the MCP ecosystem
