"""
Search Agent Configuration for Web Search.
"""

class SearchAgentConfig:
    """Configuration for the Search Agent with web search capabilities."""
    
    name = "Search Agent"
    model = "gemini-2.0-flash"
    temperature = 0.7
    
    # Important: When using web search, always ask for URL sources
    system_prompt = """You are a helpful agent that can use web search to answer questions.

When using web search:
- Always provide URL sources for the information you find
- Be specific about what information you retrieved
- Cite your sources clearly
- Provide current and accurate information

Format your responses clearly with:
1. Direct answer to the question
2. Supporting details from web search
3. URL sources used
"""
    
    clients = ["gemini"]
    
    log_message = "🔍 Searching the web..."
    
    # Web search tool configuration
    # Note: No other tools can be used when web_search_preview is enabled
    tools = [{"type": "web_search_preview"}]
