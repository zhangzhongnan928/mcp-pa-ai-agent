from typing import List, Dict, Any, Optional
import os
import logging
import base64
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Import the MCP server instance from the main file
from mcp_server import mcp, Context

logger = logging.getLogger("mcp-pa-agent.email")

# Helper functions
async def get_gmail_service():
    """Get an authenticated Gmail service if credentials are available."""
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
            scopes=["https://www.googleapis.com/auth/gmail.readonly", 
                    "https://www.googleapis.com/auth/gmail.send"]
        )
        
        return build("gmail", "v1", credentials=credentials)
    except Exception as e:
        logger.error(f"Failed to get Gmail service: {str(e)}")
        return None

# Prompts
@mcp.prompt()
def compose_email_prompt(to: str, subject: str = "") -> str:
    """Create a prompt for composing an email"""
    return f"Please write a professional email to {to}" + (f" with the subject '{subject}'" if subject else "") + "."

@mcp.prompt()
def reply_to_email_prompt(message_id: str) -> str:
    """Create a prompt for replying to an email"""
    return f"Please help me draft a reply to the email with message ID {message_id}."

# Resources
@mcp.resource("email://inbox/{max_results}")
async def inbox_resource(max_results: str = "10") -> str:
    """Resource providing emails from the inbox"""
    service = await get_gmail_service()
    if not service:
        return "Gmail service is not available. Please check your Google API credentials."
    
    try:
        # Convert max_results to int with validation
        try:
            num_results = int(max_results)
            if num_results < 1 or num_results > 50:
                return "Invalid max_results parameter. Must be between 1 and 50."
        except ValueError:
            return "Invalid max_results parameter. Must be an integer."
        
        # Call the Gmail API
        results = service.users().messages().list(
            userId='me',
            labelIds=["INBOX"],
            maxResults=num_results
        ).execute()
        
        # Return JSON representation
        import json
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Error fetching inbox: {str(e)}")
        return f"Error fetching inbox: {str(e)}"

