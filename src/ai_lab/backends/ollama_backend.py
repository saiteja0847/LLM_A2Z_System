"""Ollama backend using HTTP API."""
import httpx
from typing import Generator
import json

from ..core.inference import InferenceClient
from ..core.registry import ModelEntry


class OllamaClient(InferenceClient):
    """Ollama inference backend."""

    def __init__(self, entry: ModelEntry):
        """
        Initialize Ollama client.

        Args:
            entry: Model registry entry
        """
        super().__init__(entry)
        self.base_url = "http://localhost:11434"
        self.model_name = entry.ollama_name

    def complete(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate completion using Ollama.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate (not used by Ollama)
            temperature: Sampling temperature
            **kwargs: Additional Ollama parameters

        Returns:
            Generated text
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        try:
            response = httpx.post(url, json=payload, timeout=300.0)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama request failed: {e}")
        except httpx.TimeoutException:
            raise RuntimeError("Ollama request timed out after 5 minutes")

    def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Stream completion tokens from Ollama.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Yields:
            Generated token strings
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        try:
            with httpx.stream("POST", url, json=payload, timeout=300.0) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.strip():
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done", False):
                            break
        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama streaming failed: {e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse Ollama response: {e}")

    def chat(
        self,
        messages: list[dict],
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate chat completion using Ollama chat API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Generated response
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        try:
            response = httpx.post(url, json=payload, timeout=300.0)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama chat failed: {e}")
        except httpx.TimeoutException:
            raise RuntimeError("Ollama chat timed out after 5 minutes")

    def check_available(self) -> bool:
        """
        Check if Ollama is running and model is available.

        Returns:
            True if available, False otherwise
        """
        try:
            # Check if Ollama is running
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            response.raise_for_status()

            # Check if our model is in the list
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            return self.model_name in models

        except (httpx.HTTPError, httpx.TimeoutException):
            return False
