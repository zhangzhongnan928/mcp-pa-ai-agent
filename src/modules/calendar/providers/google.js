/**
 * Google Calendar Provider
 * Handles interaction with Google Calendar API
 */

import { google } from 'googleapis';
import logger from '../../../utils/logger.js';
import config from '../../../config/index.js';

let googleCalendarClient = null;

/**
 * Get an authenticated Google Calendar client
 * @returns {Promise<any>} Google Calendar client
 */
export async function getGoogleCalendarClient() {
  if (googleCalendarClient) {
    return googleCalendarClient;
  }

  try {
    logger.info('Initializing Google Calendar client');

    // Check if Google Calendar is enabled in config
    if (!config.modules.calendar.providers.google.enabled) {
      throw new Error('Google Calendar provider is disabled in configuration');
    }

    // Get auth credentials from environment variables
    const credentials = getGoogleCredentials();

    // Set up OAuth2 client
    const oAuth2Client = new google.auth.OAuth2(
      credentials.clientId,
      credentials.clientSecret,
      credentials.redirectUri
    );

    // Set credentials
    oAuth2Client.setCredentials({
      refresh_token: credentials.refreshToken,
      access_token: credentials.accessToken,
    });

    // Create Calendar client
    googleCalendarClient = google.calendar({ version: 'v3', auth: oAuth2Client });

    logger.info('Google Calendar client initialized successfully');
    return googleCalendarClient;
  } catch (error) {
    logger.error(`Failed to initialize Google Calendar client: ${error.message}`);
    throw new Error(`Failed to initialize Google Calendar client: ${error.message}`);
  }
}

/**
 * Get Google API credentials from environment variables
 * @returns {Object} Google API credentials
 */
function getGoogleCredentials() {
  const clientId = process.env.GOOGLE_CLIENT_ID;
  const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
  const redirectUri = process.env.GOOGLE_REDIRECT_URI;
  const refreshToken = process.env.GOOGLE_REFRESH_TOKEN;
  const accessToken = process.env.GOOGLE_ACCESS_TOKEN;

  if (!clientId || !clientSecret || !redirectUri || !refreshToken) {
    throw new Error('Missing required Google API credentials in environment variables');
  }

  return {
    clientId,
    clientSecret,
    redirectUri,
    refreshToken,
    accessToken,
  };
}

/**
 * Fetch events from Google Calendar
 * @param {Object} client - Google Calendar client
 * @param {Object} options - Options for fetching events
 * @returns {Promise<Array>} List of events
 */
export async function getEvents(client, options) {
  try {
    const { calendarId, startDate, endDate, maxResults } = options;

    logger.info(`Fetching events from Google Calendar ${calendarId}`);

    // Format start and end times as RFC3339 timestamps
    let timeMin = new Date(startDate).toISOString();
    let timeMax = endDate ? new Date(endDate).toISOString() : undefined;

    // Fetch events
    const response = await client.events.list({
      calendarId,
      timeMin,
      timeMax,
      maxResults: maxResults || 10,
      singleEvents: true,
      orderBy: 'startTime',
    });

    // Transform and return events
    return response.data.items.map(event => ({
      id: event.id,
      summary: event.summary,
      description: event.description,
      location: event.location,
      start: event.start.dateTime || event.start.date,
      end: event.end.dateTime || event.end.date,
      attendees: event.attendees ? event.attendees.map(a => a.email) : [],
      link: event.htmlLink,
      created: event.created,
      updated: event.updated,
    }));
  } catch (error) {
    logger.error(`Failed to fetch Google Calendar events: ${error.message}`);
    throw new Error(`Failed to fetch calendar events: ${error.message}`);
  }
}

/**
 * Create a new event in Google Calendar
 * @param {Object} client - Google Calendar client
 * @param {Object} eventData - Event data
 * @returns {Promise<Object>} Created event
 */