# Tool functions
@mcp.tool()
async def get_emails(max_results: int = 10, label: str = "INBOX", ctx: Context = None) -> str:
    """Get recent emails from a specific label.
    
    Args:
        max_results: Maximum number of emails to retrieve (default 10, max 50)
        label: Email label to fetch from (default 'INBOX')
    """
    if ctx:
        ctx.info(f"Getting up to {max_results} emails from label: {label}")
    
    if max_results < 1 or max_results > 50:
        error_msg = "max_results must be between 1 and 50."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    service = await get_gmail_service()
    if not service:
        error_msg = "Gmail service is not available. Please check your Google API credentials."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    try:
        # Call the Gmail API
        results = service.users().messages().list(
            userId='me',
            labelIds=[label],
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return f"No messages found in {label}."
        
        if ctx:
            ctx.info(f"Found {len(messages)} emails. Fetching details...")
        
        # Format the emails nicely
        formatted_emails = []
        for i, message in enumerate(messages):
            if ctx:
                await ctx.report_progress(i, len(messages))
                
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            
            # Extract headers
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No subject')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown sender')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown date')
            
            # Extract snippet
            snippet = msg.get('snippet', 'No preview available')
            
            formatted_emails.append(f"""
From: {sender}
Date: {date}
Subject: {subject}
Preview: {snippet}
Message ID: {message['id']}
""")
        
        return "\n---\n".join(formatted_emails)
    
    except HttpError as error:
        error_msg = f"An error occurred while fetching emails: {error}"
        if ctx:
            ctx.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error fetching emails: {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return error_msg

@mcp.tool()
async def read_email(message_id: str, ctx: Context = None) -> str:
    """Read the full content of a specific email.
    
    Args:
        message_id: The ID of the email to read
    """
    if ctx:
        ctx.info(f"Reading email with ID: {message_id}")
    
    if not message_id or message_id.strip() == "":
        error_msg = "Message ID cannot be empty."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    service = await get_gmail_service()
    if not service:
        error_msg = "Gmail service is not available. Please check your Google API credentials."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    try:
        # Get the full message
        msg = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        
        # Extract headers
        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No subject')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown sender')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown date')
        to = next((h['value'] for h in headers if h['name'].lower() == 'to'), 'Unknown recipient')
        
        if ctx:
            ctx.info(f"Retrieved email: '{subject}' from {sender}")
        
        # Extract body
        body = ""
        if 'parts' in msg['payload']:
            for part in msg['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
        elif 'body' in msg['payload'] and 'data' in msg['payload']['body']:
            body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')
        
        if not body:
            body = "Email body could not be extracted (possibly HTML-only content)"
        
        return f"""
From: {sender}
To: {to}
Date: {date}
Subject: {subject}

{body}
"""
    
    except HttpError as error:
        error_msg = f"An error occurred while reading the email: {error}"
        if ctx:
            ctx.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error reading email: {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return error_msg

@mcp.tool()
async def send_email(to: str, subject: str, body: str, ctx: Context = None) -> str:
    """Send an email.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body (plain text)
    """
    if ctx:
        ctx.info(f"Preparing to send email to: {to}")
    
    # Validate inputs
    if not to or len(to.strip()) == 0:
        error_msg = "Recipient email address cannot be empty."
        if ctx:
            ctx.error(error_msg)
        return error_msg
        
    # Validate email format with regex
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not email_pattern.match(to):
        error_msg = f"Invalid email address format: {to}"
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    if not subject or len(subject.strip()) == 0:
        error_msg = "Email subject cannot be empty."
        if ctx:
            ctx.error(error_msg)
        return error_msg
        
    if not body or len(body.strip()) == 0:
        error_msg = "Email body cannot be empty."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    service = await get_gmail_service()
    if not service:
        error_msg = "Gmail service is not available. Please check your Google API credentials."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    try:
        if ctx:
            ctx.info("Creating email message...")
            
        # Create the email message
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        
        # Add text part
        msg = MIMEText(body)
        message.attach(msg)
        
        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        if ctx:
            ctx.info("Sending email...")
            
        # Send the message
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        success_msg = f"Email sent successfully. Message ID: {sent_message['id']}"
        if ctx:
            ctx.info(success_msg)
        return success_msg
    
    except HttpError as error:
        error_msg = f"An error occurred while sending the email: {error}"
        if ctx:
            ctx.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error sending email: {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return error_msg

@mcp.tool()
async def search_emails(query: str, max_results: int = 10, ctx: Context = None) -> str:
    """Search emails using Gmail search syntax.
    
    Args:
        query: Search query using Gmail search operators
        max_results: Maximum number of results to return (default 10, max 50)
    """
    if ctx:
        ctx.info(f"Searching emails with query: {query}")
    
    if not query or len(query.strip()) == 0:
        error_msg = "Search query cannot be empty."
        if ctx:
            ctx.error(error_msg)
        return error_msg
        
    if max_results < 1 or max_results > 50:
        error_msg = "max_results must be between 1 and 50."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    service = await get_gmail_service()
    if not service:
        error_msg = "Gmail service is not available. Please check your Google API credentials."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    try:
        # Search emails
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return f"No emails matching '{query}' found."
        
        if ctx:
            ctx.info(f"Found {len(messages)} matching emails. Fetching details...")
        
        # Format the emails nicely
        formatted_emails = []
        for i, message in enumerate(messages):
            if ctx:
                await ctx.report_progress(i, len(messages))
                
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            
            # Extract headers
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No subject')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown sender')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown date')
            
            # Extract snippet
            snippet = msg.get('snippet', 'No preview available')
            
            formatted_emails.append(f"""
From: {sender}
Date: {date}
Subject: {subject}
Preview: {snippet}
Message ID: {message['id']}
""")
        
        return f"Search results for '{query}':\n\n" + "\n---\n".join(formatted_emails)
    
    except HttpError as error:
        error_msg = f"An error occurred while searching emails: {error}"
        if ctx:
            ctx.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error searching emails: {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return error_msg 