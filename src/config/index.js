/**
 * Main configuration for the MCP Personal Assistant Agent
 */

const config = {
  // Server configuration
  server: {
    port: process.env.PORT || 3000,
    host: process.env.HOST || 'localhost',
  },
  
  // Module configurations
  modules: {
    // Calendar module configuration
    calendar: {
      providers: {
        google: {
          enabled: true,
          // The credentials will be loaded from environment variables
          scopes: [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events',
          ],
        },
        apple: {
          enabled: false,
        },
        outlook: {
          enabled: false,
        },
      },
      defaultProvider: 'google',
    },
    
    // Task management module configuration
    tasks: {
      providers: {
        local: {
          enabled: true,
          storageFile: 'data/tasks.json',
        },
        todoist: {
          enabled: false,
        },
      },
      defaultProvider: 'local',
    },
    
    // Email module configuration
    email: {
      providers: {
        gmail: {
          enabled: true,
          // The credentials will be loaded from environment variables
        },
        outlook: {
          enabled: false,
        },
      },
      defaultProvider: 'gmail',
      maxEmailsToRetrieve: 50,
    },
    
    // Knowledge retrieval module configuration
    knowledge: {
      providers: {
        web: {
          enabled: true,
          searchEngine: 'duckduckgo',
        },
        local: {
          enabled: true,
          indexPath: 'data/knowledge-index',
        },
      },
    },
    
    // Smart home module configuration
    smartHome: {
      providers: {
        homeAssistant: {
          enabled: false,
        },
        smartThings: {
          enabled: false,
        },
      },
    },
  },
  
  // User preferences
  user: {
    // These can be overridden by user settings
    timeFormat: '12h', // or '24h'
    dateFormat: 'MM/DD/YYYY',
    timezone: 'America/Los_Angeles',
    language: 'en-US',
  },
  
  // Storage configuration
  storage: {
    type: 'redis', // or 'file'
    redis: {
      host: process.env.REDIS_HOST || 'localhost',
      port: process.env.REDIS_PORT || 6379,
      password: process.env.REDIS_PASSWORD || '',
    },
    file: {
      path: 'data/storage',
    },
  },
};

export default config;
