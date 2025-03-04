from typing import List, Dict, Any, Optional
import os
import logging
import httpx
import json
import re

# Import the MCP server instance from the main file
from mcp_server import mcp, Context

logger = logging.getLogger("mcp-pa-agent.smarthome")

# Helper functions
async def get_home_assistant_client():
    """Get a client for Home Assistant if configured."""
    base_url = os.getenv("HOME_ASSISTANT_URL")
    token = os.getenv("HOME_ASSISTANT_TOKEN")
    
    if not base_url or not token:
        return None
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    return httpx.AsyncClient(base_url=base_url, headers=headers, timeout=10.0)

# Prompts
@mcp.prompt()
def create_scene_prompt(name: str) -> str:
    """Create a prompt for defining a smart home scene"""
    return f"Please help me create a smart home scene called '{name}'. What devices should be included and what states should they have? List specific devices and their desired settings."

@mcp.prompt()
def automation_prompt(trigger: str) -> str:
    """Create a prompt for defining a smart home automation"""
    return f"Please help me create a smart home automation with the trigger '{trigger}'. What actions should occur when this trigger happens?"

# Resources
@mcp.resource("smarthome://devices")
async def all_devices_resource() -> str:
    """Provide all smart home devices as a resource"""
    client = await get_home_assistant_client()
    if not client:
        return "Smart home integration is not available. Please configure HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN."
    
    try:
        # In a real implementation, you would make an actual API call
        # This is a demonstration response
        mock_devices = [
            {"entity_id": "light.living_room", "state": "on", "attributes": {"brightness": 255, "friendly_name": "Living Room Light"}},
            {"entity_id": "light.kitchen", "state": "off", "attributes": {"friendly_name": "Kitchen Light"}},
            {"entity_id": "switch.office_fan", "state": "on", "attributes": {"friendly_name": "Office Fan"}},
            {"entity_id": "climate.thermostat", "state": "heat", "attributes": {"temperature": 72, "friendly_name": "Thermostat"}}
        ]
        
        return json.dumps(mock_devices, indent=2)
    except Exception as e:
        logger.error(f"Error listing devices: {str(e)}")
        return f"Error listing devices: {str(e)}"
    finally:
        await client.aclose()

@mcp.resource("smarthome://device/{entity_id}")
async def device_resource(entity_id: str) -> str:
    """Provide details about a specific device"""
    client = await get_home_assistant_client()
    if not client:
        return "Smart home integration is not available. Please configure HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN."
    
    try:
        # Mock responses for different device types
        mock_states = {
            "light.living_room": {
                "state": "on", 
                "attributes": {
                    "brightness": 255, 
                    "friendly_name": "Living Room Light",
                    "color_temp": 300
                }
            },
            "climate.thermostat": {
                "state": "heat",
                "attributes": {
                    "temperature": 72,
                    "current_temperature": 70,
                    "hvac_modes": ["auto", "heat", "cool", "off"],
                    "friendly_name": "Thermostat"
                }
            }
        }
        
        if entity_id not in mock_states:
            return f"Device {entity_id} not found."
            
        return json.dumps(mock_states[entity_id], indent=2)
    except Exception as e:
        logger.error(f"Error getting device state: {str(e)}")
        return f"Error getting device state: {str(e)}"
    finally:
        await client.aclose()

# Tool functions
@mcp.tool()
async def list_devices(ctx: Context = None) -> str:
    """List all available smart home devices."""
    if ctx:
        ctx.info("Listing all smart home devices")
    
    client = await get_home_assistant_client()
    if not client:
        error_msg = "Smart home integration is not available. Please configure HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    try:
        if ctx:
            ctx.info("Fetching devices from Home Assistant")
            
        # In a real implementation, you would make an actual API call
        # This is a demonstration response
        mock_devices = [
            {"entity_id": "light.living_room", "state": "on", "attributes": {"brightness": 255, "friendly_name": "Living Room Light"}},
            {"entity_id": "light.kitchen", "state": "off", "attributes": {"friendly_name": "Kitchen Light"}},
            {"entity_id": "switch.office_fan", "state": "on", "attributes": {"friendly_name": "Office Fan"}},
            {"entity_id": "climate.thermostat", "state": "heat", "attributes": {"temperature": 72, "friendly_name": "Thermostat"}}
        ]
        
        if not mock_devices:
            return "No smart home devices found."
        
        formatted_devices = []
        for i, device in enumerate(mock_devices):
            if ctx:
                await ctx.report_progress(i, len(mock_devices))
                
            attributes = device.get("attributes", {})
            friendly_name = attributes.get("friendly_name", device.get("entity_id", "Unknown"))
            
            device_info = f"Device: {friendly_name}\nID: {device.get('entity_id', 'Unknown')}\nState: {device.get('state', 'Unknown')}"
            
            # Add additional attributes based on device type
            if "brightness" in attributes:
                device_info += f"\nBrightness: {attributes['brightness']}"
            if "temperature" in attributes:
                device_info += f"\nTemperature: {attributes['temperature']}°F"
                
            formatted_devices.append(device_info)
            
        return "\n---\n".join(formatted_devices)
            
    except Exception as e:
        error_msg = f"Error listing devices: {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return error_msg
    finally:
        await client.aclose()

