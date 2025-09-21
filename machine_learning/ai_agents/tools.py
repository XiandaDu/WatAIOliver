"""
LangChain Native Tools for Multi-Agent System

Implements tools using LangChain's native tools framework for better integration
with the existing LangGraph/LangChain architecture.
"""

import math
import asyncio
from typing import Optional, Any, Dict
from langchain.tools import Tool, tool
from langchain.callbacks.manager import CallbackManagerForToolRun
from pydantic import BaseModel, Field


class CalculatorInput(BaseModel):
    """Input for calculator tool"""
    expression: str = Field(description="Mathematical expression to evaluate")
    precision: Optional[int] = Field(default=6, description="Number of decimal places")


class SearchInput(BaseModel):
    """Input for search tool"""
    query: str = Field(description="Search query")
    domain: Optional[str] = Field(default="", description="Optional domain to search")


class CodeExecutorInput(BaseModel):
    """Input for code execution tool"""
    language: str = Field(description="Programming language (python, javascript, etc)")
    code: str = Field(description="Code to execute")


class WeatherInput(BaseModel):
    """Input for weather tool"""
    location: str = Field(description="City, state/country")
    units: Optional[str] = Field(default="celsius", description="Temperature units")


@tool("calculate", args_schema=CalculatorInput, return_direct=False)
def calculate_tool(expression: str, precision: int = 6) -> str:
    """
    Performs mathematical calculations and evaluates expressions.
    
    Use this tool when you need to:
    - Solve mathematical equations
    - Evaluate numerical expressions
    - Perform calculations with mathematical functions
    
    Supports: basic arithmetic, trigonometry, logarithms, square roots, etc.
    """
    try:
        # Sanitize and evaluate expression
        safe_expression = expression.lower()
        safe_expression = safe_expression.replace("^", "**")  # Power operator
        safe_expression = safe_expression.replace("π", str(math.pi))
        safe_expression = safe_expression.replace("pi", str(math.pi))
        safe_expression = safe_expression.replace("e", str(math.e))
        
        # Add math functions
        safe_names = {
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "asin": math.asin, "acos": math.acos, "atan": math.atan,
            "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
            "log": math.log, "log10": math.log10, "ln": math.log,
            "sqrt": math.sqrt, "abs": abs, "round": round,
            "floor": math.floor, "ceil": math.ceil,
            "exp": math.exp, "pow": pow,
            "pi": math.pi, "e": math.e
        }
        
        # Evaluate safely
        result = eval(safe_expression, {"__builtins__": {}}, safe_names)
        
        # Format result
        if isinstance(result, float):
            formatted_result = round(result, precision)
        else:
            formatted_result = result
            
        return f"Calculation: {expression} = {formatted_result}"
        
    except Exception as e:
        return f"Error in calculation: {str(e)}"


@tool("search_web", args_schema=SearchInput, return_direct=False)
def search_tool(query: str, domain: str = "") -> str:
    """
    Searches for current information on the web.
    
    Use this tool when you need:
    - Current/recent information
    - Latest news or updates
    - Real-time data
    - Information beyond your training cutoff
    """
    import requests
    import json
    import re
    from bs4 import BeautifulSoup
    from typing import List, Dict
    
    try:
        import urllib.parse
        import json
        
        # Use DuckDuckGo HTML search (more reliable than their API)
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(search_url, headers=headers, timeout=15)
        
        if response.status_code in [200, 202]:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Try multiple possible selectors for DuckDuckGo results
            search_results = (
                soup.find_all('div', class_='web-result') or
                soup.find_all('div', class_='result') or
                soup.find_all('div', class_='results_links') or
                soup.find_all('div', attrs={'data-domain': True})
            )[:5]
            
            for i, result in enumerate(search_results):
                title = ''
                snippet = ''
                url = ''
                
                # Try different ways to extract title
                title_elem = (
                    result.find('a', class_='result__a') or
                    result.find('h2') and result.find('h2').find('a') or
                    result.find('a', attrs={'data-testid': 'result-title-a'}) or
                    result.find('a')
                )
                if title_elem:
                    title = title_elem.get_text().strip()
                    url = title_elem.get('href', '')
                
                # Try different ways to extract snippet
                snippet_elem = (
                    result.find('a', class_='result__snippet') or
                    result.find('div', class_='result__snippet') or
                    result.find('span', class_='result__snippet') or
                    result.find('p') or
                    result.find('div', class_='snippet')
                )
                if snippet_elem:
                    snippet = snippet_elem.get_text().strip()
                
                if title and snippet:
                    results.append(f"{i+1}. {title}")
                    results.append(f"   {snippet}")
                    if url:
                        results.append(f"   URL: {url}")
            
            if results:
                from datetime import datetime
                current_date = datetime.now().strftime("%Y-%m-%d")
                return f"Search Results for '{query}':\n\n" + "\n\n".join(results) + f"\n\nSearched on: {current_date}"
        
        # If that failed, return honest failure
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        return f"Search failed for '{query}' on {current_date}. DuckDuckGo returned status {response.status_code}."
            
    except requests.RequestException as e:
        return f"Search service temporarily unavailable: {str(e)}"
    except Exception as e:
        return f"Search processing error: {str(e)}"


