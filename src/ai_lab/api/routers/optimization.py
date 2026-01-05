"""Optimization API endpoints."""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path


logger = logging.getLogger(__name__)

from ...core.jobs import (
    JobManager,
    get_job_manager,
    Job,
    JobStatus,
    JobType,
    OptimizationJobConfig,
)
from ...core.registry import Registry, ModelNotFoundError
from ...backends.mlx_backend import MLXTrainer


router = APIRouter()


# Request/Response models
class StartOptimizationRequest(BaseModel):
    """Request to start hyperparameter optimization."""
    base_model: str = Field(..., description="Name of base model to optimize")
    dataset_path: str = Field(..., description="Path to training dataset (JSONL)")
    num_trials: int = Field(default=20, ge=1, le=100, description="Number of optimization trials")
    experiment_name: str = Field(default="lora_optimization", description="Name of experiment")
    experiment_epochs: int = Field(default=1, ge=1, le=5, description="Epochs per trial (use 1 for speed)")


class OptimizationJobResponse(BaseModel):
    """Optimization job response."""
    id: str
    type: str
    status: str
    config: dict
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: float
    error: Optional[str] = None
    result: Optional[dict] = None


class BestParametersResponse(BaseModel):
    """Best parameters response."""
    job_id: str
    best_parameters: Dict[str, Any]
    parameter_importance: Dict[str, float]


class Trial(BaseModel):
    """Single optimization trial."""
    trial_index: int
    parameters: Dict[str, Any]
    objective_mean: float
    training_time_seconds: float


class TrialsResponse(BaseModel):
    """Trials response."""
    job_id: str
    trials: List[Trial]


def _job_to_response(job: Job) -> OptimizationJobResponse:
    """Convert Job to API response."""
    return OptimizationJobResponse(
        id=job.id,
        type=job.type.value,
        status=job.status.value,
        config=job.config,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        progress=job.progress,
        error=job.error,
        result=job.result,
    )


def _create_training_function(
    base_model: str,
    dataset_path: str,
    experiment_epochs: int
) -> Callable[[Dict[str, Any]], tuple[float, float]]:
    """
    Create a training function for optimization.

    Args:
        base_model: Base model name
        dataset_path: Path to dataset
        experiment_epochs: Number of epochs per trial

    Returns:
        Function that takes parameters and returns (loss, sem)
    """
    def training_function(parameters: Dict[str, Any]) -> tuple[float, float]:
        """
        Train with given parameters and return loss.

        Args:
            parameters: Trial parameters from Ax

        Returns:
            Tuple of (loss, sem)
        """
        from ...core.jobs import get_job_manager

        # Create training config from parameters
        output_name = f"optimization_trial_{parameters.get('lora_r', 8)}"

        # Import MLX trainer and registry
        registry = Registry()

        # Get base model entry
        base_entry = registry.get(base_model)

        # Create trainer instance
        trainer = MLXTrainer(base_entry)

        try:
            # Run actual training
            output_path, metrics = trainer.train(
                dataset_path=Path(dataset_path),
                output_name=output_name,
                epochs=experiment_epochs,
                batch_size=parameters.get("batch_size", 2),
                lora_rank=int(parameters.get("lora_r", 8)),
                lora_layers=16,
                learning_rate=parameters.get("learning_rate", 1e-4),
                max_seq_length=2048,
                val_batches=10,  # Faster validation for experiments
                steps_per_eval=100,  # Evaluate frequently for optimization
            )

            # Extract validation loss
            loss = metrics.get("val_loss", 999.0)
            sem = 0.0  # Standard error - MLX doesn't provide this

            return (loss, sem)

        except Exception as e:
            logger.error(f"Training trial failed: {e}", exc_info=True)
            # Return worst-case loss so Ax avoids this parameter region
            return (float('inf'), 0.0)

    return training_function


@router.post("/start", response_model=OptimizationJobResponse)
async def start_optimization(
    request: StartOptimizationRequest,
    background_tasks: BackgroundTasks,
) -> OptimizationJobResponse:
    """
    Start a hyperparameter optimization job.

    Runs Ax optimization to find best LoRA hyperparameters.
    """
    job_manager = get_job_manager()

    # Validate base model exists
    try:
        registry = Registry()
        registry.get(request.base_model)
    except ModelNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Validate dataset exists
    dataset_path = Path(request.dataset_path)
    if not dataset_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Dataset not found: {request.dataset_path}"
        )

    # Create optimization job
    job = job_manager.create_optimization_job(
        base_model=request.base_model,
        dataset_path=request.dataset_path,
        num_trials=request.num_trials,
        experiment_name=request.experiment_name,
        experiment_epochs=request.experiment_epochs,
    )

    # Create training function
    training_function = _create_training_function(
        base_model=request.base_model,
        dataset_path=request.dataset_path,
        experiment_epochs=request.experiment_epochs,
    )

    # Start optimization in background
    background_tasks.add_task(
        job_manager.run_optimization_job,
        job.id,
        training_function,
    )

    return _job_to_response(job)


@router.get("/list", response_model=List[OptimizationJobResponse])
async def list_optimization_jobs(
    status: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=100),
) -> List[OptimizationJobResponse]:
    """List all optimization jobs."""
    job_manager = get_job_manager()

    # Filter by status
    job_status = JobStatus(status) if status else None

    jobs = job_manager.list_jobs(status=job_status, job_type=JobType.OPTIMIZATION, limit=limit)

    return [_job_to_response(job) for job in jobs]


@router.get("/{job_id}", response_model=OptimizationJobResponse)
async def get_optimization_job(job_id: str) -> OptimizationJobResponse:
    """Get optimization job status."""
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if job.type != JobType.OPTIMIZATION:
        raise HTTPException(
            status_code=400, detail=f"Job {job_id} is not an optimization job"
        )

    return _job_to_response(job)


@router.get("/{job_id}/best", response_model=BestParametersResponse)
async def get_best_parameters(job_id: str) -> BestParametersResponse:
    """Get best parameters from completed optimization."""
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if job.type != JobType.OPTIMIZATION:
        raise HTTPException(
            status_code=400, detail=f"Job {job_id} is not an optimization job"
        )

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} has not completed. Status: {job.status.value}",
        )

    if not job.result:
        raise HTTPException(status_code=404, detail="No results available")

    return BestParametersResponse(
        job_id=job_id,
        best_parameters=job.result.get("best_parameters", {}),
        parameter_importance=job.result.get("parameter_importance", {}),
    )


@router.get("/{job_id}/trials", response_model=TrialsResponse)
async def get_trials(job_id: str) -> TrialsResponse:
    """Get all trials from optimization job."""
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if job.type != JobType.OPTIMIZATION:
        raise HTTPException(
            status_code=400, detail=f"Job {job_id} is not an optimization job"
        )

    # Safely get experiment name from config
    experiment_name = "optimization"
    if job.config and isinstance(job.config, dict):
        experiment_name = job.config.get('experiment_name', 'optimization')

    # Read trials from saved results
    results_file = (
        Path("jobs/optimization") / f"{experiment_name}_results.json"
    )

    trials = []
    if results_file.exists():
        try:
            import json
            with open(results_file) as f:
                data = json.load(f)
                if isinstance(data, dict):
                    trials = data.get("trials", [])
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to read trials file: {e}", exc_info=True)

    return TrialsResponse(job_id=job_id, trials=trials)
