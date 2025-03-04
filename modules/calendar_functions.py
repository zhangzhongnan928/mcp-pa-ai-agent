from typing import List, Dict, Any, Optional
import datetime
import os
import logging
import re
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Import the MCP server instance from the main file
from mcp_server import mcp, Context

logger = logging.getLogger("mcp-pa-agent.calendar")

# Helper functions
async def get_google_calendar_service():
    """Get an authenticated Google Calendar service if credentials are available."""
    try:
        # In a real implementation, you would handle OAuth2 credentials properly
        # For demo purposes, we'll just check if the required env vars exist
        if not all([
            os.getenv("GOOGLE_CLIENT_ID"),
            os.getenv("GOOGLE_CLIENT_SECRET"),
            os.getenv("GOOGLE_REFRESH_TOKEN")
        ]):
            return None
            
        credentials = Credentials(
            token=os.getenv("GOOGLE_ACCESS_TOKEN"),
            refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            token_uri="https://oauth2.googleapis.com/token",
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        
        return build("calendar", "v3", credentials=credentials)
    except Exception as e:
        logger.error(f"Failed to get calendar service: {str(e)}")
        return None

# Prompts
@mcp.prompt()
def schedule_meeting_prompt(participants: str, duration: str = "30 minutes") -> str:
    """Create a prompt for scheduling a meeting"""
    return f"Please help me schedule a {duration} meeting with {participants}. Suggest some appropriate times and draft a meeting invitation."

@mcp.prompt()
def check_availability_prompt(date: str) -> str:
    """Create a prompt for checking calendar availability"""
    return f"Please check my calendar for {date} and let me know when I'm free for meetings."

# Resources
@mcp.resource("calendar://today")
async def today_events_resource() -> str:
    """Resource providing today's calendar events"""
    service = await get_google_calendar_service()
    if not service:
        return "Calendar service is not available. Please check your Google API credentials."
    
    try:
        # Calculate time bounds for today
        now = datetime.datetime.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + datetime.timedelta(days=1)
        
        # Call the Calendar API
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_of_day.isoformat() + 'Z',
            timeMax=end_of_day.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return "No events scheduled for today."
            
        # Return JSON representation of events
        import json
        return json.dumps(events, indent=2)
    except Exception as e:
        logger.error(f"Error fetching today's events: {str(e)}")
        return f"Error fetching calendar events: {str(e)}"

# Tool functions
@mcp.tool()
async def get_events(days: int = 7, ctx: Context = None) -> str:
    """Get upcoming calendar events.
    
    Args:
        days: Number of days to look ahead (default 7)
    """
    if ctx:
        ctx.info(f"Getting calendar events for the next {days} days")
    
    if days < 1 or days > 30:
        error_msg = "Days parameter must be between 1 and 30."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    service = await get_google_calendar_service()
    if not service:
        error_msg = "Calendar service is not available. Please check your Google API credentials."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    try:
        # Calculate time bounds
        now = datetime.datetime.utcnow()
        end_date = now + datetime.timedelta(days=days)
        
        if ctx:
            ctx.info(f"Fetching events from {now.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Call the Calendar API
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now.isoformat() + 'Z',
            timeMax=end_date.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return f"No upcoming events found in the next {days} days."
            
        # Format the events nicely
        formatted_events = []
        for i, event in enumerate(events):
            if ctx:
                await ctx.report_progress(i, len(events))
                
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            # Handle different date formats
            try:
                if 'T' in start:  # DateTime format
                    start_time = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                    formatted_start = start_time.strftime("%Y-%m-%d %H:%M")
                else:  # Date-only format
                    formatted_start = start
                    
                if 'T' in end:  # DateTime format
                    end_time = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
                    formatted_end = end_time.strftime("%Y-%m-%d %H:%M")
                else:  # Date-only format
                    formatted_end = end
            except Exception:
                formatted_start = start
                formatted_end = end
            
            formatted_events.append(f"""
Event: {event.get('summary', 'Untitled Event')}
Time: {formatted_start} to {formatted_end}
Location: {event.get('location', 'No location specified')}
Description: {event.get('description', 'No description provided')}
""")
            
        return "\n---\n".join(formatted_events)
        
    except HttpError as error:
        error_msg = f"An error occurred while fetching calendar events: {error}"
        if ctx:
            ctx.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error fetching calendar events: {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return error_msg

@mcp.tool()
async def create_event(title: str, start_time: str, end_time: str, description: str = "", location: str = "", ctx: Context = None) -> str:
    """Create a new calendar event.
    
    Args:
        title: Title of the event
        start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS) or YYYY-MM-DD for all-day events
        end_time: End time in ISO format (YYYY-MM-DDTHH:MM:SS) or YYYY-MM-DD for all-day events
        description: Optional description of the event
        location: Optional location of the event
    """
    if ctx:
        ctx.info(f"Creating calendar event: {title}")
    
    # Validate inputs
    if not title:
        error_msg = "Event title cannot be empty."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    # Validate date formats
    date_only_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    datetime_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$')
    
    is_all_day = False
    
    # Check start time format
    if not (date_only_pattern.match(start_time) or datetime_pattern.match(start_time)):
        error_msg = "Invalid start time format. Use YYYY-MM-DD for all-day events or YYYY-MM-DDTHH:MM:SS for specific times."
        if ctx:
            ctx.error(error_msg)
        return error_msg
        
    # Check end time format
    if not (date_only_pattern.match(end_time) or datetime_pattern.match(end_time)):
        error_msg = "Invalid end time format. Use YYYY-MM-DD for all-day events or YYYY-MM-DDTHH:MM:SS for specific times."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    # Determine if this is an all-day event
    if date_only_pattern.match(start_time) and date_only_pattern.match(end_time):
        is_all_day = True
    elif date_only_pattern.match(start_time) != date_only_pattern.match(end_time):
        error_msg = "Both start and end times must be in the same format (either both dates or both date-times)."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    service = await get_google_calendar_service()
    if not service:
        error_msg = "Calendar service is not available. Please check your Google API credentials."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    try:
        # Create event object based on whether it's an all-day event or not
        event = {
            'summary': title,
            'location': location,
            'description': description,
        }
        
        timezone = 'America/Los_Angeles'  # Default timezone, should be configurable
        
        if is_all_day:
            # For all-day events, end date should be the next day
            if start_time == end_time:
                # If start and end are the same, make it a one-day event
                end_date = (datetime.datetime.strptime(end_time, '%Y-%m-%d') + 
                           datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                end_date = end_time
                
            event['start'] = {'date': start_time}
            event['end'] = {'date': end_date}
        else:
            # For specific time events
            event['start'] = {
                'dateTime': start_time,
                'timeZone': timezone,
            }
            event['end'] = {
                'dateTime': end_time,
                'timeZone': timezone,
            }
        
        if ctx:
            ctx.info(f"Sending event creation request to Google Calendar API")
            
        event = service.events().insert(calendarId='primary', body=event).execute()
        return f"Event created successfully: {event.get('htmlLink')}"
        
    except HttpError as error:
        error_msg = f"Calendar API error: {error}"
        if ctx:
            ctx.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"An error occurred while creating the event: {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return error_msg

@mcp.tool()
async def get_free_time(date: str, ctx: Context = None) -> str:
    """Find free time slots in your calendar for a specific date.
    
    Args:
        date: The date to check in YYYY-MM-DD format
    """
    if ctx:
        ctx.info(f"Finding free time slots for {date}")
    
    # Validate date format
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    if not date_pattern.match(date):
        error_msg = f"Invalid date format: {date}. Please use YYYY-MM-DD."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    service = await get_google_calendar_service()
    if not service:
        error_msg = "Calendar service is not available. Please check your Google API credentials."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    try:
        # Parse the requested date
        requested_date = datetime.datetime.strptime(date, '%Y-%m-%d')
        start_of_day = requested_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = requested_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Define working hours (9 AM to 5 PM)
        business_start = requested_date.replace(hour=9, minute=0, second=0, microsecond=0)
        business_end = requested_date.replace(hour=17, minute=0, second=0, microsecond=0)
        
        if ctx:
            ctx.info(f"Fetching events for {date}")
        
        # Get events for that day
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_of_day.isoformat() + 'Z',
            timeMax=end_of_day.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return f"You have no events on {date}. The entire day is free!"
        
        # Collect busy times
        busy_times = []
        for event in events:
            if ctx:
                ctx.debug(f"Processing event: {event.get('summary')}")
                
            # Skip declined events
            if 'attendees' in event:
                for attendee in event['attendees']:
                    if attendee.get('self', False) and attendee.get('responseStatus') == 'declined':
                        continue
            
            start_str = event['start'].get('dateTime')
            end_str = event['end'].get('dateTime')
            
            # Skip all-day events from free time calculation
            if not start_str or not end_str:
                continue
                
            # Parse event times
            event_start = datetime.datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            event_end = datetime.datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            
            # Store busy slots
            busy_times.append((event_start, event_end, event.get('summary', 'Busy')))
        
        # Sort busy times
        busy_times.sort(key=lambda x: x[0])
        
        # Find free slots within business hours
        free_slots = []
        current_time = business_start
        
        for busy_start, busy_end, summary in busy_times:
            # If there's a gap between current time and busy start, it's a free slot
            if current_time < busy_start and current_time < business_end:
                end_time = min(busy_start, business_end)
                free_slots.append((current_time, end_time))
            
            # Move current time to the end of this busy period
            current_time = max(current_time, busy_end)
        
        # Add any remaining time until end of business hours
        if current_time < business_end:
            free_slots.append((current_time, business_end))
        
        # Format and return free slots
        if not free_slots:
            return f"You're fully booked on {date}. No free slots available during business hours (9 AM - 5 PM)."
        
        formatted_free_times = []
        for start, end in free_slots:
            # Calculate duration in minutes
            duration = int((end - start).total_seconds() / 60)
            
            if duration < 15:  # Skip very short gaps
                continue
                
            formatted_free_times.append(f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')} ({duration} minutes)")
        
        if not formatted_free_times:
            return f"You have some gaps on {date}, but they're all shorter than 15 minutes."
            
        return f"Free time slots on {date}:\n\n" + "\n".join(formatted_free_times)
        
    except HttpError as error:
        error_msg = f"An error occurred while fetching calendar information: {error}"
        if ctx:
            ctx.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error checking free time: {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return error_msg 