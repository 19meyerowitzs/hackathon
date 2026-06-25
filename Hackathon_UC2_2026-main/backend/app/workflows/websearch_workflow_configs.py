"""
Configuration for the Web Search Workflow (Testing).
"""
from .agents import SearchAgentConfig

config = {
    "workflow_name": "Web Search Test Workflow",
    "description": "Simple workflow for testing web search capabilities with Gemini 2.0/2.5.",
    "nodes": {
        "search": {
            "engine": "gemini-2.5-flash-lite",  # Use available model
            "temperature": SearchAgentConfig.temperature,
            "system_text": SearchAgentConfig.system_prompt,
            "clients": SearchAgentConfig.clients,
            "agent_name": SearchAgentConfig.name,
            "tools": SearchAgentConfig.tools,
            "response_key": "search_result",
            "description": "Performs web search and provides answers with URL sources",
            "log_message": {
                "loading": SearchAgentConfig.log_message,
                "finished": "Search completed",
                "step_id": 1,
            },
        },
    },
    "edges": {
        # Simple single-node workflow - no edges needed
    },
}
