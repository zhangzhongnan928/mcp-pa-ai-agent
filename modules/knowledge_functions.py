from typing import List, Dict, Any, Optional
import os
import logging
import httpx
import json
import io
from urllib.parse import quote_plus
import matplotlib.pyplot as plt
import numpy as np

# Import the MCP server instance from the main file
from mcp_server import mcp, Context
from mcp.server.fastmcp import Image

logger = logging.getLogger("mcp-pa-agent.knowledge")

# Resources
@mcp.resource("search://{query}")
async def search_resource(query: str) -> str:
    """Provide search results as a resource"""
    try:
        api_key = os.getenv("DUCKDUCKGO_API_KEY")
        if not api_key:
            return "Web search is not available. Please set the DUCKDUCKGO_API_KEY environment variable."
        
        url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&key={api_key}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            
            # This is simplified as the actual DuckDuckGo API response would be different
            search_results = response.json()
            
            if not search_results or "results" not in search_results:
                return "No search results found."
            
            results = search_results["results"][:5]
            return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Error performing search: {str(e)}")
        return f"Error performing search: {str(e)}"

# Prompts
@mcp.prompt()
def analyze_news_prompt(topic: str) -> str:
    """Create a prompt for news analysis"""
    return f"Please analyze the latest news about '{topic}' and provide a short summary of the key developments and their potential implications."

