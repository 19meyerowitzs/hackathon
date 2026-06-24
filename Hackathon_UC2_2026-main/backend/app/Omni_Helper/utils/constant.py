"""
Use dev environment or prod environment based on the environment variable.
This module defines constants for the Omni API environment and the base URL for the API.
"""

from typing_extensions import Literal


class OmniAPIEnvironment:
    DEV = "dev"
    PROD = "prod"

    litellm_url = None
    api_url = None
    api_url_v1 = None
    thread_url = None
    old_thread_url = None
    semantic_url_v1 = None
    semantic_url_v0 = None
    documents_url = None
    documents_url_metadata = None

    def __init__(self, environment: str = "dev"):
        self.environment = environment

        if self.environment == self.DEV:
            self.litellm_url = "https://devlitellm.annalect.com"
            self.api_url = "https://devgai-conversation-api.annalect.com/api/conversation"
            self.api_url_v1 = "https://devgai-conversation-api.annalect.com/v1/api/conversations"
            self.thread_url = "https://devlitellm.annalect.com/v1/threads"
            self.old_thread_url = "https://devgai-conversation-api.annalect.com/api/thread"
            self.semantic_url_v0 = "https://devembedding-api.annalect.com/api/embeddings"
            self.semantic_url_v1 = "https://devsemantic-service-api.annalect.com/tokens/create"
            self.documents_url = f"https://devsemantic-service-api.annalect.com/documents/"
            self.documents_url_metadata = f"https://devsemantic-service-api.annalect.com/metadata"
        elif self.environment == self.PROD:
            self.litellm_url = "https://litellm.annalect.com"
            self.api_url = "https://gai-conversation-api.annalect.com/api/conversation"
            self.api_url_v1 = "https://gai-conversation-api.annalect.com/v1/api/conversations"
            self.thread_url = "https://litellm.annalect.com/v1/threads"
            self.old_thread_url = "https://gai-conversation-api.annalect.com/api/thread"
            self.semantic_url_v0 = "https://embedding-api.annalect.com/api/embeddings"
            self.semantic_url_v1 = "https://semantic-service-api.annalect.com/tokens/create"
            self.documents_url = f"https://semantic-service-api.annalect.com/documents/"
            self.documents_url_metadata = f"https://semantic-service-api.annalect.com/metadata"
        else:
            raise ValueError(f"Invalid environment: {self.environment}. Use 'dev' or 'prod'.")

        # print(f"OmniAPIEnvironment initialized with environment: {self.environment}")  


class Model_Config:
    
    ENGINE_MODELS = Literal[
        # OpenAI Models
        'gpt-5', 'gpt-5-nano', 'gpt-5-mini', 'gpt-5-chat',
        'gpt-4.1', 'gpt-4.1-mini', 'gpt-4.1-nano',
        'gpt-4o', 'gpt-4o-mini', 'o4-mini', 'o3', 'o3-mini',
        # Anthropic Models
        'anthropic-claude-sonnet-4', 'anthropic.claude-sonnet-4-20250514-v1:0',
        'anthropic.claude-3-7-sonnet-20250219-v1:0',
        # Google Models
        'gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.5-flash-lite',
        'gemini-2.0-flash', 'gemini-2.0-flash-lite',
        # Meta Models
        'meta.llama3-2-1b-instruct-v1:0','meta.llama3-2-3b-instruct-v1:0', 
        'meta.llama3-2-11b-instruct-v1:0','meta.llama3-2-90b-instruct-v1:0'
    ]
    REASONING_MODELS = ['gpt-5', 'o4', 'o3', 'gemini-2.5']
    
    def set_temperature(model, temperature):
        if any(x in model for x in ['gpt-5', 'o4', 'o3']):
            return 1.0
        else: 
            return temperature