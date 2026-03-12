import httpx
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        pass

    @abstractmethod
    async def reason(
        self,
        messages: List[Dict[str, str]],
        model: str,
    ) -> str:
        """For thinking/reasoning mode (e.g., deepseek-reasoner)."""
        pass


class DeepSeekProvider(LLMProvider):
    """
    DeepSeek API provider.
    Uses OpenAI-compatible format at https://api.deepseek.com/chat/completions.
    - deepseek-chat: Non-thinking mode (DeepSeek-V3.2, 128K context)
    - deepseek-reasoner: Thinking mode with reasoning_content in response
    """

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def reason(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-reasoner",
    ) -> str:
        """
        Use DeepSeek reasoning mode. The response includes reasoning_content
        (chain-of-thought) and content (final answer).
        """
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            message = data["choices"][0]["message"]
            # deepseek-reasoner returns reasoning_content alongside content
            reasoning = message.get("reasoning_content", "")
            content = message.get("content", "")
            logger.info(f"Reasoning tokens used: {len(reasoning.split())}")
            return content


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def reason(
        self,
        messages: List[Dict[str, str]],
        model: str = "o1",
    ) -> str:
        return await self.chat(messages, model=model, temperature=1.0)


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-sonnet-4-6",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        # Convert messages to Anthropic format
        system_msg = ""
        api_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                api_messages.append(msg)

        async with httpx.AsyncClient(timeout=120) as client:
            body: Dict[str, Any] = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": api_messages,
            }
            if system_msg:
                body["system"] = system_msg

            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                },
                json=body,
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

    async def reason(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-opus-4-6",
    ) -> str:
        return await self.chat(messages, model=model, temperature=1.0)


def get_llm_provider(provider_name: str, api_key: str, base_url: Optional[str] = None) -> LLMProvider:
    """Factory function to get the appropriate LLM provider."""
    providers = {
        "deepseek": lambda: DeepSeekProvider(
            api_key=api_key,
            base_url=base_url or "https://api.deepseek.com",
        ),
        "openai": lambda: OpenAIProvider(
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1",
        ),
        "anthropic": lambda: AnthropicProvider(
            api_key=api_key,
            base_url=base_url or "https://api.anthropic.com/v1",
        ),
    }

    factory = providers.get(provider_name)
    if not factory:
        raise ValueError(f"Unknown LLM provider: {provider_name}. Supported: {list(providers.keys())}")
    return factory()
