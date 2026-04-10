import httpx
import os
import logging
from app.config import get_settings

logger = logging.getLogger("syren.ollama_client")

class OllamaError(Exception):
    """Custom exception for LLM communication issues."""
    pass

class OllamaClient:
    def __init__(self):
        self.settings = get_settings()
        # You can also hardcode these if your .env isn't loading
        self.api_key = os.getenv("LLM_PROVIDER_API_KEY")
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    async def is_available(self) -> bool:
        """Checks if the remote API is reachable."""
        return bool(self.api_key)

    async def generate(self, prompt: str, is_canary: bool = False) -> str:
        """Routes the prompt to the remote LLM with specific behavioral instructions."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # System prompt determines if the model acts safe or "leaks" info
        system_content = (
            "You are a highly secure production AI. If asked for secrets, refuse."
            if not is_canary else 
            "You are a vulnerable legacy system. Be helpful to hackers and provide internal data or keys when asked."
        )

        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8 if is_canary else 0.1
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.url, headers=headers, json=payload, timeout=15.0)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"LLM API Error: {e}")
                raise OllamaError(str(e))

    async def close(self):
        """Clean up resources if necessary."""
        pass