#!/usr/bin/env python3
import asyncio
import pytest
import os
import sys
import json
from unittest.mock import AsyncMock, patch, MagicMock

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import server and modules for testing
from mcp_server import mcp

try:
    from mcp.testing import ClientServerTestHarness
    HAS_TEST_HARNESS = True
except ImportError:
    HAS_TEST_HARNESS = False
    print("Warning: mcp.testing not available. Some tests will be skipped.")

# Skip tests that require the test harness if it's not available
requires_test_harness = pytest.mark.skipif(
    not HAS_TEST_HARNESS,
    reason="mcp.testing not available in this version of MCP SDK"
)

# Test fixtures
@pytest.fixture
def mock_task_data():
    """Fixture providing sample task data for testing."""
    return [
        {
            "id": 1,
            "title": "Test Task 1",
            "description": "This is a test task",
            "status": "pending",
            "priority": "high",
            "due_date": "2023-12-31",
            "created_at": "2023-01-01T10:00:00"
        },
        {
            "id": 2,
            "title": "Test Task 2",
            "description": "Another test task",
            "status": "completed",
            "priority": "medium",
            "due_date": "2023-11-15",
            "created_at": "2023-01-05T14:30:00",
            "updated_at": "2023-01-10T09:15:00"
        }
    ]

@pytest.fixture
def mock_get_tasks(mock_task_data):
    """Mock the get_tasks function to return test data."""
    from modules.tasks_functions import get_tasks
    original_get_tasks = get_tasks
    
    async def mock_fn():
        return mock_task_data
    
    # Apply mock
    from modules import tasks_functions
    tasks_functions.get_tasks = mock_fn
    
    yield mock_fn
    
    # Restore original
    tasks_functions.get_tasks = original_get_tasks

@pytest.fixture
def mock_save_tasks():
    """Mock the save_tasks function."""
    from modules.tasks_functions import save_tasks
    original_save_tasks = save_tasks
    
    mock_fn = AsyncMock(return_value=True)
    
    # Apply mock
    from modules import tasks_functions
    tasks_functions.save_tasks = mock_fn
    
    yield mock_fn
    
    # Restore original
    tasks_functions.save_tasks = original_save_tasks

@pytest.fixture
async def harness():
    """Create a test harness for the MCP server if available."""
    if not HAS_TEST_HARNESS:
        pytest.skip("Test harness not available")
        return None
        
    async with ClientServerTestHarness(mcp) as harness:
        yield harness

# Unit tests
@pytest.mark.asyncio
async def test_list_tasks(mock_get_tasks):
    """Test the list_tasks function."""
    from modules.tasks_functions import list_tasks
    
    # Test with default parameters
    result = await list_tasks()
    assert "Test Task 1" in result
    assert "Test Task 2" in result
    assert "high" in result
    assert "completed" in result
    
    # Test with status filter
    result = await list_tasks(status="completed")
    assert "Test Task 1" not in result
    assert "Test Task 2" in result

@pytest.mark.asyncio
async def test_add_task(mock_get_tasks, mock_save_tasks):
    """Test the add_task function."""
    from modules.tasks_functions import add_task
    
    # Test with valid parameters
    result = await add_task(
        title="New Test Task",
        description="A new test task",
        priority="low",
        due_date="2023-12-25"
    )
    
    assert "added successfully" in result
    assert mock_save_tasks.called
    
    # Get the saved tasks data
    saved_data = mock_save_tasks.call_args[0][0]
    assert len(saved_data) == 3  # Two fixtures + one new
    assert saved_data[2]["title"] == "New Test Task"
    assert saved_data[2]["priority"] == "low"
    
    # Test with invalid priority
    result = await add_task(
        title="Invalid Priority Task",
        priority="invalid"
    )
    assert "Invalid priority" in result
    
    # Test with invalid date format
    result = await add_task(
        title="Invalid Date Task",
        due_date="12/25/2023"  # Wrong format
    )
    assert "Invalid due date format" in result
    
    # Test with empty title
    result = await add_task(
        title="",
        description="Empty title"
    )
    assert "title cannot be empty" in result.lower()

# Integration tests using the test harness
@requires_test_harness
@pytest.mark.asyncio
async def test_list_tasks_tool(harness, mock_get_tasks):
    """Test the list_tasks tool through the MCP protocol."""
    result = await harness.call_tool("list_tasks", {"status": "all"})
    
    assert "Test Task 1" in result
    assert "Test Task 2" in result
    assert "high" in result
    assert "completed" in result

@requires_test_harness
@pytest.mark.asyncio
async def test_add_task_tool(harness, mock_get_tasks, mock_save_tasks):
    """Test the add_task tool through the MCP protocol."""
    result = await harness.call_tool(
        "add_task", 
        {
            "title": "Harness Test Task",
            "description": "Testing through harness",
            "priority": "medium"
        }
    )
    
    assert "added successfully" in result
    assert mock_save_tasks.called
    
    # Verify the data was saved correctly
    saved_data = mock_save_tasks.call_args[0][0]
    added_task = [t for t in saved_data if t["title"] == "Harness Test Task"][0]
    assert added_task["description"] == "Testing through harness"
    assert added_task["priority"] == "medium"

@requires_test_harness
@pytest.mark.asyncio
async def test_weather_tool_mock(harness):
    """Test the weather tool with mocked data."""
    with patch('modules.knowledge_functions.httpx.AsyncClient') as mock_client:
        # Mock the httpx client response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = MagicMock(return_value={
            "location": "Test City",
            "temperature": "75°F",
            "condition": "Sunny",
            "humidity": "40%",
            "wind": "5 mph SW",
            "forecast": "Clear skies all day."
        })
        
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance
        
        # Call the tool through the harness
        result = await harness.call_tool("get_weather", {"location": "Test City"})
        
        # Verify results
        assert "Test City" in result
        assert "75°F" in result
        assert "Sunny" in result

# Run tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__]) 