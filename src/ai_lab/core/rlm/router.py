"""RLM Router for recursive inference."""
from typing import Optional

from .config import RLMConfig
from .adapter import InferenceClientAdapter
from ..registry import Registry
from ..inference import get_inference_client


class RLMRouter:
    """
    Routes requests through RLM using any registered model.

    This is a separate routing layer that adds recursive
    inference capabilities to any InferenceClient.

    The router wraps any existing InferenceClient (MLXClient,
    RemoteClient, OllamaClient, etc.) with RLM capabilities,
    allowing it to handle near-infinite context through
    recursive decomposition and sub-calls.

    Example:
        # Use MLX model with RLM
        router = RLMRouter("qwen3-4b-instruct")
        result = router.complete(large_document)

        # Use remote API model with RLM
        router = RLMRouter("gpt-4")
        result = router.complete(huge_context)
    """

    def __init__(
        self,
        model_name: str,
        config: Optional[RLMConfig] = None,
        registry: Optional[Registry] = None,
    ):
        """
        Initialize RLM Router.

        Args:
            model_name: Name of model to use from registry
            config: RLM configuration (uses defaults if None)
            registry: Model registry (creates default if None)

        Raises:
            ValueError: If model not found in registry
            ImportError: If RLM library not installed
        """
        self.registry = registry or Registry()
        self.model_entry = self.registry.get(model_name)
        self.config = config or RLMConfig(model_name=model_name)

        # Get base inference client
        self.base_client = get_inference_client(self.model_entry)

        # Initialize RLM with our adapter
        self._init_rlm()

    def _init_rlm(self):
        """Initialize RLM library with our adapter."""
        try:
            from rlm import RLM
            from rlm.logger import RLMLogger
            from contextlib import contextmanager
        except ImportError:
            raise ImportError(
                "RLM library not installed. Install with:\n"
                "  pip install git+https://github.com/alexzhang13/rlm.git\n"
                "Or add to requirements.txt and install."
            )

        # Create adapter
        self.adapter = InferenceClientAdapter(
            client=self.base_client,
            model_name=self.model_entry.name,
        )

        # Set up logger if configured
        logger = None
        if self.config.log_dir:
            logger = RLMLogger(log_dir=self.config.log_dir)

        # Store config for use in spawn
        self._rlm_config_dict = {
            "environment": self.config.environment_type,
            "environment_kwargs": self.config.environment_kwargs or {},
        }

        # Initialize RLM with a simpler approach - use socket-based LM handler
        # RLM expects to communicate with LM via a socket server
        self.rlm = RLM(
            backend="socket",  # Use socket backend
            backend_kwargs={
                "model_name": self.model_entry.name,
            },
            environment=self.config.environment_type,
            environment_kwargs=self.config.environment_kwargs,
            max_depth=self.config.max_depth,
            max_iterations=self.config.max_iterations,
            custom_system_prompt=self.config.custom_system_prompt,
            logger=logger,
            verbose=self.config.verbose,
        )

    def complete(
        self,
        prompt: str,
        root_prompt: Optional[str] = None,
    ) -> str:
        """
        Run RLM completion on potentially huge context.

        This method can handle inputs that far exceed the model's
        context window by recursively chunking and processing.

        Args:
            prompt: Context/document to process (can be millions of chars)
            root_prompt: Optional task/question about the context

        Returns:
            Final answer after recursive processing

        Example:
            >>> router = RLMRouter("qwen3-4b-instruct")
            >>> doc = "..."  # 500K character document
            >>> result = router.complete(
            ...     prompt=doc,
            ...     root_prompt="Summarize the key findings"
            ... )
            >>> print(result)
        """
        result = self.rlm.completion(
            prompt=prompt,
            root_prompt=root_prompt,
        )
        return result.response

    def chat(self, messages: list[dict]) -> str:
        """
        Run RLM chat completion.

        Args:
            messages: List of chat messages with 'role' and 'content'

        Returns:
            Response text

        Example:
            >>> router = RLMRouter("gpt-4")
            >>> messages = [
            ...     {"role": "user", "content": "Analyze this data..."}
            ... ]
            >>> response = router.chat(messages)
        """
        # Convert to prompt format
        prompt = self._format_chat(messages)
        return self.complete(prompt)

    def _format_chat(self, messages: list[dict]) -> str:
        """Format chat messages as prompt string."""
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            parts.append(f"{role}: {content}")
        return "\n\n".join(parts)

    def get_usage_summary(self):
        """Get usage statistics from RLM run."""
        return self.adapter.get_usage_summary()
