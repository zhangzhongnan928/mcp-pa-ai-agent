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

    logger.info(`Successfully fetched ${response.data.items.length} events`);
    
    // Transform events to a cleaner format
    return response.data.items.map(event => ({
      id: event.id,
      summary: event.summary,
      description: event.description,
      location: event.location,
      start: event.start.dateTime || event.start.date,
      end: event.end.dateTime || event.end.date,
      organizer: event.organizer ? event.organizer.email : null,
      attendees: event.attendees ? event.attendees.map(a => a.email) : [],
      status: event.status,
      htmlLink: event.htmlLink,
      created: event.created,
      updated: event.updated,
    }));
  } catch (error) {
    logger.error(`Failed to fetch events from Google Calendar: ${error.message}`);
    throw new Error(`Failed to fetch events from Google Calendar: ${error.message}`);
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
    const { 
      calendarId, 
      summary, 
      startDateTime, 
      endDateTime, 
      description, 
      location, 
      attendees 
    } = eventData;

    logger.info(`Creating event in Google Calendar ${calendarId}`);

    // Format start and end times
    const start = formatEventDateTime(startDateTime);
    const end = formatEventDateTime(endDateTime || addHour(startDateTime));

    // Format attendees if provided
    const formattedAttendees = attendees 
      ? attendees.map(email => ({ email })) 
      : undefined;

    // Create event
    const event = {
      summary,
      description,
      location,
      start,
      end,
      attendees: formattedAttendees,
    };

    const response = await client.events.insert({
      calendarId,
      resource: event,
      sendUpdates: 'all', // Notify attendees
    });

    logger.info(`Successfully created event with ID: ${response.data.id}`);
    
    return {
      id: response.data.id,
      summary: response.data.summary,
      description: response.data.description,
      location: response.data.location,
      start: response.data.start.dateTime || response.data.start.date,
      end: response.data.end.dateTime || response.data.end.date,
      htmlLink: response.data.htmlLink,
      attendees: response.data.attendees ? response.data.attendees.map(a => a.email) : [],
    };
  } catch (error) {
    logger.error(`Failed to create event in Google Calendar: ${error.message}`);
    throw new Error(`Failed to create event in Google Calendar: ${error.message}`);
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
    const { 
      calendarId, 
      eventId, 
      summary, 
      startDateTime, 
      endDateTime, 
      description, 
      location, 
      attendees 
    } = eventData;

    logger.info(`Updating event ${eventId} in Google Calendar ${calendarId}`);

    // First, get the current event
    const currentEvent = await client.events.get({
      calendarId,
      eventId,
    });

    // Format start and end times if provided
    const start = startDateTime 
      ? formatEventDateTime(startDateTime) 
      : currentEvent.data.start;
      
    const end = endDateTime 
      ? formatEventDateTime(endDateTime) 
      : currentEvent.data.end;

    // Format attendees if provided
    const formattedAttendees = attendees 
      ? attendees.map(email => ({ email })) 
      : currentEvent.data.attendees;

    // Update event with new data or keep existing data
    const event = {
      summary: summary || currentEvent.data.summary,
      description: description !== undefined ? description : currentEvent.data.description,
      location: location !== undefined ? location : currentEvent.data.location,
      start,
      end,
      attendees: formattedAttendees,
    };

    const response = await client.events.update({
      calendarId,
      eventId,
      resource: event,
      sendUpdates: 'all', // Notify attendees
    });

    logger.info(`Successfully updated event ${eventId}`);
    
    return {
      id: response.data.id,
      summary: response.data.summary,
      description: response.data.description,
      location: response.data.location,
      start: response.data.start.dateTime || response.data.start.date,
      end: response.data.end.dateTime || response.data.end.date,
      htmlLink: response.data.htmlLink,
      attendees: response.data.attendees ? response.data.attendees.map(a => a.email) : [],
      updated: response.data.updated,
    };
  } catch (error) {
    logger.error(`Failed to update event in Google Calendar: ${error.message}`);
    throw new Error(`Failed to update event in Google Calendar: ${error.message}`);
  }
}

/**
 * Delete an event from Google Calendar
 * @param {Object} client - Google Calendar client
 * @param {Object} options - Options for deleting event
 * @returns {Promise<Object>} Result of the operation
 */
export async function deleteEvent(client, options) {
  try {
    const { calendarId, eventId } = options;

    logger.info(`Deleting event ${eventId} from Google Calendar ${calendarId}`);

    await client.events.delete({
      calendarId,
      eventId,
      sendUpdates: 'all', // Notify attendees
    });

    logger.info(`Successfully deleted event ${eventId}`);
    
    return {
      success: true,
      message: `Event ${eventId} has been deleted`,
      eventId,
      calendarId,
    };
  } catch (error) {
    logger.error(`Failed to delete event from Google Calendar: ${error.message}`);
    throw new Error(`Failed to delete event from Google Calendar: ${error.message}`);
  }
}

/**
 * List available calendars from Google Calendar
 * @param {Object} client - Google Calendar client
 * @returns {Promise<Array>} List of calendars
 */
export async function listCalendars(client) {
  try {
    logger.info('Fetching available Google Calendars');

    const response = await client.calendarList.list();

    logger.info(`Successfully fetched ${response.data.items.length} calendars`);
    
    return response.data.items.map(calendar => ({
      id: calendar.id,
      summary: calendar.summary,
      description: calendar.description,
      primary: calendar.primary || false,
      accessRole: calendar.accessRole,
    }));
  } catch (error) {
    logger.error(`Failed to fetch Google Calendars: ${error.message}`);
    throw new Error(`Failed to fetch Google Calendars: ${error.message}`);
  }
}

/**
 * Helper function to format date and time for Google Calendar API
 * @param {string} dateTimeStr - Date and time string
 * @returns {Object} Formatted date and time object
 */
function formatEventDateTime(dateTimeStr) {
  try {
    // For full ISO datetime strings (with time)
    if (dateTimeStr.includes('T')) {
      return {
        dateTime: new Date(dateTimeStr).toISOString(),
        timeZone: config.user.timezone,
      };
    }
    
    // For date-only strings
    return {
      date: dateTimeStr,
    };
  } catch (error) {
    logger.error(`Error formatting date: ${error.message}`);
    throw new Error(`Invalid date format: ${dateTimeStr}`);
  }
}

/**
 * Helper function to add one hour to a datetime string
 * @param {string} dateTimeStr - Date and time string
 * @returns {string} New date and time string with one hour added
 */
function addHour(dateTimeStr) {
  try {
    const date = new Date(dateTimeStr);
    date.setHours(date.getHours() + 1);
    return date.toISOString();
  } catch (error) {
    logger.error(`Error adding hour to date: ${error.message}`);
    throw new Error(`Invalid date format: ${dateTimeStr}`);
  }
}
