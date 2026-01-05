"""Model registry with Pydantic models and YAML persistence."""
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import yaml


class ModelBackend(str, Enum):
    """Supported inference backends."""
    MLX = "mlx"
    GGUF = "gguf"
    OLLAMA = "ollama"
    REMOTE = "remote"


class TrainingBackend(str, Enum):
    """Supported training backends."""
    MLX_LORA = "mlx_lora"
    AXOLOTL = "axolotl"
    UNSLOTH = "unsloth"
    NONE = "none"


class ModelType(str, Enum):
    """Model types."""
    BASE = "base"
    ADAPTER = "adapter"


class ModelStatus(str, Enum):
    """Model lifecycle status."""
    DOWNLOADING = "downloading"
    READY = "ready"
    CANDIDATE = "candidate"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    FAILED = "failed"


class Quantization(str, Enum):
    """Quantization levels."""
    FP16 = "fp16"
    INT8 = "int8"
    INT4 = "int4"
    NONE = "none"


class ModelEntry(BaseModel):
    """Single model entry in the registry."""

    # Identity
    name: str = Field(..., pattern=r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', min_length=2, max_length=64)
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)

    # Type & Lineage
    type: ModelType = ModelType.BASE
    parent: Optional[str] = None  # For adapters

    # Backend Configuration
    backend: ModelBackend = ModelBackend.MLX
    path: Optional[Path] = None  # Local path (MLX, GGUF)
    ollama_name: Optional[str] = None  # Ollama model name
    api_base: Optional[str] = None  # Remote API base URL
    api_model: Optional[str] = None  # Remote model identifier
    api_key_env: Optional[str] = None  # Env var name for API key

    # Model Specs
    size_gb: Optional[float] = None
    quantization: Quantization = Quantization.INT4
    context_length: int = Field(default=4096, ge=512, le=262144)  # Support up to 256K context (Qwen3)
    estimated_memory_gb: Optional[float] = None

    # Training
    training_backend: TrainingBackend = TrainingBackend.NONE
    training_config: Optional[str] = None  # Path to training config

    # Status & Metadata
    status: ModelStatus = ModelStatus.READY
    source_url: Optional[str] = None
    chat_template: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='after')
    def validate_backend_requirements(self):
        """Validate backend-specific requirements."""
        if self.backend == ModelBackend.MLX and not self.path:
            raise ValueError("MLX backend requires 'path'")
        if self.backend == ModelBackend.GGUF and not self.path:
            raise ValueError("GGUF backend requires 'path'")
        if self.backend == ModelBackend.OLLAMA and not self.ollama_name:
            raise ValueError("Ollama backend requires 'ollama_name'")
        if self.backend == ModelBackend.REMOTE and not (self.api_base and self.api_model):
            raise ValueError("Remote backend requires 'api_base' and 'api_model'")
        if self.type == ModelType.ADAPTER and not self.parent:
            raise ValueError("Adapter models require 'parent'")
        return self

    @field_validator('path')
    @classmethod
    def validate_path_exists(cls, v: Optional[Path]) -> Optional[Path]:
        """Validate that path exists if provided."""
        if v is not None and not Path(v).exists():
            raise ValueError(f"Path does not exist: {v}")
        return Path(v) if v is not None else None

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True


class Registry:
    """Manages the model registry YAML file."""

    def __init__(self, path: str = "registry.yaml"):
        self.path = Path(path)
        self._ensure_exists()

    def _ensure_exists(self):
        """Create registry file if it doesn't exist."""
        if not self.path.exists():
            self.path.write_text("models: []\n")

    def _load(self) -> dict:
        """Load registry from YAML."""
        content = yaml.safe_load(self.path.read_text())
        return content or {"models": []}

    def _save(self, data: dict):
        """Save registry to YAML."""
        self.path.write_text(
            yaml.dump(data, default_flow_style=False, sort_keys=False)
        )

    def list(
        self,
        status: Optional[ModelStatus] = None,
        backend: Optional[ModelBackend] = None,
        type: Optional[ModelType] = None,
        tag: Optional[str] = None
    ) -> list[ModelEntry]:
        """List models with optional filters."""
        data = self._load()
        models = [ModelEntry(**m) for m in data.get("models", [])]

        if status:
            models = [m for m in models if m.status == status]
        if backend:
            models = [m for m in models if m.backend == backend]
        if type:
            models = [m for m in models if m.type == type]
        if tag:
            models = [m for m in models if tag in m.tags]

        return models

    def get(self, name: str) -> ModelEntry:
        """Get a single model by name."""
        for model in self.list():
            if model.name == name:
                return model
        raise ModelNotFoundError(f"Model '{name}' not found in registry")

    def add(self, entry: ModelEntry) -> ModelEntry:
        """Add a new model to the registry."""
        data = self._load()

        # Check for duplicates
        if any(m["name"] == entry.name for m in data["models"]):
            raise ValueError(f"Model '{entry.name}' already exists")

        # Validate parent exists if adapter
        if entry.parent:
            self.get(entry.parent)  # Raises if not found

        # Convert to dict with JSON-compatible serialization
        entry_dict = entry.model_dump(mode='json')
        data["models"].append(entry_dict)
        self._save(data)
        return entry

    def update(self, name: str, updates: dict) -> ModelEntry:
        """Update an existing model."""
        data = self._load()

        for i, m in enumerate(data["models"]):
            if m["name"] == name:
                m.update(updates)
                m["updated_at"] = datetime.now().isoformat()
                entry = ModelEntry(**m)
                data["models"][i] = entry.model_dump(mode='json')
                self._save(data)
                return entry

        raise ModelNotFoundError(f"Model '{name}' not found")

    def remove(self, name: str, force: bool = False) -> bool:
        """Remove a model from the registry."""
        data = self._load()

        # Check for dependents
        if not force:
            dependents = [m["name"] for m in data["models"] if m.get("parent") == name]
            if dependents:
                raise ValueError(
                    f"Cannot remove: models depend on this: {dependents}"
                )

        data["models"] = [m for m in data["models"] if m["name"] != name]
        self._save(data)
        return True


class ModelNotFoundError(Exception):
    """Raised when a model is not found in the registry."""
    pass
