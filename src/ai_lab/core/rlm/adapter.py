"""Adapter to make InferenceClient compatible with RLM BaseLM."""
import asyncio
from typing import Any

from ..inference import InferenceClient

# Lazy import RLM library only when actually needed
try:
    from rlm.clients.base_lm import BaseLM
    from rlm.core.types import UsageSummary, ModelUsageSummary
    RLM_AVAILABLE = True
except ImportError:
    # RLM not installed - will be raised when trying to use adapter
    RLM_AVAILABLE = False
    BaseLM = object  # Dummy base class


class InferenceClientAdapter(BaseLM):
    """
    Adapter that wraps our InferenceClient to work with RLM.

    RLM expects clients inheriting from BaseLM. This adapter
    bridges our InferenceClient interface to RLM's BaseLM.

    This allows ANY InferenceClient (MLXClient, RemoteClient, etc.)
    to work seamlessly with RLM without modification.
    """

    def __init__(self, client: InferenceClient, model_name: str, **kwargs):
        """
        Initialize adapter.

        Args:
            client: Our InferenceClient (MLXClient, RemoteClient, etc.)
            model_name: Model identifier for RLM

        Raises:
            ImportError: If RLM library is not installed
        """
        if not RLM_AVAILABLE:
            raise ImportError(
                "RLM library not installed. Install with:\n"
                "  pip install git+https://github.com/alexzhang13/rlm.git"
            )

        # Import here that we know RLM is available
        from rlm.core.types import ModelUsageSummary

        super().__init__(model_name, **kwargs)
        self.client = client

        # Track usage statistics
        self._usage = ModelUsageSummary(
            total_calls=0,
            total_input_tokens=0,
            total_output_tokens=0,
        )

    def completion(self, prompt: str | dict[str, Any]) -> str:
        """
        Synchronous completion using our client.

        Args:
            prompt: Prompt string or dict with 'messages' key

        Returns:
            Generated text
        """
        self._usage.total_calls += 1

        # Handle both string prompts and chat message dicts
        if isinstance(prompt, dict):
            messages = prompt.get("messages", [])
            if not messages:
                # Fallback to string
                return self.client.complete(str(prompt))
            return self.client.chat(messages)
        else:
            return self.client.complete(prompt)

    async def acompletion(self, prompt: str | dict[str, Any]) -> str:
        """
        Async completion (RLM uses this for batched calls).

        Args:
            prompt: Prompt string or dict

        Returns:
            Generated text
        """
        # Run sync client in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.completion,
            prompt
        )

    def get_usage_summary(self):
        """Get aggregated usage statistics."""
        from rlm.core.types import UsageSummary
        return UsageSummary(
            model_usage_summaries={
                self.model_name: self._usage
            }
        )

    def get_last_usage(self):
        """Get last call usage (same as total for now)."""
        return self.get_usage_summary()