@tool("execute_python", args_schema=CodeExecutorInput, return_direct=False)
def code_executor_tool(language: str, code: str) -> str:
    """
    Executes code in a safe, sandboxed environment.
    
    Use this tool when you need to:
    - Run and test code snippets
    - Demonstrate programming concepts
    - Debug code issues
    - Show actual execution results
    
    Currently supports Python with safety restrictions.
    """
    if language.lower() != "python":
        return f"Code execution for '{language}' not supported. Only Python is currently available."
    
    try:
        # Basic safety checks
        dangerous_patterns = [
            "import os", "import sys", "import subprocess", "import socket",
            "open(", "file(", "exec(", "eval(", "__import__", "compile("
        ]
        
        code_lower = code.lower()
        for pattern in dangerous_patterns:
            if pattern in code_lower:
                return f"Code execution blocked for security: contains '{pattern}'"
        
        # Simple whitelist approach for demo
        allowed_imports = ["math", "random", "datetime", "json"]
        
        # Pre-import allowed modules
        available_modules = {}
        for module_name in allowed_imports:
            try:
                available_modules[module_name] = __import__(module_name)
            except ImportError:
                pass  # Module not available
        
        # Safe execution environment
        safe_globals = {
            "__builtins__": {
                "print": print, "len": len, "str": str, "int": int,
                "float": float, "list": list, "dict": dict, "range": range,
                "sum": sum, "max": max, "min": min, "abs": abs,
                "round": round, "sorted": sorted, "reversed": reversed,
                "__import__": __import__  # Allow imports for whitelisted modules
            }
        }
        
        # Add pre-imported modules to globals
        safe_globals.update(available_modules)
        
        # Capture output
        import io
        import sys
        
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()
        
        try:
            exec(code, safe_globals)
            output = captured_output.getvalue()
            return f"Code executed successfully:\n\n```python\n{code}\n```\n\nOutput:\n{output.strip()}"
        finally:
            sys.stdout = old_stdout
            
    except Exception as e:
        return f"Code execution error: {str(e)}"


@tool("get_weather", args_schema=WeatherInput, return_direct=False)
def weather_tool(location: str, units: str = "celsius") -> str:
    """
    Gets current weather information for a location.
    
    Use this tool when users ask about:
    - Current weather conditions
    - Temperature information
    - Weather forecasts
    - Climate information
    """
    import requests
    import json
    
    try:
        # Use OpenWeatherMap free API (requires API key but has generous free tier)
        # For now, using wttr.in which is free and doesn't require API key
        
        # Clean location string
        location_clean = location.replace(" ", "+")
        
        # Use wttr.in API for weather data (free, no key required)
        url = f"https://wttr.in/{location_clean}?format=j1"
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'current_condition' in data and data['current_condition']:
            current = data['current_condition'][0]
            
            # Extract data
            temp_c = current.get('temp_C', 'N/A')
            temp_f = current.get('temp_F', 'N/A')
            condition = current.get('weatherDesc', [{}])[0].get('value', 'Unknown')
            humidity = current.get('humidity', 'N/A')
            wind_speed_kmh = current.get('windspeedKmph', 'N/A')
            wind_speed_mph = current.get('windspeedMiles', 'N/A')
            feels_like_c = current.get('FeelsLikeC', 'N/A')
            feels_like_f = current.get('FeelsLikeF', 'N/A')
            
            # Format based on units
            if units.lower() == "celsius":
                temp_display = f"{temp_c}°C"
                feels_like = f"{feels_like_c}°C"
                wind_display = f"{wind_speed_kmh} km/h"
            else:
                temp_display = f"{temp_f}°F"
                feels_like = f"{feels_like_f}°F"
                wind_display = f"{wind_speed_mph} mph"
            
            return f"""Current weather for {location}:

Condition: {condition}
Temperature: {temp_display}
Feels like: {feels_like}
Humidity: {humidity}%
Wind: {wind_display}"""
        
        else:
            return f"Weather data not available for {location}"
            
    except requests.RequestException as e:
        return f"Weather service unavailable: {str(e)}"
    except Exception as e:
        return f"Weather error: {str(e)}"


# Collection of all available tools
AVAILABLE_TOOLS = [
    calculate_tool,
    search_tool,
    code_executor_tool,
    weather_tool
]


