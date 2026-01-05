"""GGUF backend using llama-cpp-python."""
from typing import Generator
from pathlib import Path

from ..core.inference import InferenceClient
from ..core.registry import ModelEntry


class GGUFClient(InferenceClient):
    """GGUF inference backend using llama.cpp."""

    def __init__(self, entry: ModelEntry):
        """
        Initialize GGUF client.

        Args:
            entry: Model registry entry
        """
        super().__init__(entry)
        self._llama = None

    def _get_llama(self):
        """Lazy load llama.cpp model."""
        if self._llama is None:
            try:
                from llama_cpp import Llama
            except ImportError:
                raise RuntimeError(
                    "llama-cpp-python not installed. "
                    "Install with: pip install llama-cpp-python"
                )

            # Load model with Metal support for Apple Silicon
            self._llama = Llama(
                model_path=str(self.entry.path),
                n_ctx=self.entry.context_length,
                n_gpu_layers=-1,  # Use all GPU layers (Metal)
                verbose=False
            )

        return self._llama

    def complete(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate completion.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional llama.cpp parameters

        Returns:
            Generated text
        """
        llama = self._get_llama()

        output = llama(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=kwargs.get("stop", []),
            echo=False
        )

        return output["choices"][0]["text"]

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
        llama = self._get_llama()

        stream = llama(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=kwargs.get("stop", []),
            stream=True
        )

        for output in stream:
            chunk = output["choices"][0]["text"]
            if chunk:
                yield chunk

    def chat(
        self,
        messages: list[dict],
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Generated response
        """
        llama = self._get_llama()

        # Try to use llama.cpp's chat completion if available
        try:
            output = llama.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return output["choices"][0]["message"]["content"]
        except (AttributeError, KeyError):
            # Fallback: format manually and use completion
            prompt = self._format_chat(messages)
            return self.complete(prompt, max_tokens, temperature, **kwargs)

    def _format_chat(self, messages: list[dict]) -> str:
        """
        Format messages to prompt string.

        Args:
            messages: List of message dicts

        Returns:
            Formatted prompt
        """
        template = self.entry.chat_template or "chatml"

        if template == "chatml":
            formatted = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                formatted.append(f"<|im_start|>{role}\n{content}<|im_end|>")
            formatted.append("<|im_start|>assistant\n")
            return "\n".join(formatted)

        else:
            # Simple format
            formatted = []
            for msg in messages:
                role = msg.get("role", "user").capitalize()
                content = msg.get("content", "")
                formatted.append(f"{role}: {content}")
            formatted.append("Assistant:")
            return "\n".join(formatted)

    def __del__(self):
        """Clean up model on deletion."""
        if self._llama is not None:
            del self._llama
            self._llama = None