export async function createEvent(client, eventData) {
  try {
    const { calendarId, summary, startDateTime, endDateTime, description, location, attendees } = eventData;

    logger.info(`Creating event "${summary}" in Google Calendar ${calendarId}`);

    // Prepare event resource
    const event = {
      summary,
      description,
      location,
      start: {
        dateTime: new Date(startDateTime).toISOString(),
        timeZone: config.user.timezone,
      },
      end: {
        dateTime: endDateTime ? new Date(endDateTime).toISOString() : new Date(new Date(startDateTime).getTime() + 3600000).toISOString(),
        timeZone: config.user.timezone,
      },
    };

    // Add attendees if provided
    if (attendees && attendees.length > 0) {
      event.attendees = attendees.map(email => ({ email }));
    }

    // Insert event
    const response = await client.events.insert({
      calendarId,
      resource: event,
      sendUpdates: 'all',
    });

    // Return created event
    return {
      id: response.data.id,
      summary: response.data.summary,
      description: response.data.description,
      location: response.data.location,
      start: response.data.start.dateTime,
      end: response.data.end.dateTime,
      attendees: response.data.attendees ? response.data.attendees.map(a => a.email) : [],
      link: response.data.htmlLink,
    };
  } catch (error) {
    logger.error(`Failed to create Google Calendar event: ${error.message}`);
    throw new Error(`Failed to create calendar event: ${error.message}`);
  }
}

/**
 * Update an existing event in Google Calendar
 * @param {Object} client - Google Calendar client
 * @param {Object} eventData - Event data
 * @returns {Promise<Object>} Updated event
 */
export async function updateEvent(client, eventData) {
  try {
    const { calendarId, eventId, summary, startDateTime, endDateTime, description, location, attendees } = eventData;

    logger.info(`Updating event ${eventId} in Google Calendar ${calendarId}`);

    // First get the existing event
    const existingEvent = await client.events.get({
      calendarId,
      eventId,
    });

    // Prepare update with only the provided fields
    const updatedEvent = { ...existingEvent.data };
    
    if (summary) updatedEvent.summary = summary;
    if (description) updatedEvent.description = description;
    if (location) updatedEvent.location = location;
    
    if (startDateTime) {
      updatedEvent.start = {
        dateTime: new Date(startDateTime).toISOString(),
        timeZone: config.user.timezone,
      };
    }
    
    if (endDateTime) {
      updatedEvent.end = {
        dateTime: new Date(endDateTime).toISOString(),
        timeZone: config.user.timezone,
      };
    }
    
    if (attendees) {
      updatedEvent.attendees = attendees.map(email => ({ email }));
    }

    // Update event
    const response = await client.events.update({
      calendarId,
      eventId,
      resource: updatedEvent,
      sendUpdates: 'all',
    });

    // Return updated event
    return {
      id: response.data.id,
      summary: response.data.summary,
      description: response.data.description,
      location: response.data.location,
      start: response.data.start.dateTime,
      end: response.data.end.dateTime,
      attendees: response.data.attendees ? response.data.attendees.map(a => a.email) : [],
      link: response.data.htmlLink,
    };
  } catch (error) {
    logger.error(`Failed to update Google Calendar event: ${error.message}`);
    throw new Error(`Failed to update calendar event: ${error.message}`);
  }
}

/**
 * Delete an event from Google Calendar
 * @param {Object} client - Google Calendar client
 * @param {Object} options - Delete options
 * @returns {Promise<Object>} Result of deletion
 */
export async function deleteEvent(client, options) {
  try {
    const { calendarId, eventId } = options;

    logger.info(`Deleting event ${eventId} from Google Calendar ${calendarId}`);

    // Delete event
    await client.events.delete({
      calendarId,
      eventId,
      sendUpdates: 'all',
    });

    // Return success
    return {
      success: true,
      message: `Event ${eventId} deleted successfully`,
    };
  } catch (error) {
    logger.error(`Failed to delete Google Calendar event: ${error.message}`);
    throw new Error(`Failed to delete calendar event: ${error.message}`);
  }
}

/**
 * List available calendars from Google Calendar
 * @param {Object} client - Google Calendar client
 * @returns {Promise<Array>} List of calendars
 */
export async function listCalendars(client) {
  try {
    logger.info('Listing Google Calendars');

    // List calendars
    const response = await client.calendarList.list();

    // Transform and return calendars
    return response.data.items.map(calendar => ({
      id: calendar.id,
      summary: calendar.summary,
      description: calendar.description,
      primary: calendar.primary || false,
      accessRole: calendar.accessRole,
    }));
  } catch (error) {
    logger.error(`Failed to list Google Calendars: ${error.message}`);
    throw new Error(`Failed to list calendars: ${error.message}`);
  }
}