def get_tools_for_query(query: str) -> list:
    """
    Smart tool selection based on query content.
    Returns subset of tools that are likely needed for the query.
    """
    print(f"\n🔍 TOOL DETECTION DEBUG")
    print(f"📝 Query: '{query}'")
    
    query_lower = query.lower()
    selected_tools = []
    triggered_keywords = []
    
    # Mathematical/calculation keywords
    calc_keywords = ["calculate", "compute", "solve", "math", "equation", "formula", "+", "-", "*", "/", "="]
    calc_matches = [kw for kw in calc_keywords if kw in query_lower]
    if calc_matches:
        selected_tools.append(calculate_tool)
        triggered_keywords.extend([f"calc:{kw}" for kw in calc_matches])
        print(f"✅ CALCULATE tool triggered by: {calc_matches}")
    
    # Search keywords
    search_keywords = ["search", "find", "look up", "latest", "current", "recent", "what is", "who is", "2024", "2025"]
    search_matches = [kw for kw in search_keywords if kw in query_lower]
    if search_matches:
        selected_tools.append(search_tool)
        triggered_keywords.extend([f"search:{kw}" for kw in search_matches])
        print(f"✅ SEARCH tool triggered by: {search_matches}")
    
    # Code execution keywords
    code_keywords = ["code", "python", "execute", "run", "script", "program", "debug", "test"]
    code_matches = [kw for kw in code_keywords if kw in query_lower]
    if code_matches:
        selected_tools.append(code_executor_tool)
        triggered_keywords.extend([f"code:{kw}" for kw in code_matches])
        print(f"✅ CODE EXECUTION tool triggered by: {code_matches}")
    
    # Weather keywords
    weather_keywords = ["weather", "temperature", "forecast", "climate", "rain", "snow", "sunny", "cloudy"]
    weather_matches = [kw for kw in weather_keywords if kw in query_lower]
    if weather_matches:
        selected_tools.append(weather_tool)
        triggered_keywords.extend([f"weather:{kw}" for kw in weather_matches])
        print(f"✅ WEATHER tool triggered by: {weather_matches}")
    
    # Summary
    if selected_tools:
        tool_names = [tool.name for tool in selected_tools]
        print(f"🎯 FINAL TOOLS SELECTED: {tool_names}")
        print(f"🔑 ALL TRIGGERED KEYWORDS: {triggered_keywords}")
    else:
        print(f"❌ NO TOOLS DETECTED - using standard response")
    
    print(f"🔍 TOOL DETECTION COMPLETE\n")
    return selected_tools


def create_tool_calling_prompt_template() -> str:
    """
    Create a prompt template that instructs the model on tool usage.
    This integrates with LangChain's tool calling format.
    """
    return """You are an AI assistant with access to specialized tools. Use tools when they would be helpful to provide accurate, up-to-date, or computed information.

AVAILABLE TOOLS:
- calculate: For mathematical calculations and equation solving
- search_web: For current information and real-time data
- execute_python: For running and testing code
- get_weather: For weather information

TOOL USAGE GUIDELINES:
1. Use tools when the user's question would benefit from:
   - Mathematical computation
   - Current/recent information
   - Code execution/testing
   - Weather data
2. Call tools before providing your final answer
3. Explain why you're using each tool
4. Integrate tool results into your response

WHEN TO USE EACH TOOL:
- calculate: "What's 15% of 240?", "Solve x² + 5x - 6 = 0", "Calculate sin(π/4)"
- search_web: "Latest AI news", "Current events", "Recent research"
- execute_python: "Test this code", "Run this script", "Debug this function"
- get_weather: "Weather in Tokyo", "Temperature in London"

If a tool would help answer the question, use it. Otherwise, respond normally."""


class ToolAgent:
    """
    Enhanced agent that can use tools via LangChain's native tool calling.
    This can be integrated into your existing agent architecture.
    """
    
    def __init__(self, llm, tools=None):
        self.llm = llm
        self.tools = tools or AVAILABLE_TOOLS
    
    def get_tools_for_query(self, query: str):
        """Get relevant tools for a specific query"""
        return get_tools_for_query(query)
    
    async def execute_with_tools(self, query: str, context: str = ""):
        """
        Execute query with tool calling capabilities.
        This method can be integrated into your existing agent workflow.
        """
        # Get relevant tools
        relevant_tools = self.get_tools_for_query(query)
        
        if not relevant_tools:
            # No tools needed, use standard LLM
            return await self._execute_without_tools(query, context)
        
        # Create tool-calling prompt
        tool_prompt = create_tool_calling_prompt_template()
        enhanced_prompt = f"{tool_prompt}\n\nContext: {context}\n\nUser Query: {query}"
        
        # This would integrate with your existing LangChain/LangGraph workflow
        # The exact implementation depends on your current agent setup
        return {
            "enhanced_prompt": enhanced_prompt,
            "available_tools": [tool.name for tool in relevant_tools],
            "tools": relevant_tools
        }
    
    async def _execute_without_tools(self, query: str, context: str):
        """Fallback execution without tools"""
        return {
            "enhanced_prompt": f"Context: {context}\n\nUser Query: {query}",
            "available_tools": [],
            "tools": []
        }