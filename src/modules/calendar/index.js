/**
 * Calendar Module Functions
 * Provides MCP functions for interacting with calendar services
 */

import config from '../../config/index.js';
import logger from '../../utils/logger.js';
import { getGoogleCalendarClient } from './providers/google.js';

// Get the default calendar provider from config
const defaultProvider = config.modules.calendar.defaultProvider;

/**
 * Get calendar events within a specified time range
 */
const getEvents = {
  description: "Get calendar events within a specified time range",
  parameters: {
    properties: {
      startDate: {
        type: "string",
        description: "Start date in ISO format (YYYY-MM-DD) or relative format like 'today', 'tomorrow'"
      },
      endDate: {
        type: "string",
        description: "End date in ISO format (YYYY-MM-DD) or relative format like 'today', 'tomorrow'"
      },
      calendarId: {
        type: "string",
        description: "ID of the calendar to fetch events from (defaults to primary calendar)"
      },
      maxResults: {
        type: "number",
        description: "Maximum number of events to return"
      },
      provider: {
        type: "string",
        description: "Calendar provider to use (google, apple, outlook)"
      }
    },
    required: ["startDate"]
  },
  async handler(params) {
    try {
      const provider = params.provider || defaultProvider;
      const calendarId = params.calendarId || 'primary';
      
      // Format dates if they're relative
      const startDate = formatDate(params.startDate);
      const endDate = params.endDate ? formatDate(params.endDate) : null;
      
      logger.info(`Fetching events from ${startDate} to ${endDate || 'indefinite'} using ${provider} provider`);
      
      // Get events based on the provider
      if (provider === 'google') {
        const client = await getGoogleCalendarClient();
        return await getGoogleEvents(client, {
          calendarId,
          startDate,
          endDate,
          maxResults: params.maxResults || 10
        });
      } else {
        throw new Error(`Calendar provider '${provider}' is not supported or enabled`);
      }
    } catch (error) {
      logger.error(`Failed to get calendar events: ${error.message}`);
      throw new Error(`Failed to get calendar events: ${error.message}`);
    }
  }
};

/**
 * Create a new calendar event
 */
const createEvent = {
  description: "Create a new calendar event",
  parameters: {
    properties: {
      summary: {
        type: "string",
        description: "Title/summary of the event"
      },
      startDateTime: {
        type: "string",
        description: "Start date and time in ISO format or natural language"
      },
      endDateTime: {
        type: "string",
        description: "End date and time in ISO format or natural language"
      },
      description: {
        type: "string",
        description: "Description of the event"
      },
      location: {
        type: "string",
        description: "Location of the event"
      },
      attendees: {
        type: "array",
        items: {
          type: "string"
        },
        description: "List of email addresses of attendees"
      },
      calendarId: {
        type: "string",
        description: "ID of the calendar to create the event in (defaults to primary calendar)"
      },
      provider: {
        type: "string",
        description: "Calendar provider to use (google, apple, outlook)"
      }
    },
    required: ["summary", "startDateTime"]
  },
  async handler(params) {
    try {
      const provider = params.provider || defaultProvider;
      const calendarId = params.calendarId || 'primary';
      
      logger.info(`Creating event "${params.summary}" using ${provider} provider`);
      
      // Create event based on the provider
      if (provider === 'google') {
        const client = await getGoogleCalendarClient();
        return await createGoogleEvent(client, {
          calendarId,
          summary: params.summary,
          startDateTime: params.startDateTime,
          endDateTime: params.endDateTime,
          description: params.description,
          location: params.location,
          attendees: params.attendees
        });
      } else {
        throw new Error(`Calendar provider '${provider}' is not supported or enabled`);
      }
    } catch (error) {
      logger.error(`Failed to create calendar event: ${error.message}`);
      throw new Error(`Failed to create calendar event: ${error.message}`);
    }
  }
};

/**
 * Update an existing calendar event
 */