@mcp.tool()
async def control_device(entity_id: str, action: str, value: Optional[int] = None, ctx: Context = None) -> str:
    """Control a smart home device.
    
    Args:
        entity_id: The entity ID of the device to control
        action: The action to perform (on, off, set_temperature, brightness, etc.)
        value: Optional value for the action (e.g., brightness level, temperature)
    """
    if ctx:
        if value is not None:
            ctx.info(f"Controlling device {entity_id}: {action} = {value}")
        else:
            ctx.info(f"Controlling device {entity_id}: {action}")
    
    if not entity_id or len(entity_id.strip()) == 0:
        error_msg = "Entity ID cannot be empty."
        if ctx:
            ctx.error(error_msg)
        return error_msg
        
    if not action or len(action.strip()) == 0:
        error_msg = "Action cannot be empty."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    # Validate entity_id format
    entity_pattern = re.compile(r'^[a-z0-9_]+\.[a-z0-9_]+$')
    if not entity_pattern.match(entity_id):
        error_msg = f"Invalid entity ID format: {entity_id}. Expected format: domain.entity (e.g., light.living_room)"
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    client = await get_home_assistant_client()
    if not client:
        error_msg = "Smart home integration is not available. Please configure HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    try:
        # Validate action based on entity type
        valid_actions = {
            "light": ["on", "off", "brightness"],
            "switch": ["on", "off"],
            "climate": ["set_temperature", "set_mode"]
        }
        
        entity_type = entity_id.split(".")[0] if "." in entity_id else None
        
        if not entity_type:
            error_msg = f"Invalid entity ID: {entity_id}. Missing domain prefix."
            if ctx:
                ctx.error(error_msg)
            return error_msg
            
        if entity_type not in valid_actions:
            error_msg = f"Unsupported entity type: {entity_type}. Supported types are: {', '.join(valid_actions.keys())}"
            if ctx:
                ctx.error(error_msg)
            return error_msg
        
        if action.lower() not in valid_actions[entity_type] and action.lower() not in ["on", "off"]:
            error_msg = f"Invalid action for {entity_type}: {action}. Supported actions are: {', '.join(valid_actions[entity_type])}"
            if ctx:
                ctx.error(error_msg)
            return error_msg
        
        # In a real implementation, you would make an actual API call
        # This is a demonstration response
        
        # Build response based on action
        if ctx:
            ctx.info(f"Sending {action} command to {entity_id}")
            
        if action.lower() in ["on", "off"]:
            service = f"{entity_type}.turn_{action.lower()}"
            return f"Successfully turned {action.lower()} {entity_id}"
        elif action.lower() == "brightness" and entity_type == "light":
            if value is None or not (0 <= value <= 255):
                error_msg = "Brightness value must be between 0 and 255."
                if ctx:
                    ctx.error(error_msg)
                return error_msg
            return f"Successfully set brightness of {entity_id} to {value}"
        elif action.lower() == "set_temperature" and entity_type == "climate":
            if value is None:
                error_msg = "Temperature value is required."
                if ctx:
                    ctx.error(error_msg)
                return error_msg
            return f"Successfully set temperature of {entity_id} to {value}°F"
        elif action.lower() == "set_mode" and entity_type == "climate":
            if not value and isinstance(value, str):
                error_msg = "Mode value is required."
                if ctx:
                    ctx.error(error_msg)
                return error_msg
            return f"Successfully set mode of {entity_id} to {value}"
        else:
            error_msg = f"Action {action} not implemented for {entity_type}"
            if ctx:
                ctx.error(error_msg)
            return error_msg
            
    except Exception as e:
        error_msg = f"Error controlling device: {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return error_msg
    finally:
        await client.aclose()

