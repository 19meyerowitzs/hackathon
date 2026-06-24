import requests
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.Omni_Helper.utils.constant import OmniAPIEnvironment
from app.Omni_Helper.utils.logging_config import logger


class Embeddings_Calculator:

    def __init__(self, token, environment = "dev"):
        self.token = token
        env = OmniAPIEnvironment(environment)
        self.api_url = env.semantic_url_v0
        self.api_url_v1 = env.semantic_url_v1

    def get_v0(self, text: str) -> list:
        """
        Call the omni API to create embeddings
        """
        logger.warning(f"Going to be Deprecated and replaced by https://omni-api.annalect.com/reference/create_embeddings_embeddings_create_post with new semantic key")
        url = self.api_url
        payload = {"text": text, "engine": "text-embedding-ada-002"}
        headers = {
            "accept": "application/json",
            "X-Api-Key": self.token,
            "content-type": "application/json",
        }
        for i in range(4):
            response = requests.post(url, json=payload, headers=headers)
            try:
                return response.json()["embeddings"]
            except:
                logger.error(f"Error in getting the Embeddings: {response.text}")
                time.sleep(10 * (i + 2))
        return []
    
    def authentication(self):
        try:
            url = self.api_url_v1
            payload = {
                "client_layout_id": "default",
                "user_id": "default"
            }
            headers = {
                "accept": "application/json",
                "x-api-key": self.token,
                "content-type": "application/json"
            }
            response = requests.post(url, json=payload, headers=headers)
            self.bearer_token = f'Bearer {response.json()["token"]}'
            # logger.info(self.bearer_token)
        except Exception as e:
            logger.error(f"Error in authentication: {e}")

    def get_v1(self, text: str, model="text-embedding-3-small") -> list:
        """
        Call the new omni API to create embeddings
        """
        self.authentication()
        url = "https://devsemantic-service-api.annalect.com/embeddings/create"
        payload = {
            "model_name": model,
            "text": text
        }
        headers = {
            "accept": "application/json",
            "authentication": self.bearer_token,
            "content-type": "application/json"
        }
        for i in range(4):
            response = requests.post(url, json=payload, headers=headers)
            try:
                return response.json()["embeddings"]
            except:
                logger.error(f"Error in getting the Embeddings: {response.text}")
                time.sleep(10 * (i + 2))
        return []