const updateEvent = {
  description: "Update an existing calendar event",
  parameters: {
    properties: {
      eventId: {
        type: "string",
        description: "ID of the event to update"
      },
      summary: {
        type: "string",
        description: "New title/summary of the event"
      },
      startDateTime: {
        type: "string",
        description: "New start date and time in ISO format or natural language"
      },
      endDateTime: {
        type: "string",
        description: "New end date and time in ISO format or natural language"
      },
      description: {
        type: "string",
        description: "New description of the event"
      },
      location: {
        type: "string",
        description: "New location of the event"
      },
      attendees: {
        type: "array",
        items: {
          type: "string"
        },
        description: "New list of email addresses of attendees"
      },
      calendarId: {
        type: "string",
        description: "ID of the calendar containing the event (defaults to primary calendar)"
      },
      provider: {
        type: "string",
        description: "Calendar provider to use (google, apple, outlook)"
      }
    },
    required: ["eventId"]
  },
  async handler(params) {
    try {
      const provider = params.provider || defaultProvider;
      const calendarId = params.calendarId || 'primary';
      
      logger.info(`Updating event ${params.eventId} using ${provider} provider`);
      
      // Update event based on the provider
      if (provider === 'google') {
        const client = await getGoogleCalendarClient();
        return await updateGoogleEvent(client, {
          calendarId,
          eventId: params.eventId,
          summary: params.summary,
          startDateTime: params.startDateTime,
          endDateTime: params.endDateTime,
          description: params.description,
          location: params.location,
          attendees: params.attendees
        });
      } else {
        throw new Error(`Calendar provider '${provider}' is not supported or enabled`);
      }
    } catch (error) {
      logger.error(`Failed to update calendar event: ${error.message}`);
      throw new Error(`Failed to update calendar event: ${error.message}`);
    }
  }
};

/**
 * Delete a calendar event
 */
const deleteEvent = {
  description: "Delete a calendar event",
  parameters: {
    properties: {
      eventId: {
        type: "string",
        description: "ID of the event to delete"
      },
      calendarId: {
        type: "string",
        description: "ID of the calendar containing the event (defaults to primary calendar)"
      },
      provider: {
        type: "string",
        description: "Calendar provider to use (google, apple, outlook)"
      }
    },
    required: ["eventId"]
  },
  async handler(params) {
    try {
      const provider = params.provider || defaultProvider;
      const calendarId = params.calendarId || 'primary';
      
      logger.info(`Deleting event ${params.eventId} using ${provider} provider`);
      
      // Delete event based on the provider
      if (provider === 'google') {
        const client = await getGoogleCalendarClient();
        return await deleteGoogleEvent(client, {
          calendarId,
          eventId: params.eventId
        });
      } else {
        throw new Error(`Calendar provider '${provider}' is not supported or enabled`);
      }
    } catch (error) {
      logger.error(`Failed to delete calendar event: ${error.message}`);
      throw new Error(`Failed to delete calendar event: ${error.message}`);
    }
  }
};

/**
 * List available calendars
 */
const listCalendars = {
  description: "List available calendars",
  parameters: {
    properties: {
      provider: {
        type: "string",
        description: "Calendar provider to use (google, apple, outlook)"
      }
    },
    required: []
  },
  async handler(params) {
    try {
      const provider = params.provider || defaultProvider;
      
      logger.info(`Listing calendars using ${provider} provider`);
      
      // List calendars based on the provider
      if (provider === 'google') {
        const client = await getGoogleCalendarClient();
        return await listGoogleCalendars(client);
      } else {
        throw new Error(`Calendar provider '${provider}' is not supported or enabled`);
      }
    } catch (error) {
      logger.error(`Failed to list calendars: ${error.message}`);
      throw new Error(`Failed to list calendars: ${error.message}`);
    }
  }
};

// Helper functions (would be implemented in the actual provider files)
async function getGoogleEvents(client, options) {
  // This would be implemented in the Google provider
  return { message: "This is a placeholder. Google Calendar integration would be implemented here." };
}

async function createGoogleEvent(client, eventData) {
  // This would be implemented in the Google provider
  return { message: "This is a placeholder. Google Calendar integration would be implemented here." };
}

async function updateGoogleEvent(client, eventData) {
  // This would be implemented in the Google provider
  return { message: "This is a placeholder. Google Calendar integration would be implemented here." };
}

async function deleteGoogleEvent(client, options) {
  // This would be implemented in the Google provider
  return { message: "This is a placeholder. Google Calendar integration would be implemented here." };
}

async function listGoogleCalendars(client) {
  // This would be implemented in the Google provider
  return { message: "This is a placeholder. Google Calendar integration would be implemented here." };
}

/**
 * Helper function to format relative dates
 */
function formatDate(dateStr) {
  if (!dateStr) return null;
  
  // Handle relative dates
  if (dateStr.toLowerCase() === 'today') {
    const today = new Date();
    return today.toISOString().split('T')[0];
  } else if (dateStr.toLowerCase() === 'tomorrow') {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  } else if (dateStr.toLowerCase() === 'yesterday') {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    return yesterday.toISOString().split('T')[0];
  }
  
  // Return the date as-is if it doesn't match any relative format
  return dateStr;
}

export default [
  getEvents,
  createEvent,
  updateEvent,
  deleteEvent,
  listCalendars
];
