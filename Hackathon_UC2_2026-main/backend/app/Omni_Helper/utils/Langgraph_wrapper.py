import copy
from pyexpat.errors import messages
from typing import Any, Dict, List, Optional, Sequence, Union, Mapping, Literal, Callable, Type, Iterator, Tuple
from pydantic import Field
import json
import sys
import os
import ast
import re
from dotenv import load_dotenv
from langchain_core.language_models import LanguageModelInput, BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk
from langchain_core.messages import (
    AIMessage, AIMessageChunk, BaseMessage, HumanMessage, SystemMessage, ToolMessage
)
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.messages.ai import UsageMetadata
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_core.runnables import Runnable

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.Omni_Helper.utils.chatbot import Chatbot
from app.Omni_Helper.utils.logging_config import logger

load_dotenv(dotenv_path="../.env")
API_Token = os.getenv("API_Token")

# Regex patterns for tool call extraction
FENCE_RE = re.compile(r"```(?:tool_code)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
FUNC_RE = re.compile(r"\s*([A-Za-z_]\w*)\s*\(", re.MULTILINE)


def first_json_value(s: str) -> Tuple[Any, int]:
    """
    Parse first complete JSON value from string; returns (value, end_idx).
    """
    i = 0
    while i < len(s) and s[i].isspace():
        i += 1
    return json.JSONDecoder().raw_decode(s, idx=i)


def transform_kwargs_to_dict(args_str: str) -> str:
    """
    Transform keyword arguments to dictionary format
    Example: param="value", key=123 -> {"param":"value", "key":123}
    """
    args_str = args_str.strip()
    if args_str.startswith('{') and args_str.endswith('}'):
        return args_str
    # Replace = with : and add quotes around keys
    pattern = r'(\w+)\s*=\s*'
    transformed = re.sub(pattern, r'"\1":', args_str)
    return '{' + transformed + '}'

def merge_concatenated_strings(s: str) -> str:
    """
    Merge Python-style concatenated string literals into a single string
    """
    pattern = re.compile(r'"([^"]*)"\s*\+\s*"([^"]*)"')
    while pattern.search(s):
        s = pattern.sub(lambda m: '"' + m.group(1) + m.group(2) + '"', s)
    return s


class Graph_GAI(BaseChatModel):
    """
    Custom langgraph llm for Omni API.
    Custom chat model integrating with an external chatbot, supporting tool calling.

    Args:
        token (str): API token for authentication.
        engine (str): Model engine to use.
        temperature (float): Sampling temperature.
        system_text (str): System prompt.
        bound_tools (List[Dict[str, Any]]): Tools registered for tool calling.

    Example:
        model = Graph_GAI(token="...", engine="...", system_text="...")
        model_with_tools = model.bind_tools([some_tool])
        result = model_with_tools.invoke([HumanMessage(content="What is X?")])
    """
    token: str = Field(..., description="API token for authentication")
    engine: str = Field(..., description="The model engine to use")
    temperature: float = Field(default=0.7, description="Temperature of the model")
    system_text: str = Field(default="You are a helpful assistant that can use tools to answer questions.",
                             description="System prompt for the chatbot")
    bot: Chatbot = None
    bound_tools: List[Dict[str, Any]] = Field(default_factory=list, description="Tools bound to this model")
    input_tokens: int = 0
    output_tokens: int = 0
    environment: str = Field(default="dev", description="Environment for the chatbot")
    current_thread_id: Optional[str] = Field(default=None, description="Current thread ID for conversation continuity")
    current_verbose: Optional[str] = Field(default=None, description="Current verbose mode for conversation continuity")

    def __init__(self, **data):
        """Initialize the LLM and create the Chatbot instance."""
        super().__init__(**data)
        self.bot = Chatbot(token=self.token, engine=self.engine, temperature=self.temperature,
                           environment=self.environment)
        # Only add if not already present
        if "ANSWER_COMPLETE" not in self.system_text:
            self.system_text += """\n\n
            $$ Override Rules $$
            These rules take ABSOLUTE PRECEDENCE over all previous instructions:
            - Use tools when needed considering TOOL CALLING RULES.
            - Always conclude responses with 'ANSWER_COMPLETE' only when question fully answered and no more tools needed.
            $$ Override Rules $$
            """
        self.bot.register_agent(self.system_text)

    # property that returns a string. Used for logging purposes only.
    @property
    def _llm_type(self) -> str:
        return f"gai_omni_api with {self.engine}"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model_name": self.engine,
            "temperature": self.temperature,
            "has_tools": len(self.bound_tools) > 0,
        }

    # method that takes in a string, some optional stop words, and returns a string.
    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        response, returned_thread_id = self.bot.ask(prompt, thread_id=self.current_thread_id)
        self.current_thread_id = returned_thread_id
        if stop:
            for s in stop:
                if s in response:
                    response = response.split(s)[0]
        return response

    def _format_messages_for_chatbot(self, messages: List[BaseMessage]) -> str:
        """Convert LangChain messages to a format suitable for the chatbot."""
        formatted_parts = []
        # print("--->", messages)
        for message in messages:
            if isinstance(message, HumanMessage):
                formatted_parts.append(f"Human Query: {message.content}")
            elif isinstance(message, SystemMessage):
                formatted_parts.append(f"System: {message.content}")
            elif isinstance(message, AIMessage):
                if message.tool_calls:
                    # Format tool calls
                    tool_calls_str = []
                    for tool_call in message.tool_calls:
                        tool_calls_str.append(f"Tool Call: {tool_call['name']}({json.dumps(tool_call['args'])})")
                    formatted_parts.append(f"Assistant: {message.content}\n{chr(10).join(tool_calls_str)}")
                else:
                    formatted_parts.append(f"Assistant: {message.content}")
            elif isinstance(message, ToolMessage):
                formatted_parts.append(f"Tool Result ({message.name}): {message.content}")

        # Add tool information if tools are bound
        if self.bound_tools:
            tools_info = """
            System:
            Your goal is to be helpful and efficient and output tools and function calls when needed.
            $$ instructions $$
            IMPORTANT INSTRUCTIONS FOR TOOL EXECUTION:
            1. When the user asks multiple questions, identify all the tools you need to query.
            2. For independent tool calls: Call ALL necessary tools in your first response.
            3. For sequential/dependent tool calls: Call tools one at a time, waiting for each result before proceeding.
            4. Observe the result of the tool calls.
            5. Do NOT make additional tool calls unless absolutely necessary.
            6. Once you have all the tool results, provide a complete final answer addressing all parts of the question.
            7. END your response with "ANSWER_COMPLETE" ONLY in your final message when you have fully answered the user's question AND No further tool calls are needed.

            CRITICAL:
            Do NOT include "ANSWER_COMPLETE" in responses containing tool calls OR additional tool calls in subsequent messages are expected.

            TOOL CALLING RULES:
            1. Use EXACT format that always starts with 'tool_code' keyword:
            ```tool_code
            function_name({"param1": value1, "param2": value2})
            ```
            2. Use separate code blocks for multiple tools:
            ```tool_code
            function_1({"param": value})
            ```
            ```tool_code
            function_2()
            ``` 

            Available tools:\n"""
            for tool in self.bound_tools:
                tools_info += f"- {tool['function']['name']}: ### {tool['function']['description']} ###\n"
            tools_info += "$$ instructions $$"
            formatted_parts = [tools_info] + formatted_parts

        return "\n\n".join(formatted_parts)

    def _clean_args(self, response: str) -> str | list[Any]:
        """Extract function call and args from the string"""
        tool_calls = []

        # Extract all code fence contents
        for code_block in FENCE_RE.findall(response):
            func_match = FUNC_RE.search(code_block)
            if not func_match:
                continue
            func_name = func_match.group(1)
            after_paren = code_block[func_match.end():]
            # Parse arguments using JSON decoder for robust parsing
            try:
                after_paren = after_paren.replace("'", '"')  # Json expect key value in double quotes
                after_paren = merge_concatenated_strings(after_paren)
                args_value, _ = first_json_value(after_paren)
                if not isinstance(args_value, dict):
                    raise ValueError("args_value is not a dictionary")
                args = args_value
            except (json.JSONDecodeError, ValueError) as e:  # Fallback: extract until closing parenthesis using ast
                close_paren = after_paren.find(')')
                raw_args = after_paren[:close_paren] if close_paren != -1 else after_paren.strip()
                try:
                    if raw_args and not raw_args.strip().startswith('{'):
                        # Convert keyword arguments to dict format
                        raw_args = copy.deepcopy(transform_kwargs_to_dict(raw_args))
                    args = ast.literal_eval(raw_args.replace("'", '"')) if raw_args else {}
                except Exception as e:
                    logger.warning(f"Error in Tool call {func_name} with {after_paren}: {e}")
                    return (f"""Error in Tool call {func_name} with {after_paren}: {e}
                            Try again with correct function name and arguments format as
                            ```tool_code
                            func_name({"param_1": param_value_1})
                            ```""")

            tool_calls.append({
                "name": func_name,
                "args": args,
                "id": f"tool_call_{len(tool_calls)}"
            })

        return tool_calls

    def _parse_tool_calls(self, response: str) -> tuple[str, list[Any], bool]:
        """Parse tool calls from response text. Returns (clean_response, tool_calls, should_stop)"""
        # Check for completion signal and remove it from the response
        should_stop = "ANSWER_COMPLETE" in response.upper() and 'tool_code' not in response.lower()
        clean_response = re.sub(r'\s*ANSWER_COMPLETE\s*', '', response, flags=re.IGNORECASE).strip()
        tool_calls = []
        if not should_stop:
            tool_calls = self._clean_args(response)
            if isinstance(tool_calls, str):  # Error in tool call
                clean_response = tool_calls
                tool_calls = []

        return clean_response, tool_calls, should_stop

    def _generate(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> ChatResult:
        """Generate a response from the messages, handling tool calls."""
        self.check_kwargs(messages)
        if self.current_verbose: logger.info(f"\x1b[1;35m**Langgraph Agent Thinking Process**\x1b[0m")
        # Format messages for the chatbot
        formatted_prompt = self._format_messages_for_chatbot(messages)
        if self.current_verbose: logger.info(f"\n==========\n1. {formatted_prompt}\n==========\n")
        # Get response from chatbot
        raw_response = self._call(formatted_prompt, stop=stop, **kwargs)
        if self.current_verbose: logger.info(f"\n==========\n2. {raw_response}\n==========\n")
        # Parse tool calls from response
        content, tool_calls, should_stop = self._parse_tool_calls(raw_response)
        if self.current_verbose: logger.info(f"\n==========\n3. {content}\n{tool_calls}\n==========\n")
        # Update token usage
        self.input_tokens = self.bot.token_usage['Input']
        self.output_tokens = self.bot.token_usage['Output']
        # Create AI message with tool calls
        message = AIMessage(
            content=content,
            tool_calls=tool_calls,
            additional_kwargs={"should_stop": should_stop},
            response_metadata={"model_name": self.engine, "should_stop": should_stop,
                               "thread_id": self.current_thread_id},
            usage_metadata={
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "total_tokens": self.input_tokens + self.output_tokens,
            },
        )

        return ChatResult(generations=[ChatGeneration(message=message)])

    def _stream(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        last_message = messages[-1]
        tokens = str(last_message.content[:5])
        ct_input_tokens = sum(len(str(m.content)) for m in messages)

        for token in tokens:
            usage_metadata = UsageMetadata({
                "input_tokens": ct_input_tokens,
                "output_tokens": 1,
                "total_tokens": ct_input_tokens + 1,
            })
            ct_input_tokens = 0
            chunk = ChatGenerationChunk(message=AIMessageChunk(content=token, usage_metadata=usage_metadata))
            if run_manager:
                run_manager.on_llm_new_token(token, chunk=chunk)
            yield chunk

        chunk = ChatGenerationChunk(
            message=AIMessageChunk(
                content="",
                response_metadata={"time_in_sec": 3, "model_name": self.engine},
            )
        )
        if run_manager:
            run_manager.on_llm_new_token("", chunk=chunk)
        yield chunk

    def set_thread_id(self, thread_id: str):
        """Set the thread ID for conversation continuity."""
        self.current_thread_id = thread_id

    def get_thread_id(self) -> Optional[str]:
        """Get the current thread ID."""
        return self.current_thread_id

    def check_kwargs(self, messages):
        thread_id = messages[-1].additional_kwargs.get("thread_id")
        verbose = messages[-1].additional_kwargs.get("verbose")
        if thread_id and thread_id != self.current_thread_id:
            self.current_thread_id = thread_id
        if verbose and verbose != self.current_verbose:
            self.current_verbose = verbose

    def bind_tools(
            self,
            tools: Sequence[Union[Dict[str, Any], Type, Callable, BaseTool]],
            *,
            tool_choice: Optional[Union[dict, str, Literal["auto", "none", "required", "any"], bool]] = None,
            strict: Optional[bool] = None,
            parallel_tool_calls: Optional[bool] = None,
            **kwargs: Any,
    ) -> Runnable[LanguageModelInput, BaseMessage]:
        """Bind tool-like objects to this chat model."""
        if parallel_tool_calls is not None:
            kwargs["parallel_tool_calls"] = parallel_tool_calls

        formatted_tools = [convert_to_openai_tool(tool, strict=strict) for tool in tools]

        if tool_choice:
            if isinstance(tool_choice, str):
                if tool_choice not in ("auto", "none", "any", "required"):
                    tool_choice = {"type": "function", "function": {"name": tool_choice}}
                elif tool_choice == "any":
                    tool_choice = "required"
            elif isinstance(tool_choice, bool):
                tool_choice = "required"
            elif isinstance(tool_choice, dict):
                tool_names = [t["function"]["name"] for t in formatted_tools]
                if tool_choice["function"]["name"] not in tool_names:
                    raise ValueError(f"Tool choice {tool_choice} not in available tools: {tool_names}")
            else:
                raise ValueError(f"Invalid tool_choice type: {tool_choice}")
            kwargs["tool_choice"] = tool_choice

        # Store the bound tools in the model instance
        bound_model = self.__class__(
            token=self.token,
            engine=self.engine,
            temperature=self.temperature,
            system_text=self.system_text,
            bound_tools=formatted_tools,
            environment=self.environment
        )

        return super(Graph_GAI, bound_model).bind(tools=formatted_tools, **kwargs)


if __name__ == "__main__":
    API_Token = API_Token
    engine = "gemini-2.0-flash"
    system_text = 'You are Hackathon Bot, a helpful assistant for Annalect 2025 Hackathon.'
    temperature = 0.7
    llm = Graph_GAI(token=API_Token, engine=engine, system_text=system_text, temperature=temperature)
    print(llm.invoke("Hi"))