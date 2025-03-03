import dotenv from 'dotenv';
import { createMCPServer } from '@anthropic-ai/mcp-server';
import { initializeLogger } from './utils/logger.js';
import modules from './modules/index.js';
import config from './config/index.js';

// Load environment variables
dotenv.config();

// Initialize logger
const logger = initializeLogger();

async function startServer() {
  try {
    logger.info('Starting MCP Personal Assistant server...');
    
    // Create MCP server with our modules
    const server = createMCPServer({
      name: "Personal Assistant Agent",
      description: "A versatile personal assistant that helps with calendar, tasks, emails, and more",
      functions: modules,
      config: config
    });

    // Start the server
    await server.start();
    
    logger.info(`MCP Personal Assistant server started successfully`);
    
    // Handle shutdown
    process.on('SIGINT', async () => {
      logger.info('Shutting down MCP Personal Assistant server...');
      await server.stop();
      process.exit(0);
    });
    
  } catch (error) {
    logger.error(`Failed to start MCP Personal Assistant server: ${error.message}`);
    process.exit(1);
  }
}

startServer();
