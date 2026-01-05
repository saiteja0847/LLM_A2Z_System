"""Training API endpoints."""
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path
import shutil
import uuid

from ...core.jobs import (
    JobManager,
    get_job_manager,
    Job,
    JobStatus,
    JobType,
    TrainingConfig
)
from ...core.registry import Registry, ModelNotFoundError, ModelEntry, ModelType, ModelBackend
from ...backends.mlx_backend import MLXTrainer


router = APIRouter()


# Request/Response models
class StartTrainingRequest(BaseModel):
    """Request to start a training job."""
    base_model: str = Field(..., description="Name of base model to fine-tune")
    dataset_path: str = Field(..., description="Path to training dataset (JSONL)")
    output_name: str = Field(..., description="Name for the fine-tuned model")
    epochs: int = Field(default=3, ge=1, le=100, description="Number of training epochs")
    batch_size: int = Field(default=2, ge=1, le=32, description="Training batch size")
    lora_rank: int = Field(default=8, ge=1, le=256, description="LoRA rank")
    lora_layers: int = Field(default=16, ge=1, description="Number of layers for LoRA")
    learning_rate: float = Field(default=1e-4, gt=0, description="Learning rate")
    gradient_checkpoint: bool = Field(default=True, description="Enable gradient checkpointing for memory efficiency")
    max_seq_length: int = Field(default=2048, ge=128, le=32768, description="Maximum sequence length")
    val_batches: int = Field(default=25, ge=1, description="Number of validation batches")
    steps_per_eval: int = Field(default=100, ge=1, description="Steps between evaluations")


class JobResponse(BaseModel):
    """Training job response."""
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


class JobListResponse(BaseModel):
    """List of training jobs."""
    jobs: List[JobResponse]
    total: int


class JobLogsResponse(BaseModel):
    """Job logs response."""
    id: str
    logs: List[str]


def _job_to_response(job: Job) -> JobResponse:
    """Convert Job to API response."""
    return JobResponse(
        id=job.id,
        type=job.type.value,
        status=job.status.value,
        config=job.config,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        progress=job.progress,
        error=job.error,
        result=job.result
    )


def _run_training_job(job_id: str, config: TrainingConfig):
    """
    Background function to run training.

    Args:
        job_id: Job ID
        config: Training configuration
    """
    job_manager = get_job_manager()
    registry = Registry()

    try:
        # Update job status
        job_manager.update_job(job_id, status=JobStatus.RUNNING, log="Initializing training...")

        # Get base model
        try:
            base_entry = registry.get(config.base_model)
        except ModelNotFoundError:
            raise ValueError(f"Base model not found: {config.base_model}")

        # Validate dataset
        dataset_path = Path(config.dataset_path)
        if not dataset_path.exists():
            raise ValueError(f"Dataset not found: {config.dataset_path}")

        # Create trainer
        trainer = MLXTrainer(base_entry)

        # Run training with optimizations
        job_manager.update_job(job_id, log="Starting optimized LoRA training with gradient checkpointing...")

        output_path, metrics = trainer.train(
            dataset_path=dataset_path,
            output_name=config.output_name,
            epochs=config.epochs,
            batch_size=config.batch_size,
            lora_rank=config.lora_rank,
            lora_layers=config.lora_layers,
            learning_rate=config.learning_rate,
            gradient_checkpoint=config.gradient_checkpoint,
            max_seq_length=config.max_seq_length,
            val_batches=config.val_batches,
            steps_per_eval=config.steps_per_eval,
            job_id=job_id,
            job_manager=job_manager
        )

        # Register the trained adapter in the registry
        job_manager.update_job(job_id, log="Registering adapter model...")

        adapter_entry = ModelEntry(
            name=config.output_name,
            description=f"LoRA fine-tuned from {config.base_model}",
            type=ModelType.ADAPTER,
            parent=config.base_model,
            backend=ModelBackend.MLX,
            path=output_path
        )
        registry.add(adapter_entry)

        # Training completed successfully
        result = {
            "output_path": str(output_path),
            "base_model": config.base_model,
            "epochs": config.epochs,
            "adapter_name": config.output_name,
            "val_loss": metrics.get("val_loss", None)
        }

        job_manager.update_job(
            job_id,
            status=JobStatus.COMPLETED,
            result=result,
            log=f"Training completed! Adapter registered as: {config.output_name}"
        )

    except Exception as e:
        job_manager.update_job(
            job_id,
            status=JobStatus.FAILED,
            error=str(e),
            log=f"Training failed: {str(e)}"
        )


