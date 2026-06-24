from typing import List, Dict, Any, Union
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage


def should_continue_agent(state: Dict[str, Any], 
                          max_iterations=15, 
                          max_tool_calls=10, 
                          completion_phrases: List[str] = None
) -> str:
    """
    Custom stopping condition for LangGraph agents.
    This module provides stopping logic to prevent infinite loops and ensure agents complete tasks efficiently.
    
    Args:
        state: The current state of the agent conversation
        
    Returns:
        str: "continue" to keep going, "end" to stop the agent
    """
    messages = state.get("messages", [])
    
    if not messages:
        return "continue"
    
    last_message = messages[-1]
    
    # 1. Check for explicit completion signal
    # If the last message is from the agent (AI)
    if isinstance(last_message, AIMessage):
        content = last_message.content or ""
        tool_calls = getattr(last_message, 'tool_calls', []) or []
        
        # Check metadata for stopping signal (TASK_COMPLETE would have been processed and removed)
        response_metadata = getattr(last_message, 'response_metadata', {})
        if response_metadata.get('should_stop', False):
            return "end"
            
        # Check additional_kwargs for stopping signal
        additional_kwargs = getattr(last_message, 'additional_kwargs', {})
        if additional_kwargs.get('should_stop', False):
            return "end"
        
        # If no tool calls and response looks complete
        if not tool_calls and content:
            completion_phrases = completion_phrases if completion_phrases is not None else [
                "the answer is", "based on the information",
                "to summarize", "in conclusion", "hope this helps",
            ]
            if any(phrase in content.lower() for phrase in completion_phrases):
                return "end"
    
    # 2. Check the number of agent calls
    # Count iterations to prevent infinite loops
    ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]
    if len(ai_messages) >= max_iterations:  # Stop after 15 iterations max
        return "end"
    
    # 3. Check the number of tool calls
    # Count consecutive tool calls without meaningful progress
    recent_messages = messages[-15:]  # Look at last 15 messages
    tool_message_count = sum(1 for msg in recent_messages if isinstance(msg, ToolMessage))
    if tool_message_count >= max_tool_calls:  # Too many tool calls recently
        return "end"
    
    return "continue"


def create_stopping_condition(
    max_iterations: int = 15,
    max_tool_calls: int = 10,
    completion_phrases: List[str] = None
) -> callable:
    """
    Create a customizable stopping condition function.
    
    Args:
        max_iterations: Maximum number of AI message iterations
        max_tool_calls: Maximum number of recent tool calls
        completion_phrases: Custom phrases that indicate completion
        
    Returns:
        callable: A stopping condition function
    """
    if completion_phrases is None:
        completion_phrases = [
            "the answer is", "based on the information",
            "to summarize", "in conclusion", "hope this helps",
        ]
    
    def custom_stopping_condition(state: Dict[str, Any]) -> str:
        """
        Custom stopping condition with user-defined parameters.
        """
        messages = state.get("messages", [])
        
        if not messages:
            return "continue"
        
        last_message = messages[-1]
        
        # 1. Check for explicit completion signal
        if isinstance(last_message, AIMessage):
            content = last_message.content or ""
            tool_calls = getattr(last_message, 'tool_calls', []) or []
            
            # Check metadata for stopping signal
            response_metadata = getattr(last_message, 'response_metadata', {})
            if response_metadata.get('should_stop', False):
                return "end"
                
            # Check additional_kwargs for stopping signal
            additional_kwargs = getattr(last_message, 'additional_kwargs', {})
            if additional_kwargs.get('should_stop', False):
                return "end"
            
            # If no tool calls and response looks complete with custom phrases
            if not tool_calls and content:
                if any(phrase in content.lower() for phrase in completion_phrases):
                    return "end"
        
        # 2. Check the number of agent calls with custom max_iterations
        ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]
        if len(ai_messages) >= max_iterations:
            return "end"
        
        # 3. Check the number of tool calls with custom max_tool_calls
        recent_messages = messages[-15:]
        tool_message_count = sum(1 for msg in recent_messages if isinstance(msg, ToolMessage))
        if tool_message_count >= max_tool_calls:
            return "end"
        
        return "continue"
    
    return custom_stopping_condition


def get_completion_status(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get detailed completion status information.
    
    Args:
        state: The current agent state
        
    Returns:
        dict: Status information including reason for stopping
    """
    messages = state.get("messages", [])
    ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]
    tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]
    response_metadata = getattr(last_message, 'response_metadata', {})
    additional_kwargs = getattr(last_message, 'additional_kwargs', {})
    completion_phrases = [
            "the answer is", "based on the information",
            "to summarize", "in conclusion", "hope this helps",
        ]
    max_iterations = 15
    max_tool_calls = 10

    status = {
        "total_messages": len(messages),
        "ai_messages": len(ai_messages),
        "tool_messages": len(tool_messages),
        "stopped": False,
        "stop_reason": None
    }
    
    if messages:
        last_message = messages[-1]
        if isinstance(last_message, AIMessage):
            content = last_message.content or ""

            if (any(x in content.upper() for x in completion_phrases) or 
                response_metadata.get('should_stop', False) or 
                additional_kwargs.get('should_stop', False)):
                status["stopped"] = True
                status["stop_reason"] = "explicit_completion_signal"
            elif len(ai_messages) >= max_iterations:
                status["stopped"] = True
                status["stop_reason"] = "max_iterations_reached"
            elif len(tool_messages) >= max_tool_calls:
                status["stopped"] = True
                status["stop_reason"] = "max_tool_calls_reached"
    
    return status
