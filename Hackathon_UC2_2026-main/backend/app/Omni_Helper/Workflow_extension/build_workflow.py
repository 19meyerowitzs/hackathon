import sys
import os
import copy
from typing import Tuple, List, Dict, Any, Optional
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import InMemorySaver
# Add the parent directory to sys.path so we can import our models
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

from app.agentic_engine.backend.Omni_Helper.OmniAPI_helper import OmniAPI_Helper
from app.agentic_engine.backend.Omni_Helper.utils.logging_config import logger
from app.agentic_engine.backend.Omni_Helper.Workflow_extension import build_node


class WorkflowBuilder:
    """
    A class to build and manage LangGraph workflows with dynamic supervisor support.
    """

    @staticmethod
    def get_connected_agents_with_cards(
        router_workflow: StateGraph, 
        source_node: str, 
        agent_cards: Dict[str, str]
    ) -> Tuple[List[Dict[str, str]], List[str]]:
        """
        Get agents connected to a source node with their card descriptions.

        Args:
            router_workflow: The LangGraph workflow object
            source_node: The name of the source node
            agent_cards: Dictionary mapping agent names to their card descriptions

        Returns:
            Tuple of (connected_agents_with_cards, agent_names)
        """
        try:
            graph_data = router_workflow.get_graph().to_json()
            connected_agents = []
            agent_names = []
            
            for edge in graph_data.get("edges", []):
                if edge.get("source") == source_node:
                    target = edge.get("target")
                    card = agent_cards.get(target, "No description available.")
                    connected_agents.append({
                        'Name': target, 
                        'Description': card
                    })
                    agent_names.append(target)
            
            return connected_agents, agent_names
            
        except Exception as e:
            logger.error(f"Error getting connected agents: {e}")
            return [], []
        
    @staticmethod
    def _extract_agent_cards(workflow_config: Dict[str, Any]) -> Dict[str, str]:
        """Extract agent cards from workflow config."""
        return {
            name: config.get("description", "No description available.")
            for name, config in workflow_config.get('config', {}).items()
        }
    
    @staticmethod
    def _validate_supervisor_config(
        workflow_config: Optional[Dict[str, Any]], 
        dynamic_supervisor: bool
    ) -> None:
        """Validate supervisor configuration requirements."""
        if not dynamic_supervisor:
            return
            
        if not workflow_config:
            raise ValueError("Workflow config is required for dynamic supervisor.")
        
        supervisor_config = workflow_config.get('supervisor')
        if not supervisor_config:
            raise ValueError("Supervisor config is required for dynamic supervisor.")

    @staticmethod
    async def _create_dynamic_supervisor(
        workflow_config: Dict[str, Any],
        temp_router_workflow: StateGraph,
        agent_cards: Dict[str, str]
    ) -> Tuple[Any, Any, Any]:
        """Create a dynamic supervisor with connected agent information."""
        # Get connected agents to the supervisor with cards
        workers, names = WorkflowBuilder.get_connected_agents_with_cards(
            temp_router_workflow, "supervisor", agent_cards
        )
        
        # Update supervisor system text with connected agents
        supervisor_config = workflow_config['supervisor']
        supervisor_config['config']['system_text'] = supervisor_config['config']['system_text'].format(
            cards=workers, 
            names=names
        )
        workflow_config['supervisor'] = supervisor_config
        # Create supervisor node
        supervisor, supervisor_node = await build_node.NodeBuilder.create_node(
            omni_helper=supervisor_config['omni_helper'],
            **supervisor_config['config']
        )
        
        return supervisor, supervisor_node, workflow_config

    @staticmethod
    async def _update_agent_system_text(
            workflow_config: Dict[str, Any],
            agent_name: str,
            new_system_text: str
    ) -> Tuple[Any, Any, Any]:
        """Update an agent's system text and recreate the node."""
        agent_config = workflow_config.get(agent_name)
        if not agent_config:
            raise ValueError(f"Agent '{agent_name}' not found in workflow config.")

        agent_config['config']['system_text'] = new_system_text
        workflow_config[agent_name] = agent_config

        agent, agent_node = await build_node.NodeBuilder.create_node(
            omni_helper=agent_config['omni_helper'],
            **agent_config['config']
        )

        return agent, agent_node, workflow_config

    @staticmethod
    async def create_workflow_graph(
        router_builder: StateGraph, 
        workflow_config: Optional[Dict[str, Any]] = None, 
        dynamic_supervisor: bool = True,
        agent_updates: Optional[Dict[str, str]] = None
    ) -> Tuple[Any, Any, Any]:
        """
        Create the workflow graph given the router builder and workflow config.
        
        If dynamic_supervisor is enabled, recreates the supervisor agent with information
        about connected agents that the supervisor can choose from.
        
        Note: Supervisor agent should have two placeholders in system_text: {cards} and {names}
        
        Args:
            router_builder: The StateGraph builder object
            workflow_config: Configuration for workflow agents
            dynamic_supervisor: Whether to create dynamic supervisor with connected agent info
            agent_updates: If passed, update the agent with the given system text
            
        Returns:
            Compiled StateGraph workflow
            
        Raises:
            ValueError: If required configs are missing for dynamic supervisor
        """
        try:
            # Validate configuration
            WorkflowBuilder._validate_supervisor_config(workflow_config, dynamic_supervisor)
            
            # Create temporary workflow for analysis
            temp_router_builder = copy.deepcopy(router_builder)
            temp_router_workflow = temp_router_builder.compile()
            
            # Handle dynamic supervisor creation
            if dynamic_supervisor and workflow_config:
                # Extract agent cards from config
                agent_cards = WorkflowBuilder._extract_agent_cards(workflow_config)
                
                # Create dynamic supervisor
                supervisor, supervisor_node, workflow_config = await WorkflowBuilder._create_dynamic_supervisor(
                    workflow_config, temp_router_workflow, agent_cards
                )
                
                # Replace supervisor node in builder
                if "supervisor" in router_builder.nodes:
                    del router_builder.nodes["supervisor"]
                router_builder.add_node("supervisor", supervisor_node)

            # Handle agent system text updates
            if agent_updates and workflow_config:
                for agent_name, new_system_text in agent_updates.items():
                    # Skip supervisor if it was already handled by dynamic_supervisor
                    if agent_name == "supervisor" and dynamic_supervisor:
                        continue

                    # Update agent system text and recreate node
                    agent, updated_node, workflow_config = await WorkflowBuilder._update_agent_system_text(
                        workflow_config, agent_name, new_system_text
                    )

                    # Replace node in builder
                    if agent_name in router_builder.nodes:
                        del router_builder.nodes[agent_name]
                    router_builder.add_node(agent_name, updated_node)

            # Clean up temporary objects
            del temp_router_workflow
            del temp_router_builder
            new_router_builder = copy.deepcopy(router_builder)  # send a copy of uncompiled one for future changes
            # Compile and return final workflow
            router_workflow = router_builder.compile(checkpointer=InMemorySaver())
            return router_workflow, new_router_builder, workflow_config
            
        except Exception as e:
            logger.error(f"Error creating workflow graph: {e}")
            raise


def get_connected_agents_with_cards(router_workflow, source_node, agent_cards):
    return WorkflowBuilder.get_connected_agents_with_cards(router_workflow, source_node, agent_cards)

async def create_workflow_graph(router_builder, workflow_config, dynamic_supervisor=True):
    return await WorkflowBuilder.create_workflow_graph(router_builder, workflow_config, dynamic_supervisor)

async def workflow_graph_agent_update(router_builder, workflow_config, agent_name, new_system_text):
    """Update a single agent's system text and create workflow graph."""
    agent_updates = {agent_name: new_system_text}
    return await WorkflowBuilder.create_workflow_graph(
        router_builder, workflow_config, dynamic_supervisor=False, agent_updates=agent_updates
    )