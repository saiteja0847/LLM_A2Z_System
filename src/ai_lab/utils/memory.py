"""Memory monitoring and estimation utilities."""
import psutil
from dataclasses import dataclass
from typing import Tuple

from ..core.registry import ModelEntry, Quantization, ModelBackend, ModelType, Registry


@dataclass
class MemoryStatus:
    """System memory status."""
    total_gb: float
    available_gb: float
    used_gb: float
    percent_used: float


def get_memory_status() -> MemoryStatus:
    """Get current system memory status."""
    mem = psutil.virtual_memory()
    return MemoryStatus(
        total_gb=mem.total / (1024**3),
        available_gb=mem.available / (1024**3),
        used_gb=mem.used / (1024**3),
        percent_used=mem.percent
    )


def estimate_model_memory(entry: ModelEntry) -> float:
    """
    Estimate runtime memory for a model.

    Args:
        entry: Model registry entry

    Returns:
        Estimated memory in GB
    """
    # Use cached estimate if available
    if entry.estimated_memory_gb:
        return entry.estimated_memory_gb

    # Remote models don't use local memory
    if entry.backend == ModelBackend.REMOTE:
        return 0.0

    # Conservative estimate for Ollama (it manages its own memory)
    if entry.backend == ModelBackend.OLLAMA:
        return 4.0

    # For adapters, estimate based on parent model + small overhead
    if entry.type == ModelType.ADAPTER and entry.parent:
        registry = Registry()
        try:
            parent_entry = registry.get(entry.parent)
            parent_memory = estimate_model_memory(parent_entry)
            # Adapters are small (typically < 100MB), add minimal overhead
            return parent_memory + 0.1
        except Exception:
            # If parent not found, fall through to default estimate
            pass

    # Default conservative estimate if size unknown
    if not entry.size_gb:
        return 4.0

    base = entry.size_gb

    # Apply quantization factor
    quant_factors = {
        Quantization.FP16: 1.0,
        Quantization.INT8: 0.6,
        Quantization.INT4: 0.35,
        Quantization.NONE: 1.0,
    }
    base *= quant_factors.get(entry.quantization, 1.0)

    # KV cache estimate (scales with model size and context)
    # Assume typical usage of 4K tokens, not max context
    # Small models use less KV cache
    typical_context = min(4096, entry.context_length)
    if base < 1.0:  # Small models (< 3B params)
        kv_cache = (typical_context / 4096) * 0.5
    else:  # Larger models
        kv_cache = (typical_context / 4096) * 1.0

    # Overhead buffer (for activations, etc.)
    overhead = 1.0

    return base + kv_cache + overhead


def estimate_training_memory(entry: ModelEntry, batch_size: int = 1) -> float:
    """
    Estimate memory needed for training.

    Args:
        entry: Base model registry entry
        batch_size: Training batch size

    Returns:
        Estimated memory in GB
    """
    inference_mem = estimate_model_memory(entry)

    # Training typically needs 2-3x inference memory
    # LoRA is more efficient, ~1.5x inference memory
    # Scale by batch size
    return inference_mem * 1.5 * batch_size


def check_memory_available(
    required_gb: float,
    reserve_gb: float = 2.0
) -> Tuple[bool, str]:
    """
    Check if we have enough memory for an operation.

    Args:
        required_gb: Memory required in GB
        reserve_gb: Memory to keep reserved for system (default: 2GB)

    Returns:
        Tuple of (success: bool, message: str)
    """
    status = get_memory_status()
    available = status.available_gb - reserve_gb

    if required_gb > available:
        return (
            False,
            f"Need {required_gb:.1f}GB, only {available:.1f}GB available "
            f"(keeping {reserve_gb}GB reserve)"
        )

    return (
        True,
        f"OK: {required_gb:.1f}GB required, {available:.1f}GB available"
    )


def get_recommended_batch_size(entry: ModelEntry, reserve_gb: float = 2.0) -> int:
    """
    Get recommended batch size for training based on available memory.

    Args:
        entry: Base model registry entry
        reserve_gb: Memory to keep reserved

    Returns:
        Recommended batch size (1-4)
    """
    status = get_memory_status()
    available = status.available_gb - reserve_gb

    # Try batch sizes from 4 down to 1
    for batch_size in [4, 3, 2, 1]:
        required = estimate_training_memory(entry, batch_size)
        if required <= available:
            return batch_size

    # If even batch_size=1 doesn't fit, return 1 (will fail with clear error)
    return 1


def format_memory_gb(gb: float) -> str:
    """Format memory size for display."""
    if gb < 1.0:
        return f"{gb * 1024:.0f} MB"
    return f"{gb:.1f} GB"
