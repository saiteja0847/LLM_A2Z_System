"""OpenAI-backed RLM Router for full RLM capabilities."""
from typing import Optional
from rlm import RLM
from rlm.logger import RLMLogger

from .config import RLMConfig
from ..registry import Registry


class OpenAIRLMRouter:
    """
    RLM Router using your OpenAI-compatible API for full RLM capabilities.

    This uses the official RLM library by pointing it to your AI Lab server's
    OpenAI-compatible endpoints. This gives you access to advanced RLM features
    like code execution in REPL environments and sophisticated multi-step reasoning.

    Use this when:
    • You need code execution capabilities
    • Processing very large documents (>100K characters)
    • Complex multi-step analysis tasks
    • Need RLM's advanced recursive algorithms

    For simpler tasks, use SimpleRLMRouter instead.

    Example:
        # Make sure API server is running first
        # python -m uvicorn ai_lab.api.app:app

        router = OpenAIRLMRouter("qwen-1-5b")
        result = router.complete(
            prompt=open("huge_document.txt").read(),
            root_prompt="Extract all citations and format them as JSON"
        )
        print(result)
    """

    def __init__(
        self,
        model_name: str,
        base_url: str = "http://localhost:8000",
        config: Optional[RLMConfig] = None,
        registry: Optional[Registry] = None,
        skip_server_check: bool = False,
    ):
        """
        Initialize OpenAI-backed RLM router.

        Args:
            model_name: Name of model in your registry
            base_url: Base URL of your AI Lab API server
            config: RLM configuration options
            registry: Model registry (creates default if None)
            skip_server_check: Skip health check (use when already in API context)

        Raises:
            ValueError: If model not found in registry
            ConnectionError: If API server not reachable

        Example:
            >>> router = OpenAIRLMRouter(
            ...     model_name="qwen-1-5b",
            ...     base_url="http://localhost:8000"
            ... )
        """
        self.registry = registry or Registry()
        self.model_name = model_name
        self.base_url = base_url.rstrip('/')
        self.config = config or RLMConfig(model_name=model_name)

        # Validate model exists
        try:
            self.model_entry = self.registry.get(model_name)
        except ValueError:
            raise ValueError(
                f"Model '{model_name}' not found in registry. "
                f"Use 'lab models list' to see available models."
            )

        # Validate API server is running (unless skipped)
        if not skip_server_check:
            self._check_server()

        # Initialize RLM with OpenAI backend pointing to your server
        self._init_rlm()

    def _check_server(self):
        """Verify API server is running and accessible."""
        import requests

        try:
            response = requests.get(f"{self.base_url}/health", timeout=30)
            if response.status_code != 200:
                raise ConnectionError(
                    f"API server returned status {response.status_code}"
                )
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to API server at {self.base_url}\n"
                f"Make sure the server is running:\n"
                f"  python -m uvicorn ai_lab.api.app:app --host 0.0.0.0 --port 8000"
            )
        except Exception as e:
            raise ConnectionError(
                f"Error connecting to API server: {str(e)}"
            )

    def _init_rlm(self):
        """Initialize RLM library with OpenAI backend."""
        # Set up logger if configured
        logger = None
        if self.config.log_dir:
            logger = RLMLogger(log_dir=self.config.log_dir)

        # Initialize RLM with OpenAI backend
        # We point base_url to your AI Lab server
        self.rlm = RLM(
            backend="openai",
            backend_kwargs={
                "model_name": self.model_name,
                "base_url": f"{self.base_url}/v1",  # Your OpenAI-compatible endpoints
                "api_key": "dummy",  # Not used for local server, but required by OpenAI client
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

        **Important:** RLM works best with complex analytical tasks.
        For simple prompts, use SimpleRLMRouter instead.

        Args:
            prompt: Context/document to process (can be millions of chars)
            root_prompt: Optional task/question about the context

        Returns:
            Final answer after recursive processing

        Example:
            >>> router = OpenAIRLMRouter("qwen-1-5b")
            >>> doc = open("research_paper.txt").read()  # 200K chars
            >>> result = router.complete(
            ...     prompt=doc,
            ...     root_prompt="Extract all citations and format as JSON"
            ... )
            >>> print(result)

        Example with code execution:
            >>> result = router.complete(
            ...     prompt=log_file,  # 100K lines of logs
            ...     root_prompt="Use Python to find all error patterns and suggest fixes"
            ... )
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
            >>> router = OpenAIRLMRouter("qwen-1-5b")
            >>> messages = [
            ...     {
            ...         "role": "user",
            ...         "content": "Analyze this data using Python..."
            ...     }
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
        if hasattr(self.rlm, 'usage_summary'):
            return self.rlm.usage_summary
        return None
