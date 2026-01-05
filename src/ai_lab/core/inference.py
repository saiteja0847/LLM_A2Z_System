"""Backend-agnostic inference router."""
from abc import ABC, abstractmethod
from typing import Generator, Optional, Dict, Any
from ..core.registry import ModelEntry, ModelBackend


class InferenceClient(ABC):
    """Abstract base for all inference backends."""

    def __init__(self, entry: ModelEntry):
        """
        Initialize inference client.

        Args:
            entry: Model registry entry
        """
        self.entry = entry

    @abstractmethod
    def complete(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate a completion from a prompt.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Backend-specific parameters

        Returns:
            Generated text
        """
        pass

    @abstractmethod
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
            **kwargs: Backend-specific parameters

        Yields:
            Token strings
        """
        pass

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate a chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Backend-specific parameters

        Returns:
            Generated response
        """
        pass


def get_inference_client(entry: ModelEntry) -> InferenceClient:
    """
    Factory to get the right client for a model's backend.

    Args:
        entry: Model registry entry

    Returns:
        Appropriate InferenceClient implementation

    Raises:
        ValueError: If backend is not supported
    """
    # Import backends lazily to avoid circular imports
    # and missing dependencies
    clients: Dict[ModelBackend, Any] = {}

    try:
        if entry.backend == ModelBackend.MLX:
            from ..backends.mlx_backend import MLXClient
            clients[ModelBackend.MLX] = MLXClient
    except ImportError:
        pass

    try:
        if entry.backend == ModelBackend.GGUF:
            from ..backends.gguf_backend import GGUFClient
            clients[ModelBackend.GGUF] = GGUFClient
    except ImportError:
        pass

    try:
        if entry.backend == ModelBackend.OLLAMA:
            from ..backends.ollama_backend import OllamaClient
            clients[ModelBackend.OLLAMA] = OllamaClient
    except ImportError:
        pass

    try:
        if entry.backend == ModelBackend.REMOTE:
            from ..backends.remote_backend import RemoteClient
            clients[ModelBackend.REMOTE] = RemoteClient
    except ImportError:
        pass

    client_class = clients.get(entry.backend)
    if not client_class:
        raise ValueError(
            f"Backend '{entry.backend}' is not supported or not installed. "
            f"Available backends: {list(clients.keys())}"
        )

    return client_class(entry)
