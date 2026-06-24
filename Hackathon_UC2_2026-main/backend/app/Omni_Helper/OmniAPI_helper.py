import json
import sys
import os
import asyncio
from typing import List, Optional, Union, Dict
from langgraph.prebuilt import create_react_agent as ReAct
from langchain_core.tools import BaseTool, Tool, StructuredTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, MessagesState, START, END

sys.path.insert(0, os.path.abspath((os.path.dirname(__file__))))

from utils.Langchain_wrapper import GAI
from utils.Langgraph_wrapper import Graph_GAI
from utils.chatbot import Chatbot
from utils.embeddings import Embeddings_Calculator
from utils.agent_stopping import create_stopping_condition
from utils.logging_config import logger

class OmniAPI_Helper:

    def __init__(self, conversation_token, semantic_token=None, environment: str = "dev"):
        try:
            self.token = conversation_token
            self.semantic_token = semantic_token
            self.environment = environment
            self.embedding_calculator = Embeddings_Calculator(token=self.token, environment=self.environment)
            logger.info(f"OmniAPI_Helper initialized with token: {self.token}")
        except Exception as e:
            logger.error(f"Error in initiating OmniAPI_Helper: {e}")
            raise

    async def create_agent_with_tools(self,
                                      engine: str,
                                      system_text: str,
                                      temperature: float,
                                      clients: Optional[List['MultiServerMCPClient']] = None,
                                      additional_tools: Optional[List[BaseTool]] = None,
                                      max_iterations: int = 15,
                                      max_tool_calls: int = 10,
                                      completion_phrases: List[str] = None,
                                      use_custom_stopping: bool = True,
                                      ):
        """
        Creates a Langgraph wrapper for an Omni API conversation service with tools/MCP compatibility

        Args:
            engine: The LLM model for the agent.
            system_text (str): The given instructions for the agent.
            temperature (float): The parameter for the randomness of model's output. A low temperature --> predictable and deterministic, a high temperature --> random and creative.
            clients (list): list of MCP clients for the agent.
            additional_tools (list): list of tools for the agent.
            max_iterations (int): Max iteration for stopping the agent
            max_tool_calls (int): Max tool call for stopping the agent
            completion_phrases (list): Custom phrases for stopping the agent
            use_custom_stopping (bool): Whether to use stopping conditions for the agent

        Note: there should be at least one given tool or MCP client to create Langgraph agent. Otherwise ise create_agent

        Returns:
            Langgraph wrapper for Omni API as an agent with tools
        """
        try:
            all_tools = []
            if clients:
                # Iterate over each client and append their tools to the list
                for client in clients:
                    tools = await client.get_tools()
                    all_tools.extend(tools)
            if additional_tools:
                # Add any additional tools provided
                all_tools.extend(additional_tools)

            assert len(all_tools) > 0, "The list of clients or additional_tools should contain more than 0 tools."

            agent = ReAct(
                Graph_GAI(
                    token=self.token,
                    engine=engine,
                    system_text=system_text,
                    temperature=temperature,
                    environment=self.environment
                ),
                all_tools,
            )

            if use_custom_stopping:
                # Create a custom stopping condition
                stopping_condition = create_stopping_condition(
                    max_iterations=max_iterations,
                    max_tool_calls=max_tool_calls,
                    completion_phrases=completion_phrases
                )
                # Create a new graph with stopping condition
                workflow = StateGraph(MessagesState)
                workflow.add_node("agent", agent)
                workflow.add_edge(START, "agent")
                workflow.add_conditional_edges(
                    "agent",
                    lambda state: stopping_condition(state),
                    {
                        "continue": "agent",
                        "end": END,
                    }
                )
                return workflow.compile()
            else:
                return agent

        except Exception as e:
            logger.error(f"Error in creating Graph_GAI: {e}")
            raise

    def create_agent(self, engine: str, system_text: str, temperature: float, web_search: bool = False):
        """
        Creates a Langchain wrapper for an Omni API conversation service.

        Args:
            engine: The LLM model for the agent.
            system_text (str): The given instructions for the agent.
            temperature (float): The parameter for the randomness of model's output. A low temperature --> predictable and deterministic, a high temperature --> random and creative.
            web_search (bool): Whether to use web_search for only Gemini models

        Returns:
            Langchain wrapper for Omni API as an agent
        """
        try:
            return GAI(
                token=self.token,
                engine=engine,
                system_text=system_text,
                temperature=temperature,
                environment=self.environment,
                web_search=web_search
            )
        except Exception as e:
            logger.error(f"Error in creating GAI: {e}")
            raise

    def create_chatbot(self, engine: str, system_text: str, temperature: float, max_token: int = 8192, reasoning: str = 'low', timeout: int = 30):
        """
        Creates a chatbot from the given configurations using the Omni API conversation service.

        Args:
            engine: The LLM model for the chatbot.
            system_text (str): The given instructions for the chatbot.
            temperature (float): The parameter for the randomness of model's output. A low temperature --> predictable and deterministic, a high temperature --> random and creative.
            max_token (int): Maximum tokens for the response. Defaults to 8192
            reasoning (str): Reasoning effort level for reasoning models ('low', 'medium', 'high'). Defaults to 'low'
            timeout (int): Request timeout in seconds. Defaults to 30

        Returns:
            chatbot using Omni API
        """
        try:
            chatbot = Chatbot(
                token=self.token,
                engine=engine,
                temperature=temperature,
                environment=self.environment,
                max_token=max_token,
                reasoning=reasoning,
                timeout=timeout
            )
            chatbot.register_agent(system_text)
            return chatbot
        except Exception as e:
            logger.error(f"Error in creating chatbot: {e}")
            raise

    async def create_assistant(self, engine: str, system_text: str, temperature: float, tools=None, max_token: int = 8192):
        """
        Creates an assistant (chatbot) from the given configurations using the Omni API conversation service.
        This is an alias for create_chatbot for compatibility with reputation workflow.

        Args:
            engine: The LLM model for the assistant.
            system_text (str): The given instructions for the assistant.
            temperature (float): The parameter for the randomness of model's output.
            tools: Optional tools (not used, for compatibility)
            max_token (int): Maximum tokens for the response. Defaults to 8192

        Returns:
            A wrapper around chatbot that provides an ask() method returning only the response string
        """
        chatbot = self.create_chatbot(engine, system_text, temperature, max_token=max_token)
        
        # Chatbot already returns just a string from ask(), no need for wrapper
        return chatbot

    def create_structured_tool(self, func, name: str, description: str) -> StructuredTool:
        """
        Creates a StructuredTool from a given function, name, and description.

        Args:
            func: The function to be wrapped by the StructuredTool.
            name (str): The name of the tool.
            description (str): A description of what the tool does.

        Returns:
            StructuredTool: An instance of StructuredTool created from the provided function, name, and description.
        """
        try:
            return StructuredTool.from_function(
                func=func,
                name=name,
                description=description
            )
        except Exception as e:
            logger.error(f"Error in creating structured tool: {e}")
            raise

    def create_mcp_client(self, configs: Union[Dict[str, Dict[str, str]], List[Dict[str, Dict[str, str]]]]) -> MultiServerMCPClient:
        """
        Creates a MultiServerMCPClient from a given configuration or list of configurations.

        Parameters:
            configs: A dictionary or a list of dictionaries where each dictionary represents the configuration for an MCP server.
        
        Note: Each configuration should have a structure compatible with MultiServerMCPClient.
        - Stdio transport example:
            "math": {
                "command": "python",
                # Replace with absolute path to your math_server.py file
                "args": ["/path/to/math_server.py"],
                "transport": "stdio",
            },
        - Streamable HTTP transport:
            "weather": {
                # Ensure you start your weather server on port 8000 or other given server
                "url": "http://localhost:8000/mcp",
                "transport": "streamable_http",
            }

        Returns:
            MultiServerMCPClient: An instance of MultiServerMCPClient created from the provided configurations.
        """
        try:
            if not configs:
                return None
            # If configs is a single dictionary, convert it to a list with a single element
            if isinstance(configs, dict):
                configs = [configs]
            # Combine all configurations into a single dictionary
            combined_config = {}
            for config in configs:
                combined_config.update(config)
            return MultiServerMCPClient(combined_config)
        except Exception as e:
            logger.error(f"Error in creating MCP client: {e}")
            raise