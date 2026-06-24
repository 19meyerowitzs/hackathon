"""
Define the payload schema based on the model and the API route
"""
import os
import dotenv
dotenv.load_dotenv()

def v1(engine, temperature, system_text, prompt, thread_id, web=False):
    """
    Web search his only functional if the model is Gemini
    """
    if 'gpt-4' in engine:
        payload = {
            "user_id": os.environ.get("UUID", "default"),
            "model": engine,
            "model_params": {
                "model": engine,
                "temperature": temperature,
                "frequency_penalty": 0.5,
                "max_tokens": 8192,
                "messages": [
                    {"role": "system", "content": system_text},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
            },
        }
    elif any(x in engine for x in ["o4", "o3", "gpt-5"]):
        payload = {
            "user_id": os.environ.get("UUID", "default"),
            "model": engine,
            "model_params": {
                "model": engine,
                "temperature": 1,
                "max_completion_tokens": 8192,
                "messages": [
                    {"role": "system", "content": system_text},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
            },
        }
    elif 'claude' in engine:
        payload = {
            "user_id": os.environ.get("UUID", "default"),
            "model": engine,
            "model_params": {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 8192,
                "system": system_text,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            },
        }
    elif 'gemini' in engine:
        payload = {
            "metadata": {"web_search": web},
            "client_id": "default",
            "user_id": os.environ.get("UUID", "default"),
            "model": engine,
            "model_params": {
                "system_instruction": {
                    "parts": [
                        {
                            "text": system_text
                        }
                    ]
                },
                "contents": [
                    {
                        "role": "user",
                        "parts": prompt if isinstance(prompt, list) else [prompt]
                    }],
                "generation_config": {
                    "temperature": temperature,
                }
            },
        }
    else:
        raise ValueError(f"Engine {engine} not supported")
    if thread_id:
        payload["thread_id"] = thread_id
    return payload


def v0(engine, temperature, system_text, prompt):
    payload = {
        "config": {
            "engine": engine,
            "temperature": temperature,
            "frequency_penalty": 0.5,
            "max_tokens": 8192,
        },
        "prompt": prompt,
        "system_text": system_text,
    }
    return payload
