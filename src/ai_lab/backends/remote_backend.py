"""Remote API backend for OpenAI, Anthropic, etc."""
import httpx
import os
from typing import Generator
import json

from ..core.inference import InferenceClient
from ..core.registry import ModelEntry


class RemoteClient(InferenceClient):
    """Remote API backend for cloud LLM services."""

    def __init__(self, entry: ModelEntry):
        """
        Initialize remote API client.

        Args:
            entry: Model registry entry
        """
        super().__init__(entry)
        self.api_base = entry.api_base
        self.model_name = entry.api_model

        # Get API key from environment if specified
        if entry.api_key_env:
            self.api_key = os.getenv(entry.api_key_env)
            if not self.api_key:
                raise ValueError(
                    f"API key environment variable '{entry.api_key_env}' not set"
                )
        else:
            self.api_key = None

    def _get_headers(self) -> dict:
        """Get HTTP headers including auth."""
        headers = {"Content-Type": "application/json"}

        if self.api_key:
            # OpenAI-style auth
            if "openai" in self.api_base.lower():
                headers["Authorization"] = f"Bearer {self.api_key}"
            # Anthropic-style auth
            elif "anthropic" in self.api_base.lower():
                headers["x-api-key"] = self.api_key
                headers["anthropic-version"] = "2023-06-01"
            # Generic bearer token
            else:
                headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    def complete(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate completion using remote API.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional API parameters

        Returns:
            Generated text
        """
        # Convert to chat format for most APIs
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, max_tokens, temperature, **kwargs)

    def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Stream completion tokens.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Yields:
            Generated token strings
        """
        # OpenAI-compatible streaming
        url = f"{self.api_base}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }

        try:
            with httpx.stream(
                "POST",
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=300.0
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        if data_str.strip() == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPError as e:
            raise RuntimeError(f"Remote API streaming failed: {e}")

    def chat(
        self,
        messages: list[dict],
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate chat completion using remote API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Generated response
        """
        # Detect API type and format request accordingly
        if "anthropic" in self.api_base.lower():
            return self._anthropic_chat(messages, max_tokens, temperature, **kwargs)
        else:
            # OpenAI-compatible format (default)
            return self._openai_chat(messages, max_tokens, temperature, **kwargs)

    def _openai_chat(
        self,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> str:
        """OpenAI-compatible chat completion."""
        url = f"{self.api_base}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        payload.update(kwargs)

        try:
            response = httpx.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=300.0
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]

        except httpx.HTTPError as e:
            raise RuntimeError(f"OpenAI API request failed: {e}")
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected API response format: {e}")

    def _anthropic_chat(
        self,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> str:
        """Anthropic-specific chat completion."""
        url = f"{self.api_base}/messages"

        # Extract system message if present
        system = None
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                chat_messages.append(msg)

        payload = {
            "model": self.model_name,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system:
            payload["system"] = system

        payload.update(kwargs)

        try:
            response = httpx.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=300.0
            )
            response.raise_for_status()
            result = response.json()
            return result["content"][0]["text"]

        except httpx.HTTPError as e:
            raise RuntimeError(f"Anthropic API request failed: {e}")
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected API response format: {e}")