@mcp.tool()
async def get_device_state(entity_id: str, ctx: Context = None) -> str:
    """Get the current state of a smart home device.
    
    Args:
        entity_id: The entity ID of the device
    """
    if ctx:
        ctx.info(f"Getting state of device: {entity_id}")
    
    if not entity_id or len(entity_id.strip()) == 0:
        error_msg = "Entity ID cannot be empty."
        if ctx:
            ctx.error(error_msg)
        return error_msg
        
    # Validate entity_id format
    entity_pattern = re.compile(r'^[a-z0-9_]+\.[a-z0-9_]+$')
    if not entity_pattern.match(entity_id):
        error_msg = f"Invalid entity ID format: {entity_id}. Expected format: domain.entity (e.g., light.living_room)"
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    client = await get_home_assistant_client()
    if not client:
        error_msg = "Smart home integration is not available. Please configure HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    try:
        if ctx:
            ctx.info(f"Fetching state for {entity_id}")
            
        # In a real implementation, you would make an actual API call
        # This is a demonstration response
        
        # Mock responses for different device types
        mock_states = {
            "light.living_room": {
                "state": "on", 
                "attributes": {
                    "brightness": 255, 
                    "friendly_name": "Living Room Light",
                    "color_temp": 300
                }
            },
            "light.kitchen": {
                "state": "off", 
                "attributes": {
                    "friendly_name": "Kitchen Light"
                }
            },
            "switch.office_fan": {
                "state": "on", 
                "attributes": {
                    "friendly_name": "Office Fan"
                }
            },
            "climate.thermostat": {
                "state": "heat",
                "attributes": {
                    "temperature": 72,
                    "current_temperature": 70,
                    "hvac_modes": ["auto", "heat", "cool", "off"],
                    "friendly_name": "Thermostat"
                }
            }
        }
        
        if entity_id not in mock_states:
            error_msg = f"Device {entity_id} not found."
            if ctx:
                ctx.error(error_msg)
            return error_msg
        
        device = mock_states[entity_id]
        attributes = device.get("attributes", {})
        friendly_name = attributes.get("friendly_name", entity_id)
        
        state_info = f"Device: {friendly_name}\nID: {entity_id}\nState: {device.get('state', 'Unknown')}"
        
        # Add specific attributes based on entity type
        entity_type = entity_id.split(".")[0] if "." in entity_id else ""
        
        if entity_type == "light":
            if "brightness" in attributes:
                state_info += f"\nBrightness: {attributes['brightness']}"
            if "color_temp" in attributes:
                state_info += f"\nColor Temperature: {attributes['color_temp']}K"
                
        elif entity_type == "climate":
            if "temperature" in attributes:
                state_info += f"\nSet Temperature: {attributes['temperature']}°F"
            if "current_temperature" in attributes:
                state_info += f"\nCurrent Temperature: {attributes['current_temperature']}°F"
            if "hvac_modes" in attributes:
                state_info += f"\nAvailable Modes: {', '.join(attributes['hvac_modes'])}"
                
        return state_info
            
    except Exception as e:
        error_msg = f"Error getting device state: {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return error_msg
    finally:
        await client.aclose()

@mcp.tool()
async def create_scene(name: str, device_states: Dict[str, Any], ctx: Context = None) -> str:
    """Create a new scene with defined device states.
    
    Args:
        name: Name for the scene
        device_states: Dictionary of device entity_ids and their target states
    """
    if ctx:
        ctx.info(f"Creating scene: {name}")
    
    if not name or len(name.strip()) == 0:
        error_msg = "Scene name cannot be empty."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    if not device_states or not isinstance(device_states, dict) or len(device_states) == 0:
        error_msg = "Device states must be a non-empty dictionary."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    client = await get_home_assistant_client()
    if not client:
        error_msg = "Smart home integration is not available. Please configure HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    try:
        if ctx:
            ctx.info(f"Creating scene with {len(device_states)} device states")
            
        # In a real implementation, you would make an actual API call
        # This is a demonstration response
        scene_entities = []
        for entity_id, state in device_states.items():
            if isinstance(state, dict):
                scene_entities.append(f"{entity_id}: {json.dumps(state)}")
            else:
                scene_entities.append(f"{entity_id}: {state}")
        
        return f"Scene '{name}' created successfully with the following device states:\n\n" + "\n".join(scene_entities)
            
    except Exception as e:
        error_msg = f"Error creating scene: {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return error_msg
    finally:
        await client.aclose() 