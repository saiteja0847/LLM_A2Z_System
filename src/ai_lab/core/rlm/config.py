"""RLM configuration."""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class RLMConfig:
    """Configuration for RLM Router."""

    # Model selection
    model_name: str

    # RLM behavior
    max_depth: int = 1  # Currently only depth=1 supported by RLM
    max_iterations: int = 30

    # Environment
    environment_type: str = "local"  # local, docker, modal
    environment_kwargs: Optional[Dict[str, Any]] = None

    # Logging
    verbose: bool = False
    log_dir: Optional[str] = None

    # System prompt (optional customization)
    custom_system_prompt: Optional[str] = None

    def __post_init__(self):
        """Initialize defaults for mutable fields."""
        if self.environment_kwargs is None:
            self.environment_kwargs = {}
