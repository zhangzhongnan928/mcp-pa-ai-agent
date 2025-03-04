#!/usr/bin/env python3
import sys
import os
import logging
import dotenv
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any
from dataclasses import dataclass

# Check Python version
if sys.version_info < (3, 10):
    print("Error: Python 3.10 or higher is required for the MCP server.")
    print(f"Current Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print("\nPlease upgrade your Python version or use a virtual environment with Python 3.10+.")
    print("Example using conda:")
    print("  conda create -n mcp-env python=3.10")
    print("  conda activate mcp-env")
    print("\nExample using venv (if Python 3.10+ is installed):")
    print("  python3.10 -m venv venv")
    print("  source venv/bin/activate")
    sys.exit(1)

from typing import Any, Dict, List
from mcp.server.fastmcp import FastMCP, Context

# Load environment variables
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp-pa-agent")

@dataclass
class AppContext:
    """Type-safe context for the MCP server"""
    google_apis_initialized: bool = False
    home_assistant_connected: bool = False
    db_connection: Any = None
    task_store_path: str = "tasks_data.json"

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage resource lifecycle for the server"""
    context = AppContext()
    
    # Initialize resources on startup
    try:
        logger.info("Initializing server resources...")
        
        # Initialize database if using Redis
        if os.getenv("REDIS_HOST"):
            try:
                from redis import Redis
                logger.info(f"Connecting to Redis at {os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT', '6379')}")
                context.db_connection = Redis(
                    host=os.getenv("REDIS_HOST"),
                    port=int(os.getenv("REDIS_PORT", 6379)),
                    password=os.getenv("REDIS_PASSWORD", None)
                )
                context.db_connection.ping()  # Test connection
                logger.info("Redis connection successful")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
        
        # Check Google API credentials
        if all([
            os.getenv("GOOGLE_CLIENT_ID"),
            os.getenv("GOOGLE_CLIENT_SECRET"),
            os.getenv("GOOGLE_REFRESH_TOKEN")
        ]):
            context.google_apis_initialized = True
            logger.info("Google API credentials found")
        else:
            logger.warning("Google API credentials missing - calendar and email features will be unavailable")
            
        # Check Home Assistant configuration
        if os.getenv("HOME_ASSISTANT_URL") and os.getenv("HOME_ASSISTANT_TOKEN"):
            context.home_assistant_connected = True
            logger.info(f"Home Assistant configuration found: {os.getenv('HOME_ASSISTANT_URL')}")
        else:
            logger.warning("Home Assistant configuration missing - smart home features will be unavailable")
        
        # Log successful initialization
        server.info("Resources initialized successfully")
        
        yield context
    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
        raise
    finally:
        # Clean up on shutdown
        logger.info("Cleaning up server resources...")
        if context.db_connection:
            try:
                context.db_connection.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {str(e)}")
        
        server.info("Resources cleaned up successfully")

# Initialize FastMCP server
mcp = FastMCP("Personal Assistant Agent", 
              description="A versatile personal assistant that helps with calendar, tasks, emails, and more",
              lifespan=app_lifespan)

# Import module functions
from modules.calendar_functions import *
from modules.tasks_functions import *
from modules.email_functions import *
from modules.knowledge_functions import *
from modules.smarthome_functions import *

# Register the imported functions with MCP
# Note: The @mcp.tool() decorators in each module file will automatically 
# register these functions with the MCP server

def main():
    try:
        logger.info('Starting MCP Personal Assistant server...')
        
        # Log current configuration
        logger.info(f"Server configured with modules: {', '.join(['calendar', 'tasks', 'email', 'knowledge', 'smarthome'])}")
        
        # Log environment check
        if os.getenv("GOOGLE_CLIENT_ID"):
            logger.info("Google API credentials found")
        else:
            logger.warning("Google API credentials missing - calendar and email features will be unavailable")
            
        if os.getenv("HOME_ASSISTANT_URL"):
            logger.info("Home Assistant configuration found")
        else:
            logger.warning("Home Assistant configuration missing - smart home features will be unavailable")
            
        if os.getenv("DUCKDUCKGO_API_KEY"):
            logger.info("DuckDuckGo API key found")
        else:
            logger.warning("DuckDuckGo API key missing - web search will be unavailable")
        
        if os.getenv("WEATHER_API_KEY"):
            logger.info("Weather API key found")
        else:
            logger.warning("Weather API key missing - weather information will use mock data")
            
        if os.getenv("NEWS_API_KEY"):
            logger.info("News API key found")
        else:
            logger.warning("News API key missing - news retrieval will use mock data")
        
        # Run the server with stdio transport
        mcp.run(transport='stdio')
        
        logger.info('MCP Personal Assistant server started successfully')
    except Exception as e:
        logger.error(f'Failed to start MCP Personal Assistant server: {str(e)}')
        raise

if __name__ == "__main__":
    main() 