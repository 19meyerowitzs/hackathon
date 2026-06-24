import os
import sys
from typing import Any, List, Mapping, Optional
from pydantic import Field, BaseModel
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import Generation, LLMResult
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.Omni_Helper.utils.chatbot import Chatbot

# Load environment variables from .env file
load_dotenv(dotenv_path="../.env")
API_Token = os.getenv("API_Token")


class GAI(LLM):
    """
    Custom langchain llm for Omni API.
    There are only two required things that a custom LLM needs to implement:

    Args:
        token (str): API token for authentication.
        engine (str): Model engine to use.
        temperature (float): Sampling temperature.
        system_text (str): System prompt.
        web_search (bool): Only available for Gemini models

    Raises: ValueError: In case stop words are included.

    Returns: _type_: output from Omni API.
    """
    token: str = Field(..., description="API token for authentication")
    engine: str = Field(..., description="The model engine to use")
    temperature: float = Field(default=0.7, description="Temperature of the model")
    system_text: str = Field(default="You are a helpful assistant.", description="System prompt for the chatbot")
    web_search: bool = Field(default=False, description="Yo use web search, available for Gemini models")
    bot: Chatbot = None
    environment: str = Field(default="dev", description="Environment for the chatbot")
    current_thread_id: Optional[str] = Field(default=None, description="Current thread ID for conversation continuity")

    def __init__(self, **data):
        """Initialize the LLM and create the Chatbot instance."""
        super().__init__(**data)
        self.bot = Chatbot(
            token=self.token,
            engine=self.engine,
            temperature=self.temperature,
            environment=self.environment,
            web_search=self.web_search
        )
        self.bot.register_agent(self.system_text)

    # property that returns a string. Used for logging purposes only.
    @property
    def _llm_type(self) -> str:
        return f"gai_omni_api with {self.engine}"

    # method that takes in a string, some optional stop words, and returns a string.
    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        response, returned_thread_id = self.bot.ask(prompt, thread_id=self.current_thread_id)
        self.current_thread_id = returned_thread_id
        if stop:
            for s in stop:
                if s in response:
                    response = response.split(s)[0]
        return response

    def _generate(
            self,
            prompts: List[str],
            stop: Optional[List[str]] = None,
            **kwargs: Any,
    ) -> LLMResult:
        generations = [
            [Generation(text=self._call(prompt, stop=stop, **kwargs))]
            for prompt in prompts
        ]
        return LLMResult(generations=generations)

    def set_thread_id(self, thread_id: str):
        """Set the thread ID for conversation continuity."""
        self.current_thread_id = thread_id

    def get_thread_id(self) -> Optional[str]:
        """Get the current thread ID."""
        return self.current_thread_id

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {"system_text": self.system_text, "bot": self.bot}


if __name__ == "__main__":
    hackathon_key = API_Token
    engine = "gemini-2.0-flash"
    system_text = 'You are Hackathon Bot, a helpful assistant for Annalect 2025 Hackathon.'
    temperature = 0.7

    llm = GAI(token=hackathon_key, engine=engine, system_text=system_text, temperature=temperature)
    print(llm.invoke("Hi"))