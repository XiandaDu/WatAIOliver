"""
Simple Tool Integration for Daily Mode Only

This handles tool calling in the simple Daily mode flow:
User Input → RAG → Enhanced Prompt → LLM → Tool Parsing → Final Response
"""

import re
import sys
import os
import logging
from typing import Dict, List, Any, Optional

# Setup logging
try:
    from ..logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Add machine learning path for tool imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
ML_PATH = os.path.join(PROJECT_ROOT, "machine_learning")
if ML_PATH not in sys.path:
    sys.path.append(ML_PATH)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


def detect_tools_for_daily_mode(prompt: str) -> List[str]:
    """
    Simple tool detection for Daily mode
    Returns list of tool names that should be available
    """
    # Create AI agents logger for tool usage tracking
    tools_logger = logging.getLogger("ai_agents.tools")
    tools_logger.info(f"🔍 DAILY MODE TOOL DETECTION - Analyzing prompt: '{prompt[:100]}{'...' if len(prompt) > 100 else ''}'")
    
    print(f"\n🔍 DAILY MODE TOOL DETECTION")
    print(f"📝 Analyzing prompt: '{prompt[:100]}{'...' if len(prompt) > 100 else ''}'")
    
    prompt_lower = prompt.lower()
    detected_tools = []
    
    # Mathematical/calculation keywords
    calc_keywords = ["calculate", "compute", "solve", "math", "equation", "formula", "+", "-", "*", "/", "=", "derivative", "integral"]
    calc_matches = [kw for kw in calc_keywords if kw in prompt_lower]
    if calc_matches:
        detected_tools.append("calculate")
        print(f"✅ CALCULATE tool detected by: {calc_matches}")
        tools_logger.info(f"✅ CALCULATE tool detected by keywords: {calc_matches}")
    
    # Code execution keywords
    code_keywords = ["code", "python", "execute", "run", "script", "program", "debug"]
    code_matches = [kw for kw in code_keywords if kw in prompt_lower]
    if code_matches:
        detected_tools.append("execute_python")
        print(f"✅ EXECUTE_PYTHON tool detected by: {code_matches}")
        tools_logger.info(f"✅ EXECUTE_PYTHON tool detected by keywords: {code_matches}")
    
    # Search keywords
    search_keywords = ["search", "find", "look up", "latest", "current", "recent", "what is", "who is", "2024", "2025"]
    search_matches = [kw for kw in search_keywords if kw in prompt_lower]
    if search_matches:
        detected_tools.append("search_web")
        print(f"✅ SEARCH_WEB tool detected by: {search_matches}")
        tools_logger.info(f"✅ SEARCH_WEB tool detected by keywords: {search_matches}")
    
    # Weather keywords
    weather_keywords = ["weather", "temperature", "forecast", "climate", "rain", "snow", "sunny", "cloudy"]
    weather_matches = [kw for kw in weather_keywords if kw in prompt_lower]
    if weather_matches:
        detected_tools.append("get_weather")
        print(f"✅ GET_WEATHER tool detected by: {weather_matches}")
        tools_logger.info(f"✅ GET_WEATHER tool detected by keywords: {weather_matches}")
    
    if detected_tools:
        print(f"🎯 FINAL TOOLS FOR DAILY MODE: {detected_tools}")
        tools_logger.info(f"🎯 FINAL TOOLS DETECTED: {detected_tools}")
    else:
        print(f"❌ NO TOOLS NEEDED - standard response")
        tools_logger.info("❌ NO TOOLS NEEDED - standard response")
    
    print(f"🔍 TOOL DETECTION COMPLETE\n")
    return detected_tools


def enhance_daily_prompt_with_tools(original_prompt: str, rag_context: str) -> str:
    """
    Enhance Daily mode prompt with tool instructions if tools are detected
    """
    detected_tools = detect_tools_for_daily_mode(original_prompt)
    
    if not detected_tools:
        return rag_context  # No tools needed, return original
    
    print(f"🔧 ENHANCING DAILY PROMPT WITH TOOLS")
    print(f"🛠️ Adding tool instructions for: {detected_tools}")
    
    # Create tool instructions
    tool_instructions = f"""

🛠️ **EDUCATIONAL TOOLS AVAILABLE:**

You have access to these tools to help provide better educational responses:

"""
    
    if "calculate" in detected_tools:
        tool_instructions += """
📊 **CALCULATE TOOL**: For math problems, equations, calculus
   Format: [TOOL: calculate(expression="your math expression")]
   Example: [TOOL: calculate(expression="derivative of x^2 + 3x")]

"""
    
    if "execute_python" in detected_tools:
        tool_instructions += """
🐍 **PYTHON CODE TOOL**: For running and testing code
   Format: [TOOL: execute_python(code="your python code")]
   Example: [TOOL: execute_python(code="for i in range(3): print(i)")]

"""
    
    if "search_web" in detected_tools:
        tool_instructions += """
🔍 **SEARCH TOOL**: For current information and recent data
   Format: [TOOL: search_web(query="your search query")]
   Example: [TOOL: search_web(query="latest AI research 2024")]

"""
    
    if "get_weather" in detected_tools:
        tool_instructions += """
🌤️ **WEATHER TOOL**: For weather information
   Format: [TOOL: get_weather(location="city, country")]
   Example: [TOOL: get_weather(location="Toronto, Canada")]

"""
    
    tool_instructions += """
**USAGE GUIDELINES:**
- Use tools when they would provide more accurate or helpful information
- Include the tool call in your response where it makes sense
- Continue with your explanation after the tool call
- Only use tools that are relevant to the user's question

"""
    
    enhanced_prompt = f"""{rag_context}

{tool_instructions}

**Remember:** Use the available tools when they would improve your educational response."""
    
    print(f"✅ DAILY PROMPT ENHANCED")
    print(f"📏 Original length: {len(rag_context)} chars")
    print(f"📏 Enhanced length: {len(enhanced_prompt)} chars")
    print(f"🛠️ Tools available: {len(detected_tools)}")
    
    return enhanced_prompt


