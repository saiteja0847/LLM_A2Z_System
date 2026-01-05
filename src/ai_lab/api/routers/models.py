"""Models management API endpoints."""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path

from ...core.registry import (
    Registry,
    ModelEntry,
    ModelBackend,
    ModelType,
    Quantization,
    ModelStatus,
    ModelNotFoundError
)
from ...core.downloader import ModelDownloader
from ...utils.memory import estimate_model_memory, format_memory_gb


logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response models
class ModelResponse(BaseModel):
    """Model information response."""
    name: str
    description: Optional[str] = None
    backend: str
    type: str
    status: str
    quantization: str
    size_gb: Optional[float] = None
    estimated_memory_gb: Optional[float] = None
    context_length: int
    path: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class RegisterModelRequest(BaseModel):
    """Request to register a model."""
    name: str
    path: Optional[str] = None
    backend: ModelBackend = ModelBackend.MLX
    type: ModelType = ModelType.BASE
    quantization: Quantization = Quantization.INT4
    size_gb: Optional[float] = None
    context_length: int = 4096
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class DownloadModelRequest(BaseModel):
    """Request to download a model from HuggingFace."""
    repo_id: str
    name: Optional[str] = None
    backend: ModelBackend = ModelBackend.MLX
    quantization: Quantization = Quantization.INT4
    tags: List[str] = Field(default_factory=list)


def _entry_to_response(entry: ModelEntry) -> ModelResponse:
    """Convert ModelEntry to API response."""
    return ModelResponse(
        name=entry.name,
        description=entry.description,
        backend=entry.backend.value,
        type=entry.type.value,
        status=entry.status.value,
        quantization=entry.quantization.value,
        size_gb=entry.size_gb,
        estimated_memory_gb=entry.estimated_memory_gb,
        context_length=entry.context_length,
        path=str(entry.path) if entry.path else None,
        tags=entry.tags or []
    )


@router.get("/", response_model=List[ModelResponse])
async def list_models(
    status: Optional[ModelStatus] = None,
    backend: Optional[ModelBackend] = None,
    tag: Optional[str] = None
):
    """List all registered models."""
    registry = Registry()
    models = registry.list(status=status, backend=backend, tag=tag)
    return [_entry_to_response(m) for m in models]


@router.get("/{name}", response_model=ModelResponse)
async def get_model(name: str):
    """Get information about a specific model."""
    registry = Registry()
    try:
        entry = registry.get(name)
        return _entry_to_response(entry)
    except ModelNotFoundError:
        raise HTTPException(status_code=404, detail=f"Model not found: {name}")


@router.post("/", response_model=ModelResponse, status_code=201)
async def register_model(request: RegisterModelRequest):
    """Register a new model."""
    registry = Registry()
    
    try:
        entry = ModelEntry(
            name=request.name,
            description=request.description,
            path=Path(request.path) if request.path else None,
            backend=request.backend,
            type=request.type,
            quantization=request.quantization,
            size_gb=request.size_gb,
            context_length=request.context_length,
            tags=request.tags,
        )
        
        # Estimate memory
        entry.estimated_memory_gb = estimate_model_memory(entry)
        
        registry.add(entry)
        return _entry_to_response(entry)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/download", response_model=ModelResponse, status_code=201)
async def download_model(request: DownloadModelRequest):
    """Download a model from HuggingFace Hub."""
    downloader = ModelDownloader()

    logger.info(f"Download request received: repo_id={request.repo_id}, name={request.name}")

    try:
        entry = downloader.download(
            repo_id=request.repo_id,
            name=request.name,
            backend=request.backend,
            quantization=request.quantization,
            auto_register=True,
            tags=request.tags,
        )
        logger.info(f"Download successful: {entry.name}")
        return _entry_to_response(entry)

    except ValueError as e:
        logger.error(f"Download validation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Download failed with exception: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.delete("/{name}", status_code=204)
async def remove_model(name: str, force: bool = False):
    """Remove a model from the registry."""
    registry = Registry()
    
    try:
        registry.remove(name, force=force)
    except ModelNotFoundError:
        raise HTTPException(status_code=404, detail=f"Model not found: {name}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
