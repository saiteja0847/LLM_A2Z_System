"""Model management."""
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Model:
    """
    Represents a model in the registry.

    Attributes:
        name: Model name
        backend: Backend type (mlx, gguf, etc.)
        type: Model type (base or adapter)
        status: Model status (ready, downloading, error)
        path: Path to model files
        description: Optional description
        size_gb: Model size in GB
        estimated_memory_gb: Estimated memory requirement
        quantization: Quantization type
        context_length: Context window size
        parent: Parent model name (for adapters)
    """

    name: str
    backend: str
    type: str
    status: str
    path: str
    description: Optional[str] = None
    size_gb: Optional[float] = None
    estimated_memory_gb: Optional[float] = None
    quantization: Optional[str] = None
    context_length: Optional[int] = None
    parent: Optional[str] = None


class ModelManager:
    """
    Manages models in the AI Lab platform.

    Example:
        >>> client = AILabClient()
        >>> models = client.models.list()
        >>> model = client.models.get("qwen-1-5b")
        >>> client.models.download("mlx-community/Qwen2.5-1.5B-Instruct-4bit", "qwen-1-5b")
    """

    def __init__(self, client):
        self.client = client

    def list(self, status: Optional[str] = None, backend: Optional[str] = None) -> List[Model]:
        """
        List all models.

        Args:
            status: Filter by status (ready, downloading, error)
            backend: Filter by backend (mlx, gguf, ollama, remote)

        Returns:
            List of Model objects

        Example:
            >>> models = client.models.list()
            >>> base_models = [m for m in models if m.type == "base"]
        """
        params = {}
        if status:
            params["status"] = status
        if backend:
            params["backend"] = backend

        response = self.client.get("/api/models/", params=params)
        data = response.json()

        return [Model(**model_data) for model_data in data]

    def get(self, name: str) -> Model:
        """
        Get a specific model by name.

        Args:
            name: Model name

        Returns:
            Model object

        Raises:
            requests.HTTPError: If model not found

        Example:
            >>> model = client.models.get("qwen-1-5b")
            >>> print(model.size_gb)
        """
        response = self.client.get(f"/api/models/{name}")
        return Model(**response.json())

    def download(
        self,
        repo_id: str,
        name: Optional[str] = None,
        backend: str = "mlx",
    ) -> Model:
        """
        Download a model from HuggingFace.

        Args:
            repo_id: HuggingFace repository ID (e.g., "mlx-community/Qwen2.5-1.5B-Instruct-4bit")
            name: Optional local name for the model (auto-generated if not provided)
            backend: Backend to use (default: "mlx")

        Returns:
            Downloaded Model object

        Example:
            >>> model = client.models.download(
            ...     repo_id="mlx-community/Qwen2.5-1.5B-Instruct-4bit",
            ...     name="qwen-1-5b"
            ... )
        """
        payload = {
            "repo_id": repo_id,
            "backend": backend,
        }
        if name:
            payload["name"] = name

        response = self.client.post("/api/models/download", json=payload)
        return Model(**response.json())

    def delete(self, name: str, force: bool = False) -> None:
        """
        Delete a model from the registry.

        Args:
            name: Model name
            force: Force deletion even if model is in use

        Example:
            >>> client.models.delete("old-model")
        """
        params = {"force": force} if force else None
        self.client.delete(f"/api/models/{name}")
