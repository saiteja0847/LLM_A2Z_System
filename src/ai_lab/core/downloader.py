"""HuggingFace model downloader with progress tracking."""
from pathlib import Path
from typing import Optional
from huggingface_hub import snapshot_download, list_repo_files
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TimeRemainingColumn
import re

from .registry import ModelEntry, ModelBackend, Quantization, ModelType, Registry
from ..utils.memory import estimate_model_memory


class ModelDownloader:
    """Download and register models from HuggingFace Hub."""

    def __init__(self, models_dir: Path = Path("models")):
        """
        Initialize downloader.

        Args:
            models_dir: Directory to store downloaded models
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.registry = Registry()

    def download(
        self,
        repo_id: str,
        name: Optional[str] = None,
        backend: ModelBackend = ModelBackend.MLX,
        quantization: Quantization = Quantization.INT4,
        auto_register: bool = True,
        tags: Optional[list[str]] = None,
    ) -> ModelEntry:
        """
        Download a model from HuggingFace Hub.

        Args:
            repo_id: HuggingFace repository ID (e.g., "mlx-community/Qwen2.5-1.5B-Instruct-4bit")
            name: Local model name (auto-generated from repo if not provided)
            backend: Backend to use (default: MLX)
            quantization: Quantization level (default: INT4)
            auto_register: Automatically register in registry (default: True)
            tags: Optional tags for the model

        Returns:
            ModelEntry for the downloaded model

        Raises:
            ValueError: If repo doesn't exist or download fails
        """
        # Generate name from repo_id if not provided
        if not name:
            name = self._generate_name(repo_id)

        # Check if already registered
        try:
            existing = self.registry.get(name)
            if existing.path and existing.path.exists():
                raise ValueError(
                    f"Model '{name}' already exists at {existing.path}\n"
                    f"Use a different name or remove the existing model first."
                )
        except Exception:
            pass  # Not registered, continue

        # Determine download path
        download_path = self.models_dir / name

        # Download with progress tracking
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task(
                    f"Downloading {repo_id}...",
                    total=None
                )

                local_dir = snapshot_download(
                    repo_id=repo_id,
                    local_dir=str(download_path),
                    local_dir_use_symlinks=False,
                )

                progress.update(task, completed=True, description=f"✓ Downloaded to {local_dir}")

        except Exception as e:
            raise ValueError(f"Download failed: {e}")

        # Extract model info from repo
        model_info = self._extract_model_info(repo_id, Path(local_dir))

        # Create registry entry
        entry = ModelEntry(
            name=name,
            description=model_info.get("description", f"Downloaded from {repo_id}"),
            path=Path(local_dir),
            backend=backend,
            type=ModelType.BASE,
            quantization=quantization,
            size_gb=model_info.get("size_gb"),
            context_length=model_info.get("context_length", 4096),
            tags=tags or model_info.get("tags", []),
        )

        # Estimate memory
        entry.estimated_memory_gb = estimate_model_memory(entry)

        # Register if requested
        if auto_register:
            self.registry.add(entry)

        return entry

    def _generate_name(self, repo_id: str) -> str:
        """
        Generate a valid model name from HuggingFace repo ID.

        Args:
            repo_id: HuggingFace repository ID

        Returns:
            Valid model name (lowercase, hyphens only)
        """
        # Extract model name from repo_id
        # e.g., "mlx-community/Qwen2.5-1.5B-Instruct-4bit" -> "qwen2-5-1-5b-instruct-4bit"
        name = repo_id.split("/")[-1]

        # Convert to lowercase FIRST
        name = name.lower()

        # Replace periods with hyphens (e.g., "2.5" -> "2-5")
        name = name.replace(".", "-")

        # Replace invalid chars with hyphens
        name = re.sub(r"[^a-z0-9-]", "-", name)

        # Remove consecutive hyphens
        name = re.sub(r"-+", "-", name)

        # Remove leading/trailing hyphens
        name = name.strip("-")

        return name

    def _extract_model_info(self, repo_id: str, local_dir: Path) -> dict:
        """
        Extract model information from downloaded files.

        Args:
            repo_id: HuggingFace repository ID
            local_dir: Local directory where model was downloaded

        Returns:
            Dictionary with model info (description, size, context_length, tags)
        """
        info = {
            "description": f"Downloaded from {repo_id}",
            "tags": [],
        }

        # Parse repo_id for info
        repo_name = repo_id.split("/")[-1].lower()

        # Detect quantization from name
        if "4bit" in repo_name or "4-bit" in repo_name:
            info["tags"].append("4bit")
        elif "8bit" in repo_name or "8-bit" in repo_name:
            info["tags"].append("8bit")

        # Detect model type
        if "instruct" in repo_name:
            info["tags"].append("instruct")
        if "chat" in repo_name:
            info["tags"].append("chat")

        # Detect model family
        if "qwen" in repo_name:
            info["tags"].append("qwen")
        elif "llama" in repo_name:
            info["tags"].append("llama")
        elif "mistral" in repo_name:
            info["tags"].append("mistral")
        elif "phi" in repo_name:
            info["tags"].append("phi")

        # Try to read config.json for context length
        config_file = local_dir / "config.json"
        if config_file.exists():
            try:
                import json
                with open(config_file) as f:
                    config = json.load(f)
                    # Common keys for context length
                    for key in ["max_position_embeddings", "n_positions", "max_seq_len"]:
                        if key in config:
                            info["context_length"] = config[key]
                            break
            except Exception:
                pass

        # Calculate size from downloaded files
        total_size = sum(
            f.stat().st_size
            for f in local_dir.rglob("*")
            if f.is_file()
        )
        info["size_gb"] = total_size / (1024**3)

        return info

    def list_available_models(self, organization: str = "mlx-community") -> list[str]:
        """
        List available models from a HuggingFace organization.

        Args:
            organization: HuggingFace organization name

        Returns:
            List of repository IDs
        """
        try:
            from huggingface_hub import list_models

            models = list_models(author=organization)
            return [model.id for model in models]

        except Exception as e:
            raise ValueError(f"Failed to list models: {e}")

    def search_models(
        self,
        query: str,
        organization: str = "mlx-community",
        limit: int = 10
    ) -> list[dict]:
        """
        Search for models on HuggingFace Hub.

        Args:
            query: Search query (e.g., "qwen", "llama")
            organization: HuggingFace organization to search in
            limit: Maximum number of results

        Returns:
            List of model info dictionaries
        """
        try:
            from huggingface_hub import list_models

            models = list_models(
                author=organization,
                search=query,
                limit=limit
            )

            results = []
            for model in models:
                results.append({
                    "id": model.id,
                    "downloads": getattr(model, "downloads", 0),
                    "likes": getattr(model, "likes", 0),
                    "tags": getattr(model, "tags", []),
                })

            # Sort by downloads
            results.sort(key=lambda x: x["downloads"], reverse=True)

            return results

        except Exception as e:
            raise ValueError(f"Search failed: {e}")
