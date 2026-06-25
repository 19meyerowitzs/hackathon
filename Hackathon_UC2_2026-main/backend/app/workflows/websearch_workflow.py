import json
from typing import Dict, Any, Optional
from app.Omni_Helper.src.omni_helper import OmniAPI_Helper
from app.utils.logging_config import get_logger
from .websearch_workflow_configs import config


class WebSearchState(dict):
    """State for the web search workflow."""
    query: str
    search_result: Optional[str] = None
    error: Optional[str] = None


class WebSearchWorkflow:
    """
    Simple workflow for testing web search with Gemini models.
    
    Usage:
        workflow = WebSearchWorkflow(api_key="your_key", thread_id="123")
        await workflow.initialize()
        result = await workflow.search("What are the latest news in Germany?")
    """
    
    def __init__(self, api_key: str, thread_id: str):
        """Initialize the workflow."""
        self.api_key = api_key
        self.thread_id = thread_id
        self.omni_helper = OmniAPI_Helper(
            conversation_token=api_key,
            semantic_token=None,
            environment='dev'
        )
        self.base_config = config
        self.agents = {}
        self.initialized = False
        
    async def initialize(self):
        """Initialize the workflow and create agents."""
        if self.initialized:
            return
            
        get_logger().info("Creating Web Search Workflow...")
        
        try:
            await self._create_nodes()
            self.initialized = True
            get_logger().info("Web Search Workflow initialized successfully.")
        except Exception as e:
            get_logger().error(f"Web Search Workflow initialization error: {e}")
            raise
    
    async def _create_nodes(self):
        """Create web search agent with web_search_preview tool."""
        nodes_cfg = self.base_config.get("nodes", {})
        
        for node_name, cfg in nodes_cfg.items():
            # Create assistant with web search tool
            tools = cfg.get("tools", [])
            
            self.agents[node_name] = await self.omni_helper.create_assistant(
                engine=cfg.get("engine", "gemini-2.0-flash"),
                system_text=cfg.get("system_text", ""),
                temperature=cfg.get("temperature", 0.7),
                tools=tools  # Include web_search_preview tool
            )
        
        get_logger().info(f"Web Search agents created: {list(self.agents.keys())}")
    
    async def search(self, query: str, verbose: bool = True) -> Dict[str, Any]:
        """
        Perform a web search using the search agent.
        
        Args:
            query: The search query/question
            verbose: Whether to show verbose output
            
        Returns:
            Dictionary with search results and metadata
        """
        if not self.initialized:
            await self.initialize()
        
        state = WebSearchState()
        state["query"] = query
        
        try:
            get_logger().info(f"🔍 Web Search Query: {query}")
            
            # Get the search agent
            search_agent = self.agents.get("search")
            if not search_agent:
                raise ValueError("Search agent not initialized")
            
            # Perform search
            node_config = self.base_config["nodes"]["search"]
            log_msg = node_config["log_message"]["loading"]
            get_logger().info(f"*** {log_msg} ***")
            
            # Ask the agent - it will use web search automatically
            response = await search_agent.ask(query, verbose=verbose)
            
            state["search_result"] = response
            
            get_logger().info(node_config["log_message"]["finished"])
            
            return {
                "status": "success",
                "query": query,
                "result": response,
                "agent": node_config["agent_name"],
                "model": node_config["engine"],
            }
            
        except Exception as e:
            error_msg = f"Web search failed: {str(e)}"
            get_logger().error(error_msg)
            state["error"] = error_msg
            
            return {
                "status": "error",
                "query": query,
                "error": error_msg,
            }
    
    async def cleanup(self):
        """Cleanup workflow resources."""
        self.agents.clear()
        self.initialized = False
