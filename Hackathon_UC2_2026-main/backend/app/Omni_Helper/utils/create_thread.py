import sys
import os
import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.Omni_Helper.utils.constant import OmniAPIEnvironment
from app.Omni_Helper.utils.logging_config import logger

# Load environment variables from .env file
load_dotenv()
API_Token = os.getenv("API_Token")


def create_thread_id(
        token,
        user_id: str,  # User's Omni UUID - must be from the same Omni environment as 'environment'
        client_id: str = "default",
        label: str = "Test Thread",
        environment = 'dev'):
    """
    Create new Omni thread id to assign to agents/conversation
    """
    try:
        env = OmniAPIEnvironment(environment)
        thread_url = env.thread_url
        headers = {
            "accept": "application/json",
            "X-API-KEY": token,
            "Content-Type": "application/json",
        }
        data = {
            "label": label,
            "metadata": {},
            "client_id": "default",
            "user_id": user_id,
        }

        response = requests.post(thread_url, headers=headers, json=data)
        return response.json()['data']['thread_id']
    except Exception as e:
        logger.error(f"Error in creating thread {e}")


if __name__ == "__main__":
    print(create_thread_id(API_Token, user_id=os.environ["UUID"]))