"""System status and health API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel

from ...core.registry import Registry
from ...utils.memory import get_memory_status, format_memory_gb


router = APIRouter()


class MemoryStatus(BaseModel):
    """Memory status response."""
    total_gb: float
    available_gb: float
    used_gb: float
    percent_used: float


class SystemStatus(BaseModel):
    """System status response."""
    memory: MemoryStatus
    models_count: int
    models_by_status: dict


@router.get("/status", response_model=SystemStatus)
async def get_system_status():
    """Get system status including memory and model counts."""
    mem = get_memory_status()
    registry = Registry()
    models = registry.list()
    
    # Count models by status
    by_status = {}
    for m in models:
        status = m.status.value
        by_status[status] = by_status.get(status, 0) + 1
    
    return SystemStatus(
        memory=MemoryStatus(
            total_gb=mem.total_gb,
            available_gb=mem.available_gb,
            used_gb=mem.used_gb,
            percent_used=mem.percent_used
        ),
        models_count=len(models),
        models_by_status=by_status
    )


class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    version: str
    mlx_available: bool


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint with backend availability."""
    # Check if MLX is available
    mlx_available = False
    try:
        import mlx
        mlx_available = True
    except ImportError:
        pass

    return HealthCheck(
        status="healthy",
        version="1.0.0",
        mlx_available=mlx_available
    )