def parse_daily_tool_calls(response: str) -> List[Dict[str, Any]]:
    """
    Parse tool calls from Daily mode LLM response
    Format: [TOOL: tool_name(param="value")]
    """
    print(f"\n🔍 PARSING DAILY MODE TOOL CALLS")
    print(f"📝 Checking response for tool calls...")
    
    tool_calls = []
    
    # First find all [TOOL: sections
    tool_starts = []
    pos = 0
    while True:
        match = re.search(r'\[TOOL:\s*(\w+)\(', response[pos:])
        if not match:
            break
        tool_name = match.group(1)
        start_pos = pos + match.start()
        paren_start = pos + match.end() - 1  # Position of opening parenthesis
        tool_starts.append((tool_name, start_pos, paren_start))
        pos = paren_start + 1
    
    # For each tool start, find the matching closing parenthesis and ]
    for tool_name, start_pos, paren_start in tool_starts:
        paren_count = 1
        pos = paren_start + 1
        
        while pos < len(response) and paren_count > 0:
            if response[pos] == '(':
                paren_count += 1
            elif response[pos] == ')':
                paren_count -= 1
            pos += 1
        
        if paren_count == 0 and pos < len(response) and response[pos] == ']':
            # Found complete tool call
            params_str = response[paren_start + 1:pos - 1]
            raw_call = response[start_pos:pos + 1]
            
            print(f"🛠️ Found tool call: {tool_name} with params: {params_str}")
            
            # Parse parameters (simple key="value" format)
            params = {}
            param_pattern = re.compile(r'(\w+)="([^"]*)"')
            param_matches = param_pattern.findall(params_str)
            
            for param_name, param_value in param_matches:
                params[param_name] = param_value
            
            tool_calls.append({
                "tool": tool_name,
                "params": params,
                "raw": raw_call
            })
            
            print(f"  📋 Parsed: tool={tool_name}, params={params}")
    
    if tool_calls:
        print(f"🎯 FOUND {len(tool_calls)} TOOL CALLS")
    else:
        print(f"❌ NO TOOL CALLS FOUND")
    
    print(f"🔍 TOOL PARSING COMPLETE\n")
    return tool_calls


def execute_daily_tool(tool_name: str, params: Dict[str, str]) -> str:
    """
    Execute a single tool for Daily mode
    """
    tools_logger = logging.getLogger("ai_agents.tools")
    tools_logger.info(f"🚀 EXECUTING DAILY TOOL: {tool_name} with params: {params}")
    
    print(f"🚀 EXECUTING DAILY TOOL: {tool_name}")
    print(f"📋 Parameters: {params}")
    
    try:
        if tool_name == "calculate":
            from ai_agents.tools import calculate_tool
            expression = params.get("expression", "")
            result = calculate_tool.func(expression)
            print(f"✅ CALCULATION RESULT: {result}")
            tools_logger.info(f"✅ CALCULATE TOOL SUCCESS: expression='{expression}' result='{result}'")
            return result
            
        elif tool_name == "execute_python":
            from ai_agents.tools import code_executor_tool
            code = params.get("code", "")
            result = code_executor_tool.func("python", code)
            print(f"✅ CODE EXECUTION RESULT: {result}")
            tools_logger.info(f"✅ EXECUTE_PYTHON TOOL SUCCESS: code='{code}' result='{result}'")
            return result
            
        elif tool_name == "search_web":
            from ai_agents.tools import search_tool
            query = params.get("query", "")
            result = search_tool.func(query)
            print(f"✅ SEARCH RESULT: {result}")
            tools_logger.info(f"✅ SEARCH_WEB TOOL SUCCESS: query='{query}' result='{result}'")
            return result
            
        elif tool_name == "get_weather":
            from ai_agents.tools import weather_tool
            location = params.get("location", "")
            result = weather_tool.func(location)
            print(f"✅ WEATHER RESULT: {result}")
            tools_logger.info(f"✅ GET_WEATHER TOOL SUCCESS: location='{location}' result='{result}'")
            return result
            
        else:
            error_msg = f"❌ UNKNOWN TOOL: {tool_name}"
            print(error_msg)
            tools_logger.error(f"❌ UNKNOWN TOOL REQUESTED: {tool_name} with params: {params}")
            return error_msg
            
    except Exception as e:
        error_msg = f"❌ TOOL EXECUTION ERROR: {str(e)}"
        print(error_msg)
        tools_logger.error(f"❌ TOOL EXECUTION ERROR for {tool_name}: {str(e)} (params: {params})")
        return error_msg