# Tool functions
@mcp.tool()
async def web_search(query: str, num_results: int = 5, ctx: Context = None) -> str:
    """Search the web for information.
    
    Args:
        query: The search query
        num_results: Number of results to return (default 5)
    """
    if not query or len(query.strip()) == 0:
        error_msg = "Error: Search query cannot be empty."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    if ctx:
        ctx.info(f"Searching for: {query}")
    
    api_key = os.getenv("DUCKDUCKGO_API_KEY")
    if not api_key:
        error_msg = "Web search is not available. Please set the DUCKDUCKGO_API_KEY environment variable."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    try:
        # Log progress
        if ctx:
            ctx.info("Connecting to search API...")
        
        # This is a demonstration URL - DuckDuckGo doesn't actually have this API structure
        url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&key={api_key}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            
            # This is simplified as the actual DuckDuckGo API response would be different
            search_results = response.json()
            
            if not search_results or "results" not in search_results:
                return "No search results found."
            
            results = search_results["results"][:num_results]
            
            formatted_results = []
            for i, result in enumerate(results):
                if ctx:
                    await ctx.report_progress(i, len(results))
                formatted_results.append(f"""
Title: {result.get('title', 'No title')}
URL: {result.get('url', 'No URL')}
Description: {result.get('description', 'No description')}
""")
            
            return "\n---\n".join(formatted_results)
    
    except httpx.TimeoutException:
        error_msg = "Search request timed out. Please try again later."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    except httpx.HTTPStatusError as e:
        error_msg = f"Search API error: HTTP {e.response.status_code}"
        if ctx:
            ctx.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error performing web search: {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return error_msg

@mcp.tool()
async def get_weather(location: str, ctx: Context = None) -> str:
    """Get current weather information for a location.
    
    Args:
        location: The location to get weather for (city name or coordinates)
    """
    if not location or len(location.strip()) == 0:
        error_msg = "Error: Location cannot be empty."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    if ctx:
        ctx.info(f"Getting weather for: {location}")
    
    try:
        # Mock API call
        api_key = os.getenv("WEATHER_API_KEY")
        if not api_key:
            # If no API key, return mock data but with a warning
            if ctx:
                ctx.warning("Using mock weather data - set WEATHER_API_KEY for real data")
            
            # Create mock data based on the location
            mock_response = {
                "location": location,
                "temperature": "72°F",
                "condition": "Partly Cloudy",
                "humidity": "45%",
                "wind": "5 mph NW",
                "forecast": "Clear skies with occasional clouds. Low chance of precipitation."
            }
            
            return f"""
Weather for {mock_response['location']}:
Temperature: {mock_response['temperature']}
Condition: {mock_response['condition']}
Humidity: {mock_response['humidity']}
Wind: {mock_response['wind']}
Forecast: {mock_response['forecast']}

Note: This is simulated weather data. Set the WEATHER_API_KEY environment variable for real data.
"""
        
        # With a real API key, we would make a real request
        url = f"https://api.example-weather-service.com/current?location={quote_plus(location)}&key={api_key}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            
            # Process the actual response here
            weather_data = response.json()
            
            return f"""
Weather for {weather_data['location']}:
Temperature: {weather_data['temperature']}
Condition: {weather_data['condition']}
Humidity: {weather_data['humidity']}
Wind: {weather_data['wind']}
Forecast: {weather_data['forecast']}
"""
    
    except httpx.TimeoutException:
        error_msg = "Weather request timed out. Please try again later."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    except httpx.HTTPStatusError as e:
        error_msg = f"Weather API error: HTTP {e.response.status_code}"
        if ctx:
            ctx.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error getting weather information: {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return error_msg

@mcp.tool()
async def get_news(topic: str = "", num_results: int = 5, ctx: Context = None) -> str:
    """Get latest news, optionally filtered by topic.
    
    Args:
        topic: Topic to filter news by (optional)
        num_results: Number of news items to return (default 5)
    """
    if ctx:
        if topic:
            ctx.info(f"Getting news about: {topic}")
        else:
            ctx.info("Getting latest news")
    
    try:
        api_key = os.getenv("NEWS_API_KEY")
        if not api_key:
            # If no API key, return mock data but with a warning
            if ctx:
                ctx.warning("Using mock news data - set NEWS_API_KEY for real data")
            
            # Create mock news
            mock_news = [
                {
                    "title": f"Example News Headline About {topic if topic else 'Current Events'} 1",
                    "source": "Example News",
                    "description": f"This is a sample news description about {topic if topic else 'current events'} for demonstration purposes.",
                    "url": "https://example-news.com/article1",
                    "published_at": "2023-07-01T12:00:00Z"
                },
                {
                    "title": f"Example News Headline About {topic if topic else 'Current Events'} 2",
                    "source": "Sample News Network",
                    "description": f"Another mock news article description about {topic if topic else 'current events'}.",
                    "url": "https://sample-news.com/article2",
                    "published_at": "2023-07-01T11:30:00Z"
                }
            ]
            
            if not mock_news:
                return f"No news found{' for topic: ' + topic if topic else ''}."
            
            formatted_news = []
            for news in mock_news[:num_results]:
                formatted_news.append(f"""
Title: {news.get('title', 'No title')}
Source: {news.get('source', 'Unknown source')}
Published: {news.get('published_at', 'Unknown date')}
Description: {news.get('description', 'No description')}
URL: {news.get('url', 'No URL')}
""")
            
            result = "\n---\n".join(formatted_news)
            result += "\n\nNote: This is simulated news data. Set the NEWS_API_KEY environment variable for real data."
            return result
        
        # With a real API key
        url_path = f"top-headlines?apiKey={api_key}"
        if topic:
            url_path += f"&q={quote_plus(topic)}"
            
        url = f"https://newsapi.org/v2/{url_path}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            
            # Process the actual response here
            news_data = response.json()
            
            if not news_data or "articles" not in news_data or not news_data["articles"]:
                return f"No news found{' for topic: ' + topic if topic else ''}."
            
            formatted_news = []
            for article in news_data["articles"][:num_results]:
                formatted_news.append(f"""
Title: {article.get('title', 'No title')}
Source: {article.get('source', {}).get('name', 'Unknown source')}
Published: {article.get('publishedAt', 'Unknown date')}
Description: {article.get('description', 'No description')}
URL: {article.get('url', 'No URL')}
""")
            
            return "\n---\n".join(formatted_news)
    
    except httpx.TimeoutException:
        error_msg = "News request timed out. Please try again later."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    except httpx.HTTPStatusError as e:
        error_msg = f"News API error: HTTP {e.response.status_code}"
        if ctx:
            ctx.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error getting news information: {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return error_msg

@mcp.tool()
async def create_chart(data_points: str, chart_type: str = "bar", title: str = "Chart", ctx: Context = None) -> Image:
    """Create a chart from data points.
    
    Args:
        data_points: Comma-separated numbers or JSON array of numbers
        chart_type: Type of chart ('bar', 'line', 'pie', 'scatter')
        title: Title for the chart
    """
    if ctx:
        ctx.info(f"Creating {chart_type} chart with title: {title}")
    
    # Parse data
    try:
        if data_points.startswith('[') and data_points.endswith(']'):
            import json
            data = json.loads(data_points)
        else:
            data = [float(x.strip()) for x in data_points.split(',')]
            
        if not data:
            error_msg = "Error: No valid data points provided."
            if ctx:
                ctx.error(error_msg)
            return error_msg
    except json.JSONDecodeError:
        error_msg = "Error: Invalid JSON format. Use format [1,2,3] or comma-separated values."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    except ValueError:
        error_msg = "Error: Invalid number format. Ensure all values are numbers."
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    # Check chart type
    valid_chart_types = ['bar', 'line', 'pie', 'scatter']
    if chart_type.lower() not in valid_chart_types:
        error_msg = f"Error: Invalid chart type. Use one of: {', '.join(valid_chart_types)}"
        if ctx:
            ctx.error(error_msg)
        return error_msg
    
    # Create chart
    try:
        plt.figure(figsize=(10, 6))
        
        chart_type = chart_type.lower()
        if chart_type == 'bar':
            plt.bar(range(len(data)), data)
            plt.xticks(range(len(data)), [f"Item {i+1}" for i in range(len(data))])
        elif chart_type == 'line':
            plt.plot(data, marker='o')
            plt.xticks(range(len(data)), [f"Point {i+1}" for i in range(len(data))])
        elif chart_type == 'pie':
            if all(x >= 0 for x in data):
                plt.pie(data, autopct='%1.1f%%', labels=[f"Slice {i+1}" for i in range(len(data))])
            else:
                error_msg = "Error: Pie charts require non-negative values."
                if ctx:
                    ctx.error(error_msg)
                return error_msg
        elif chart_type == 'scatter':
            # For scatter, we either need pairs or we can just plot against index
            if len(data) % 2 == 0:  # If even number, try to use pairs
                x = data[0::2]
                y = data[1::2]
                plt.scatter(x, y)
            else:
                plt.scatter(range(len(data)), data)
        
        plt.title(title)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Save to bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        
        # Convert to MCP Image
        return Image(data=buf.getvalue(), format="png")
        
    except Exception as e:
        error_msg = f"Error creating chart: {str(e)}"
        if ctx:
            ctx.error(error_msg)
        return error_msg 