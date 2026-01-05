"""RLM API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from ...core.rlm import SimpleRLMRouter, RLMConfig
from ...core.registry import Registry

router = APIRouter(prefix="/api/v1/rlm", tags=["RLM"])


class RLMCompletionRequest(BaseModel):
    """Request for RLM completion."""

    model: str = Field(..., description="Model name from registry")
    prompt: str = Field(..., description="Context/document to process (can be very large)")
    root_prompt: Optional[str] = Field(
        None,
        description="Optional task/question about the context"
    )
    max_iterations: int = Field(
        30,
        ge=1,
        le=100,
        description="Maximum RLM iterations"
    )
    environment: str = Field(
        "local",
        description="REPL environment type (local, docker, modal)"
    )
    verbose: bool = Field(
        False,
        description="Enable verbose logging"
    )


class RLMCompletionResponse(BaseModel):
    """Response from RLM completion."""

    response: str
    model: str
    prompt_size: int
    iterations: int
    sub_calls: int
    execution_time: float
    usage_summary: dict


@router.post("/complete", response_model=RLMCompletionResponse)
async def rlm_complete(request: RLMCompletionRequest):
    """
    Run RLM completion on potentially huge context.

    RLM (Recursive Language Model) can handle near-infinite context
    lengths by:
    1. Intelligently chunking the input
    2. Processing each chunk with sub-LLM calls
    3. Aggregating results across iterations
    4. Producing a final answer

    Use this endpoint when:
    • Input exceeds model's context window
    • Task requires multi-step reasoning
    • Document needs comprehensive analysis

    Example:
        POST /api/v1/rlm/complete
        {
            "model": "qwen3-4b-instruct",
            "prompt": "...200K character document...",
            "root_prompt": "Summarize the key findings",
            "max_iterations": 30
        }
    """
    import time

    registry = Registry()

    # Validate model exists
    try:
        registry.get(request.model)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{request.model}' not found in registry"
        )

    try:
        # Create RLM config
        config = RLMConfig(
            model_name=request.model,
            max_iterations=request.max_iterations,
            environment_type=request.environment,
            verbose=request.verbose,
        )

        # Create router
        rlm_router = SimpleRLMRouter(
            model_name=request.model,
            config=config,
        )

        # Track time
        start_time = time.time()

        # Run RLM completion
        result = rlm_router.complete(
            prompt=request.prompt,
            root_prompt=request.root_prompt,
        )

        execution_time = time.time() - start_time

        # Get usage statistics
        usage = rlm_router.get_usage_summary()
        model_usage = usage.model_usage_summaries.get(request.model)

        return RLMCompletionResponse(
            response=result,
            model=request.model,
            prompt_size=len(request.prompt),
            iterations=0,  # RLM library provides this
            sub_calls=model_usage.total_calls if model_usage else 0,
            execution_time=execution_time,
            usage_summary=usage.to_dict(),
        )

    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"RLM library not installed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"RLM completion failed: {str(e)}"
        )


@router.get("/models")
async def list_rlm_compatible_models():
    """
    List all models that can be used with RLM.

    All registered models are RLM-compatible - RLM is a
    runtime wrapper that works with any InferenceClient.
    """
    from ...core.registry import ModelBackend

    registry = Registry()
    models = registry.list()

    return {
        "models": [
            {
                "name": m.name,
                "backend": m.backend.value,
                "context_length": m.context_length,
                "status": m.status.value,
                "description": m.description,
            }
            for m in models
        ],
        "total": len(models)
    }


@router.get("/status")
async def rlm_status():
    """Get RLM system status."""
    try:
        from rlm import RLM
        rlm_installed = True
    except ImportError:
        rlm_installed = False

    return {
        "rlm_installed": rlm_installed,
        "message": (
            "RLM library is installed and ready" if rlm_installed
            else "RLM library not installed. Install with: pip install git+https://github.com/alexzhang13/rlm.git"
        )
    }


@router.post("/full", response_model=RLMCompletionResponse)
async def rlm_full_complete(request: RLMCompletionRequest):
    """
    Run full RLM completion with official RLM library.

    This endpoint uses the official RLM library via your OpenAI-compatible API,
    providing advanced features like code execution in REPL environments and
    sophisticated multi-step reasoning.

    Use this endpoint when:
    • Input exceeds model's context window (>100K characters)
    • Task requires code execution (e.g., "Use Python to analyze...")
    • Complex multi-step reasoning needed
    • Document needs comprehensive analysis with sub-calls

    **Important:** Requires RLM library to be installed.

    Example:
        POST /api/v1/rlm/full
        {
            "model": "qwen-1-5b",
            "prompt": "...100K character log file...",
            "root_prompt": "Use Python to find all error patterns and suggest fixes",
            "max_iterations": 30
        }

    Difference from /complete:
    • /complete: Uses SimpleRLMRouter (basic chunking, no server needed)
    • /full: Uses OpenAIRLMRouter (full RLM, requires server, code execution)
    """
    import time

    registry = Registry()

    # Validate model exists
    try:
        registry.get(request.model)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{request.model}' not found in registry"
        )

    try:
        from ...core.rlm import OpenAIRLMRouter, RLMConfig

        # Create RLM config
        config = RLMConfig(
            model_name=request.model,
            max_iterations=request.max_iterations,
            environment_type=request.environment,
            verbose=request.verbose,
        )

        # Create router (skip server check since we're already in the API)
        rlm_router = OpenAIRLMRouter(
            model_name=request.model,
            config=config,
            skip_server_check=True,  # Already in API context, avoid circular check
        )

        # Track time
        start_time = time.time()

        # Run RLM completion
        result = rlm_router.complete(
            prompt=request.prompt,
            root_prompt=request.root_prompt,
        )

        execution_time = time.time() - start_time

        # Get usage statistics
        usage = rlm_router.get_usage_summary()

        return RLMCompletionResponse(
            response=result,
            model=request.model,
            prompt_size=len(request.prompt),
            iterations=0,  # RLM library tracks this internally
            sub_calls=0,  # RLM library tracks this internally
            execution_time=execution_time,
            usage_summary=usage.to_dict() if usage else {},
        )

    except ConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to API server: {str(e)}. Make sure the server is running."
        )
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"RLM library not installed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"RLM completion failed: {str(e)}"
        )