def process_daily_response_with_tools(response: str, llm_function) -> str:
    """
    Process Daily mode response with proper tool calling flow:
    1. Parse initial LLM response for tool calls
    2. Execute tools and get results
    3. Send tool results back to LLM for final response
    4. Return the LLM's final response with tool results integrated
    """
    tools_logger = logging.getLogger("ai_agents.tools")
    tools_logger.info(f"🔄 PROCESSING DAILY RESPONSE WITH TOOLS - Response length: {len(response)} chars")
    
    print(f"\n🔄 PROCESSING DAILY RESPONSE WITH PROPER TOOL FLOW")
    
    # Parse tool calls from the initial LLM response
    tool_calls = parse_daily_tool_calls(response)
    
    if not tool_calls:
        print(f"📝 No tool calls found - returning original response")
        tools_logger.info("📝 No tool calls found in response")
        return response
    
    print(f"🛠️ Found {len(tool_calls)} tool calls - executing them...")
    tools_logger.info(f"🛠️ Processing {len(tool_calls)} tool calls: {[tc['tool'] for tc in tool_calls]}")
    
    # Execute all tools and collect results
    tool_results = {}
    for tool_call in tool_calls:
        tool_name = tool_call["tool"]
        params = tool_call["params"]
        raw_call = tool_call["raw"]
        
        print(f"🚀 Executing tool: {tool_name} with params: {params}")
        tool_result = execute_daily_tool(tool_name, params)
        tool_results[raw_call] = tool_result
        print(f"✅ Tool {tool_name} executed successfully")
    
    # Create a subtle prompt with tool results seamlessly integrated
    tool_results_text = "\n\n".join([
        f"{result}"
        for call, result in tool_results.items()
    ])
    
    follow_up_prompt = f"""I just executed a search tool for the user's query and got these results:

{tool_results_text}

Based on these search results, provide a helpful response to the user's original question. If the search found useful information, reference it naturally. If the search failed or found no results, acknowledge that and respond appropriately to help the user anyway."""

    print(f"🔄 Sending tool results back to LLM for final response...")
    tools_logger.info(f"🔄 Sending tool results back to LLM for final response")
    
    try:
        # Get the final response from LLM with tool results
        final_response = llm_function(follow_up_prompt)
        
        print(f"🎯 RECEIVED FINAL RESPONSE FROM LLM")
        tools_logger.info(f"🎯 DAILY TOOL FLOW COMPLETE - Final response generated")
        return final_response
        
    except Exception as e:
        error_msg = f"❌ ERROR getting final response from LLM: {str(e)}"
        print(error_msg)
        tools_logger.error(f"❌ ERROR in final LLM call: {str(e)}")
        
        # Fallback: manually integrate tool results into original response
        print(f"🔧 FALLBACK: Manually integrating tool results...")
        processed_response = response
        for raw_call, tool_result in tool_results.items():
            tool_result_formatted = f"\n\n**Tool Result:**\n{tool_result}\n\n"
            processed_response = processed_response.replace(raw_call, tool_result_formatted)
        
        return processed_response


def create_simple_llm_function(llm_endpoint):
    """
    Create a simple LLM function for tool result processing
    """
    async def simple_llm_call(prompt: str) -> str:
        """Simple LLM call for tool result integration"""
        try:
            # Create a minimal request for the follow-up
            from .models import ChatRequest
            
            follow_up_request = ChatRequest(
                prompt=prompt,
                course_id="daily_tool_followup",
                conversation_id="tool_processing"
            )
            
            # Get response from LLM
            response = await llm_endpoint(follow_up_request)
            
            # Extract text from streaming response
            chunks = []
            async for chunk in response.body_iterator:
                chunk_str = chunk.decode('utf-8') if isinstance(chunk, bytes) else chunk
                chunks.append(chunk_str)
            
            raw_response = ''.join(chunks)
            
            # Extract content from JSON streaming format
            import json
            full_response = ""
            for line in raw_response.split('\n'):
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        if 'content' in data:
                            full_response += data['content']
                    except json.JSONDecodeError:
                        continue
            
            return full_response
            
        except Exception as e:
            return f"Error getting LLM response: {str(e)}"
    
    return simple_llm_call