import sys
import os
import time
from dotenv import load_dotenv
from typing import Literal, get_args
import litellm
from langchain_openai import ChatOpenAI

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.Omni_Helper.utils.logging_config import get_logger
from app.Omni_Helper.utils.constant import OmniAPIEnvironment
from app.Omni_Helper.utils.constant import Model_Config

# Load environment variables from .env file
load_dotenv()
API_Token = os.getenv("API_Token")


class Chatbot:
    """
    Class to create a chatbot using Omni API
    - Access token to the Conversation endpoint is needed.
    - system_text is the set of instruction given to the bot using register_agent
    
    Args:
        token (str): Access token for the Omni API Conversation endpoint
        engine (Model_Config.ENGINE_MODELS): The LLM model to use for the chatbot
        temperature (float): Controls randomness of model output (0.0-2.0)
        environment (str): Environment to use ('dev' or 'prod'). Defaults to 'dev'
        max_token (int): Maximum tokens for the response. Defaults to 8192
        reasoning (Literal['low', 'medium', 'high']): Reasoning effort level for reasoning models. Defaults to 'low'
    """
    def __init__(
        self,
        token: str,
        engine: str,
        temperature: float,
        environment: str = 'dev',
        max_token: int = 8192,
        reasoning: Literal['low', 'medium', 'high'] = 'low',
        timeout: int = 30
    ):
        self.token = token
        self.environment = environment
        self.litellm_url = OmniAPIEnvironment(environment).litellm_url
        self.system_text = "You are an all-purpose chatbot."
        self.engine = engine
        self.temperature = temperature
        self.max_token = max_token
        self.timeout = timeout
        self.token_usage = {"Model": engine, 'Input': 0, 'Output': 0}

        # Validate reasoning and engine
        if reasoning not in ['low', 'medium', 'high']:
            raise ValueError(f"reasoning must be one of ['low', 'medium', 'high'], got '{reasoning}'")
        
        # Set reasoning effort only if engine is a reasoning model
        if any(x in engine for x in Model_Config.REASONING_MODELS):
            self.reasoning_effort = reasoning if 'chat' not in engine.lower() else None
            self.temperature = Model_Config.set_temperature(engine, self.temperature)
        else:
            self.reasoning_effort = None

        # Create LLM/model triplets for retry fallback
        model_list = [
            (engine, 2, self.reasoning_effort),
            (os.getenv("model_1", "gpt-4.1-mini"), 1, None),
            (os.getenv("model_2", "anthropic-claude-sonnet-4"), 1, None),
        ]
        self._llms = [self._create_llm(m, max_retries=r, reasoning_effort=e) for m, r, e in model_list]
        self._models = [m for m, _, _ in model_list]

    def _create_llm(self, model: str, max_retries: int = 2, reasoning_effort: str = None) -> ChatOpenAI:
        """Helper method to create ChatOpenAI instances with common configuration."""
        return ChatOpenAI(
            model=model,
            openai_api_key=self.token,
            base_url=self.litellm_url,
            temperature=self.temperature,
            max_tokens=self.max_token,
            timeout=self.timeout,
            max_retries=max_retries,
            reasoning_effort=reasoning_effort,
        )

    def register_agent(self, instructions):
        """Set the system instructions for the chatbot."""
        self.system_text = instructions
        return self

    def ask(self, prompt: str, chat_history: list[dict] = None, visual_message: dict = None) -> str:
        """
        Send the constructed prompt using question, chat history, and retrieved context, to the LLM using
        history format: [ {"role": ..., "content": ...} ]
        
        Args:
            prompt (str): The user's question or message to send to the chatbot
            chat_history (list[dict]): Previous conversation messages in role/content format. Defaults to None
            visual_message (dict): Visual content message (images, etc.) to include. Defaults to None
            
        Returns:
            str: The chatbot's response to the prompt
        """
        chat_history = chat_history or []
        messages = [{'role': 'system', 'content': self.system_text}] + chat_history + [{'role': 'user', 'content': prompt}]
        messages = messages + [visual_message] if visual_message else messages
        for i, (llm, model) in enumerate(zip(self._llms, self._models)):
            try:
                response = llm.invoke(messages)
                # Token usage accounting (OpenAI format)
                if hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
                    tu = response.response_metadata['token_usage']
                    self.token_usage['Output'] += tu.get('completion_tokens', 0)
                    self.token_usage['Input'] += tu.get('prompt_tokens', 0)
                return getattr(response, 'content', str(response))
            except Exception as e:
                get_logger().error(f"Error in ask function (model {model}): {e}")
                if i < 2:
                    get_logger().warning(f"Try {i+1} --> Model change to --> {self._models[i+1]}")
                    time.sleep(10)
        return (
            "Unable to provide an answer. Possible reasons could be: \n"
            "- Excess the allowed tokens per minute count.\n"
            "- The failure of the Omni API Endpoint.\n"
            "- Existence of inappropriate words or phrases\n"
        )



# Example for calling the bot directly
if __name__ == "__main__":
    API_Token = API_Token
    engine = "gpt-4o-mini"
    system_text = 'You are Hackathon Bot, an helpful assistant for Annalect 2025 Hackathon.'
    temperature = 0.7
    bot = Chatbot(token=API_Token, engine=engine, temperature=temperature)
    bot.register_agent(instructions=system_text)
    print(bot.ask("Who are you?"))