@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_training_job(request: StartTrainingRequest, background_tasks: BackgroundTasks):
    """
    Create and start a training job.

    The job runs in the background. Use GET /training/jobs/{id} to check progress.
    """
    job_manager = get_job_manager()

    # Create training config with optimizations
    config = TrainingConfig(
        base_model=request.base_model,
        dataset_path=request.dataset_path,
        output_name=request.output_name,
        epochs=request.epochs,
        batch_size=request.batch_size,
        lora_rank=request.lora_rank,
        lora_layers=request.lora_layers,
        learning_rate=request.learning_rate,
        gradient_checkpoint=request.gradient_checkpoint,
        max_seq_length=request.max_seq_length,
        val_batches=request.val_batches,
        steps_per_eval=request.steps_per_eval
    )

    # Create job
    job = job_manager.create_job(
        job_type=JobType.TRAINING,
        config=config.model_dump()
    )

    # Start training in background thread
    job_manager.start_job_thread(job.id, _run_training_job, config)

    return _job_to_response(job)


@router.post("/train", response_model=JobResponse, status_code=201)
async def upload_and_train(
    base_model: str = Form(...),
    output_name: str = Form(...),
    dataset: UploadFile = File(...),
    epochs: int = Form(3),
    batch_size: int = Form(2),
    lora_rank: int = Form(8),
    lora_layers: int = Form(16),
    learning_rate: float = Form(0.0001),
    gradient_checkpoint: bool = Form(True),
    max_seq_length: int = Form(2048),
    val_batches: int = Form(25),
    steps_per_eval: int = Form(100)
):
    """
    Upload a dataset and start a training job.

    This endpoint accepts file uploads via multipart/form-data for web UI.
    """
    job_manager = get_job_manager()

    # Create uploads directory if it doesn't exist
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)

    # Validate filename
    if not dataset.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename")

    # Save uploaded file with unique name
    file_id = str(uuid.uuid4())
    dataset_path = uploads_dir / f"{file_id}_{dataset.filename}"

    with dataset_path.open("wb") as f:
        shutil.copyfileobj(dataset.file, f)

    # Create training config with optimizations
    config = TrainingConfig(
        base_model=base_model,
        dataset_path=str(dataset_path),
        output_name=output_name,
        epochs=epochs,
        batch_size=batch_size,
        lora_rank=lora_rank,
        lora_layers=lora_layers,
        learning_rate=learning_rate,
        gradient_checkpoint=gradient_checkpoint,
        max_seq_length=max_seq_length,
        val_batches=val_batches,
        steps_per_eval=steps_per_eval
    )

    # Create job
    job = job_manager.create_job(
        job_type=JobType.TRAINING,
        config=config.model_dump()
    )

    # Start training in background thread
    job_manager.start_job_thread(job.id, _run_training_job, config)

    return _job_to_response(job)


@router.get("/jobs", response_model=JobListResponse)
async def list_training_jobs(
    status: Optional[JobStatus] = None,
    limit: int = 50
):
    """List training jobs with optional filtering."""
    job_manager = get_job_manager()
    jobs = job_manager.list_jobs(status=status, job_type=JobType.TRAINING, limit=limit)

    return JobListResponse(
        jobs=[_job_to_response(j) for j in jobs],
        total=len(jobs)
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_training_job(job_id: str):
    """Get status of a specific training job."""
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return _job_to_response(job)


@router.get("/jobs/{job_id}/logs", response_model=JobLogsResponse)
async def get_training_logs(job_id: str, tail: int = 100):
    """Get logs from a training job."""
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    # Return last N log lines (safe for empty lists)
    if tail > 0 and job.logs:
        logs = job.logs[-tail:]
    else:
        logs = job.logs

    return JobLogsResponse(
        id=job_id,
        logs=logs
    )


@router.delete("/jobs/{job_id}", status_code=204)
async def cancel_training_job(job_id: str):
    """Cancel a running training job."""
    job_manager = get_job_manager()

    if not job_manager.cancel_job(job_id):
        raise HTTPException(
            status_code=400,
            detail="Job not found or cannot be cancelled (already completed/failed)"
        )
