from logging import config
import sys
import os
from typing import (
    TypedDict, Awaitable, Callable, Tuple, List, Optional, Union, Dict, Any
)

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.language_models.llms import LLM
from langgraph.prebuilt import create_react_agent as ReAct

# Add the parent directory to sys.path so we can import our models
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

from app.agentic_engine.backend.Omni_Helper.OmniAPI_helper import OmniAPI_Helper
from app.agentic_engine.backend.Omni_Helper.utils.logging_config import logger

DEFAULT_ENGINE = "gemini-2.0-flash"
DEFAULT_TEMPERATURE = 0.5
DEFAULT_SYSTEM_TEXT = "You are a helpful assistant."
DEFAULT_MAX_ITERATIONS = 15
DEFAULT_MAX_TOOL_CALLS = 10
DEFAULT_CHAT_HISTORY_LIMIT = 5

class NodeBuilder:
    """
    A class to build and manage agent nodes for Langgraph workflows.
    """

    @staticmethod
    def _format_prompt(
        prompt: str, 
        state: Dict[str, Any], 
        evaluator_feedback: bool = False
    ) -> str:
        """Format the prompt with context from state."""
        formatted_prompt = f"Current Query: ### {prompt} ###"
        
        if state.get("input"):
            formatted_prompt = f"Original User Prompt: ### {state.get('input')} ###\n\n{formatted_prompt}"
        
        if evaluator_feedback and state.get("evaluator_feedback"):
            formatted_prompt = f"Evaluator Feedback: ### {state.get('evaluator_feedback')} ###\n\n{formatted_prompt}"
        return formatted_prompt
    
    @staticmethod
    async def _invoke_agent(
        agent: Union[LLM, ReAct], 
        prompt: str, 
        messages: List[Dict[str, Any]], 
        chat_history_limit: int,
        verbose: bool,
        thread_id: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """Invoke the agent with the given prompt and return response + thread_id."""
        try:
            history = messages[-chat_history_limit:] if messages else []
            full_prompt = f"Chat History: ### {history} ###\n\n{prompt}" if history else prompt
            try:
                # Try GAI's LLM first
                agent.set_thread_id(thread_id)
                return agent.invoke(full_prompt), agent.get_thread_id()
            except:
                # Fallback to Graph_GAI's ReAct
                processed = [
                    {"role": "assistant", "content": f"Agent {m['role']}: {m['content']}"}
                    if m["role"] != "user" else m
                    for m in history
                ]
                response = await agent.ainvoke({
                    "messages": processed + [
                        {"role": "user", "content": prompt, "thread_id": thread_id, "verbose": verbose}]
                })
                return response['messages'][-1].content, thread_id
        except Exception as e:
            logger.error(f"Error invoking agent: {e}")
            return "Error invoking agent", thread_id

    @staticmethod
    async def _process(
        agent: Union[LLM, ReAct],
        prompt: str,
        state: TypedDict,
        agent_name: str = "Agent",
        chat_history_limit: int = DEFAULT_CHAT_HISTORY_LIMIT,
        parallel: bool = False,
        evaluator_feedback: bool = False,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Process the prompt and create response based on the given agent and state.
        
        Args:
            agent: The agent to process the prompt
            prompt: The input prompt
            state: Current state dictionary
            agent_name: Name of the agent for logging
            chat_history_limit: Maximum chat history to include
            parallel: Whether running in parallel mode
            evaluator_feedback: Whether to include evaluator feedback
            
        Returns:
            Dict containing response and updated messages
        """
        logger.info(f"\x1b[1;36m***{agent_name} Called!***\x1b[0m")
        try:
            messages = state.get("messages", [])
            thread_id = state.get("thread_id", None)
            formatted_prompt = NodeBuilder._format_prompt(prompt, state, evaluator_feedback)
            response, returned_thread_id = await NodeBuilder._invoke_agent(
                agent, formatted_prompt, messages, chat_history_limit, verbose, thread_id
            )
            if not parallel:
                # Update messages with agent response
                messages.append({"role": agent_name, "content": response})
            # logger.info(f"Given Prompt: ###\n{prompt}\n###")
            logger.info(f"{agent_name}: ###\n{response}\n###")
            return {
                "response": response,
                "messages": messages,
                "thread_id": returned_thread_id
            }
        except Exception as e:
            logger.error(f"Error in process {agent_name}: {e}")
            return {
                "response": f"An error occurred in processing the agent response: {e}",
                "messages": None
            }

    @staticmethod
    def generate_agent_function(
        agent_processor: Union[LLM, ReAct],
        agent_name: str,
        response_key: str,
        state_key: Optional[str] = None,
        parallel: bool = False,
        chat_history_limit: int = DEFAULT_CHAT_HISTORY_LIMIT,
        evaluator_feedback: bool = False,
        verbose: bool = True
    ) -> Callable[[TypedDict], Awaitable[Dict[str, Any]]]:
        """
        Generates a specific agent function based on the provided parameters.

        Args:
            - agent_processor: The agent processor to use (e.g., self.Analytical_Audience_IQ)
            - agent_name: The name of the agent
            - response_key: The key to use in the response dictionary
            - state_key: The key to use from the state dictionary for the prompt. If None, use state["input"]
            - parallel: Whether to run the process in parallel
            - chat_history_limit: The chat history limit
            - evaluator_feedback: whether to use evaluator feedback

        Returns:
            - A function that can be awaited and will process the agent's task
        """

        async def agent_function(state: TypedDict) -> Dict[str, Any]:
            try:
                prompt = state[state_key] if state_key else state["input"]
                response_dict = await NodeBuilder._process(
                    agent=agent_processor,
                    prompt=prompt,
                    state=state,
                    agent_name=agent_name,
                    chat_history_limit=chat_history_limit,
                    parallel=parallel,
                    evaluator_feedback=evaluator_feedback,
                    verbose=verbose
                )
                return {
                    response_key: response_dict.get("response", ""),
                    "messages": response_dict.get("messages", []),
                    "thread_id": response_dict.get("thread_id", None)
                }
            except Exception as e:
                logger.info(f"Error in {agent_name}: {e}")
                return {response_key: ""}

        return agent_function

    @staticmethod
    async def create_node(
        omni_helper: OmniAPI_Helper,
        engine: str = DEFAULT_ENGINE,
        temperature: float = DEFAULT_TEMPERATURE,
        system_text: str = DEFAULT_SYSTEM_TEXT,
        clients: Optional[List[MultiServerMCPClient]] = None,
        additional_tools: Optional[List[BaseTool]] = None,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        max_tool_calls: int = DEFAULT_MAX_TOOL_CALLS,
        completion_phrases: Optional[List[str]] = None,
        use_custom_stopping: bool = True,
        verbose: bool = True,
        web_search: bool = False,
        agent_name: Optional[str] = None,
        response_key: Optional[str] = None,
        state_key: str = 'input',
        parallel: bool = False,
        chat_history_limit: int = DEFAULT_CHAT_HISTORY_LIMIT,
        evaluator_feedback: bool = False,
    ) -> Tuple[Union[LLM, ReAct], Callable[[TypedDict], Awaitable[Dict[str, Any]]]]:
        """
        Create a node of an agent using the provided parameters.
        If tools or clients are empty, a GAI agent is created, otherwise a Graph_GAI agent is created.
        Args:
            - omni_helper: The OmniAPI_Helper instance
            - engine: The engine to use for the agent
            - temperature: The temperature for the agent's responses
            - system_text: The system prompt for the agent,
            - clients: The clients to use for the agent
            - additional_tools: Additional tools to use for the agent
            - max_iterations: The maximum number of iterations for the agent
            - max_tool_calls: The maximum number of tool calls for the agent
            - completion_phrases: The completion phrases for the agent
            - use_custom_stopping: Whether to use custom stopping for the agent
            - verbose: Whether to show Langgraph thinking and tool calling process
            - web_search (bool): Only available for Gemini models and Langchain agent
            - agent_name: The name of the agent
            - response_key: The key to use in the response dictionary
            - state_key: The key to use from the state dictionary for the prompt. If None, use state["input"]
            - parallel: Whether to run the process in parallel
            - chat_history_limit: The chat history limit
            - evaluator_feedback: whether to use evaluator feedback

        Return:
            - A tuple containing the agent and the agent node function.
        """
        
        assert agent_name and response_key, "The agent_name and response_key must be provided."

        has_clients = clients is not None and isinstance(clients, list) and len(clients) > 0
        has_tools = additional_tools is not None and isinstance(additional_tools, list) and len(additional_tools) > 0

        if has_clients or has_tools:
            agent = await omni_helper.create_agent_with_tools(
                engine=engine, 
                system_text=system_text, 
                temperature=temperature,
                clients=clients,
                additional_tools=additional_tools,
                max_iterations=max_iterations,
                max_tool_calls=max_tool_calls,
                completion_phrases=completion_phrases,
                use_custom_stopping=use_custom_stopping,
            )

        else:
            agent = omni_helper.create_agent(
                engine=engine,
                system_text=system_text,
                temperature=temperature,
                web_search=web_search
            )

        agent_node = NodeBuilder.generate_agent_function(
            agent_processor=agent,
            agent_name=agent_name,
            response_key=response_key,
            state_key=state_key,
            parallel=parallel,
            chat_history_limit=chat_history_limit,
            evaluator_feedback=evaluator_feedback,
            verbose=verbose
        )

        return agent, agent_node


async def process(*args, **kwargs):
    return await NodeBuilder._process(*args, **kwargs)


async def create_nodes_from_config(
    config: Dict,
    omni_helper: OmniAPI_Helper,
    mcp_server_config: Dict,
) -> Dict:
    """
    Creates nodes using the workflow config files
    return a dict of agents, agent_nodes, and their config
    """
    workflow_config = {}
    for agent_name, agent_config in config.items():
        # print(agent_config)
        # Create needed MCP clients and update agent config
        clients_name = agent_config.get("clients") if agent_config.get("clients") else []
        clients = omni_helper.create_mcp_client([mcp_server_config[k] for k in clients_name if k in mcp_server_config])
        agent_config['clients'] = [clients] if clients else None
        ## Define node config
        node_config = {
            "engine": agent_config.get("engine"),
            "temperature": agent_config.get("temperature"),
            "system_text": agent_config.get("system_text"),
            "clients": agent_config.get("clients"),
            "additional_tools": agent_config.get("additional_tools"),
            "max_iterations": agent_config.get("max_iterations"),
            "max_tool_calls": agent_config.get("max_tool_calls"),
            "completion_phrases": agent_config.get("completion_phrases"),
            "use_custom_stopping": agent_config.get("use_custom_stopping"),
            "verbose": agent_config.get("verbose", True),
            "web_search": agent_config.get("web_search", False),
            "agent_name": agent_config.get("agent_name"),
            "response_key": agent_config.get("response_key"),
            "state_key": agent_config.get("state_key"),
            "evaluator_feedback": agent_config.get("evaluator_feedback")
        }
        agent_config["clients"] = [clients] if clients else None
        # Create agent and agent node function
        agent, agent_node = await NodeBuilder.create_node(
                omni_helper=omni_helper,
                **node_config
        )
        workflow_config[agent_name] = {
            "agent": agent,
            "agent_node": agent_node,
            "omni_helper": omni_helper,
            "config": node_config
        }

        if not node_config.get("state_key"):
            logger.warning(f"Warning: Agent '{agent_name}' is missing a state key. Create a custom function for it!")

    return workflow_config