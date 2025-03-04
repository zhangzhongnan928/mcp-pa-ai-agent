from typing import List, Dict, Any, Optional
import os
import json
import logging
import re
from datetime import datetime
import httpx

# Import the MCP server instance from the main file
from mcp_server import mcp, Context

logger = logging.getLogger("mcp-pa-agent.tasks")

# Mock tasks database (in a real implementation, this would be a proper database)
TASKS_FILE = "tasks_data.json"

async def get_tasks():
    """Get all tasks from the storage."""
    try:
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading tasks: {str(e)}")
        return []

async def save_tasks(tasks):
    """Save tasks to the storage."""
    try:
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving tasks: {str(e)}")
        return False

# Resources
@mcp.resource("tasks://all")
async def all_tasks_resource() -> str:
    """Provide all tasks as a resource"""
    tasks = await get_tasks()
    return json.dumps(tasks, indent=2)

@mcp.resource("tasks://status/{status}")
async def tasks_by_status_resource(status: str) -> str:
    """Provide tasks filtered by status"""
    all_tasks = await get_tasks()
    filtered = [t for t in all_tasks if t.get('status', '').lower() == status.lower()]
    return json.dumps(filtered, indent=2)

@mcp.resource("tasks://priority/{priority}")
async def tasks_by_priority_resource(priority: str) -> str:
    """Provide tasks filtered by priority"""
    all_tasks = await get_tasks()
    filtered = [t for t in all_tasks if t.get('priority', '').lower() == priority.lower()]
    return json.dumps(filtered, indent=2)

# Prompts
@mcp.prompt()
def create_task_prompt(description: str, priority: str = "medium") -> str:
    """Create a prompt for task creation"""
    return f"Please help me create a new task based on this description: '{description}'. It should have {priority} priority. Please organize the information into title, description, and suggest a reasonable due date if applicable."

# Tool functions
@mcp.tool()
async def list_tasks(status: str = "all", ctx: Context = None) -> str:
    """List tasks with optional filtering by status.
    
    Args:
        status: Filter tasks by status ('all', 'pending', 'completed', 'in_progress')
    """
    if ctx:
        ctx.info(f"Listing tasks with status filter: {status}")
    
    tasks = await get_tasks()
    
    if not tasks:
        return "No tasks found."
    
    filtered_tasks = tasks
    if status.lower() != "all":
        filtered_tasks = [task for task in tasks if task.get('status', '').lower() == status.lower()]
    
    if not filtered_tasks:
        return f"No tasks with status '{status}' found."
    
    formatted_tasks = []
    for idx, task in enumerate(filtered_tasks, 1):
        due_date = task.get('due_date', 'No due date')
        created_at = task.get('created_at', 'Unknown')
        updated_at = task.get('updated_at', created_at)
        
        formatted_tasks.append(f"""
Task #{task.get('id', idx)}: {task.get('title', 'Untitled')}
Status: {task.get('status', 'Not specified')}
Priority: {task.get('priority', 'Not specified')}
Due Date: {due_date}
Description: {task.get('description', 'No description provided')}
Created: {created_at}
Last Updated: {updated_at}
""")
    
    return "\n---\n".join(formatted_tasks)

@mcp.tool()
async def add_task(title: str, description: str = "", priority: str = "medium", due_date: str = "", ctx: Context = None) -> str:
    """Add a new task.
    
    Args:
        title: Title of the task
        description: Optional description of the task
        priority: Priority level ('low', 'medium', 'high')
        due_date: Optional due date in YYYY-MM-DD format
    """
    if ctx:
        ctx.info(f"Adding new task: {title}")
    
    tasks = await get_tasks()
    
    # Validate title
    if not title or len(title.strip()) == 0:
        error_msg = "Error: Task title cannot be empty."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    # Validate priority
    valid_priorities = ['low', 'medium', 'high']
    if priority.lower() not in valid_priorities:
        error_msg = f"Invalid priority: {priority}. Must be one of: {', '.join(valid_priorities)}."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    # Validate due date format if provided
    if due_date:
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        if not date_pattern.match(due_date):
            error_msg = f"Invalid due date format: {due_date}. Please use YYYY-MM-DD."
            if ctx:
                ctx.error(error_msg)
            return error_msg
            
        try:
            datetime.strptime(due_date, '%Y-%m-%d')
        except ValueError:
            error_msg = f"Invalid due date: {due_date}. Please use a valid date in YYYY-MM-DD format."
            if ctx:
                ctx.error(error_msg)
            return error_msg
    
    # Generate a unique ID
    task_id = 1
    if tasks:
        existing_ids = [task.get('id', 0) for task in tasks]
        task_id = max(existing_ids) + 1
    
    new_task = {
        'id': task_id,
        'title': title,
        'description': description,
        'status': 'pending',
        'priority': priority.lower(),
        'due_date': due_date,
        'created_at': datetime.now().isoformat(),
    }
    
    tasks.append(new_task)
    if await save_tasks(tasks):
        success_msg = f"Task '{title}' added successfully with ID {new_task['id']}."
        if ctx:
            ctx.info(success_msg)
        return success_msg
    else:
        error_msg = "Failed to save the task. Please try again."
        if ctx:
            ctx.error(error_msg)
        return error_msg

@mcp.tool()
async def update_task_status(task_id: int, status: str, ctx: Context = None) -> str:
    """Update the status of a task.
    
    Args:
        task_id: The ID of the task to update
        status: New status ('pending', 'in_progress', 'completed')
    """
    if ctx:
        ctx.info(f"Updating task #{task_id} status to: {status}")
    
    # Validate status
    valid_statuses = ['pending', 'in_progress', 'completed']
    if status.lower() not in valid_statuses:
        error_msg = f"Invalid status: {status}. Must be one of: {', '.join(valid_statuses)}."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    tasks = await get_tasks()
    
    # Find the task with the given ID
    task_found = False
    for task in tasks:
        if task.get('id') == task_id:
            task_found = True
            old_status = task.get('status', 'unknown')
            task['status'] = status.lower()
            task['updated_at'] = datetime.now().isoformat()
            
            if await save_tasks(tasks):
                success_msg = f"Task #{task_id} status updated from '{old_status}' to '{status}'."
                if ctx:
                    ctx.info(success_msg)
                return success_msg
            else:
                error_msg = "Failed to update task status. Please try again."
                if ctx:
                    ctx.error(error_msg)
                return error_msg
    
    error_msg = f"Task with ID {task_id} not found."
    if ctx:
        ctx.error(error_msg)
    return error_msg

@mcp.tool()
async def delete_task(task_id: int, ctx: Context = None) -> str:
    """Delete a task.
    
    Args:
        task_id: The ID of the task to delete
    """
    if ctx:
        ctx.info(f"Deleting task #{task_id}")
    
    tasks = await get_tasks()
    
    # Find and remove the task with the given ID
    original_count = len(tasks)
    tasks = [task for task in tasks if task.get('id') != task_id]
    
    if len(tasks) < original_count:
        if await save_tasks(tasks):
            success_msg = f"Task #{task_id} deleted successfully."
            if ctx:
                ctx.info(success_msg)
            return success_msg
        else:
            error_msg = "Failed to delete task. Please try again."
            if ctx:
                ctx.error(error_msg)
            return error_msg
    else:
        error_msg = f"Task with ID {task_id} not found."
        if ctx:
            ctx.error(error_msg)
        return error_msg 