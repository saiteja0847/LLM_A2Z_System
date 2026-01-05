"""Background job management for training tasks."""
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import json
import threading
import uuid


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Job type enumeration."""
    TRAINING = "training"
    EVALUATION = "evaluation"
    EXPORT = "export"
    OPTIMIZATION = "optimization"


class TrainingConfig(BaseModel):
    """Training configuration with MLX optimizations."""
    base_model: str
    dataset_path: str
    output_name: str
    epochs: int = 3
    batch_size: int = 2
    lora_rank: int = 8
    lora_layers: int = 16
    learning_rate: float = 1e-4
    max_steps: Optional[int] = None
    gradient_checkpoint: bool = True
    max_seq_length: int = 2048
    val_batches: int = 25
    steps_per_eval: int = 100


class OptimizationJobConfig(BaseModel):
    """Configuration for optimization jobs."""
    base_model: str
    dataset_path: str
    num_trials: int = 20
    experiment_name: str = "lora_optimization"
    experiment_epochs: int = 1  # Fast 1-epoch training for trials


class Job(BaseModel):
    """Background job representation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: JobType
    status: JobStatus = JobStatus.PENDING
    config: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0
    logs: list[str] = Field(default_factory=list)
    result: Optional[Dict[str, Any]] = None


class JobManager:
    """Manage background training jobs."""

    def __init__(self, jobs_dir: Path = Path("jobs")):
        """
        Initialize job manager.

        Args:
            jobs_dir: Directory to store job data
        """
        self.jobs_dir = Path(jobs_dir)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.active_jobs: Dict[str, Job] = {}
        self.threads: Dict[str, threading.Thread] = {}
        
        # Load existing jobs
        self._load_jobs()

    def _load_jobs(self):
        """Load jobs from disk."""
        for job_file in self.jobs_dir.glob("*.json"):
            try:
                with open(job_file) as f:
                    data = json.load(f)
                    job = Job(**data)
                    self.active_jobs[job.id] = job
            except Exception:
                pass  # Skip corrupted job files

    def _save_job(self, job: Job):
        """Save job to disk."""
        job_file = self.jobs_dir / f"{job.id}.json"
        with open(job_file, "w") as f:
            json.dump(job.model_dump(mode="json"), f, indent=2, default=str)

    def create_job(self, job_type: JobType, config: Dict[str, Any]) -> Job:
        """
        Create a new job.

        Args:
            job_type: Type of job
            config: Job configuration

        Returns:
            Created job
        """
        job = Job(type=job_type, config=config)
        self.active_jobs[job.id] = job
        self._save_job(job)
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job if found, None otherwise
        """
        return self.active_jobs.get(job_id)

    def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        limit: int = 50
    ) -> list[Job]:
        """
        List jobs with optional filtering.

        Args:
            status: Filter by status
            job_type: Filter by type
            limit: Maximum number of jobs to return

        Returns:
            List of jobs
        """
        jobs = list(self.active_jobs.values())

        # Filter
        if status:
            jobs = [j for j in jobs if j.status == status]
        if job_type:
            jobs = [j for j in jobs if j.type == job_type]

        # Sort by created_at descending
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        return jobs[:limit]

    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        progress: Optional[float] = None,
        error: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        log: Optional[str] = None
    ):
        """
        Update job status and progress.

        Args:
            job_id: Job ID
            status: New status
            progress: Progress (0.0-1.0)
            error: Error message
            result: Job result
            log: Log message to append
        """
        job = self.active_jobs.get(job_id)
        if not job:
            return

        if status:
            job.status = status
            if status == JobStatus.RUNNING and not job.started_at:
                job.started_at = datetime.now()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                job.completed_at = datetime.now()

        if progress is not None:
            job.progress = max(0.0, min(1.0, progress))

        if error:
            job.error = error

        if result:
            job.result = result

        if log:
            job.logs.append(f"[{datetime.now().isoformat()}] {log}")

        self._save_job(job)

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.

        Args:
            job_id: Job ID

        Returns:
            True if cancelled, False if not found or already completed
        """
        job = self.active_jobs.get(job_id)
        if not job or job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
            return False

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now()
        self._save_job(job)

        # Stop thread if running
        if job_id in self.threads:
            # Note: Python threads can't be forcefully stopped
            # The training function should check job status periodically
            pass

        return True

    def start_job_thread(self, job_id: str, target_func, *args, **kwargs):
        """
        Start a job in a background thread.

        Args:
            job_id: Job ID
            target_func: Function to run
            *args: Positional arguments for target_func
            **kwargs: Keyword arguments for target_func
        """
        def wrapped_target():
            try:
                target_func(job_id, *args, **kwargs)
            except Exception as e:
                self.update_job(job_id, status=JobStatus.FAILED, error=str(e))

        thread = threading.Thread(target=wrapped_target, daemon=True)
        self.threads[job_id] = thread
        thread.start()

    def cleanup_completed(self, keep_recent: int = 100):
        """
        Remove old completed jobs.

        Args:
            keep_recent: Number of recent jobs to keep
        """
        completed = [
            j for j in self.active_jobs.values()
            if j.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
        ]
        completed.sort(key=lambda j: j.created_at, reverse=True)

        # Remove old ones
        for job in completed[keep_recent:]:
            job_file = self.jobs_dir / f"{job.id}.json"
            if job_file.exists():
                job_file.unlink()
            del self.active_jobs[job.id]

    def create_optimization_job(
        self,
        base_model: str,
        dataset_path: str,
        num_trials: int = 20,
        experiment_name: str = "lora_optimization",
        experiment_epochs: int = 1,
    ) -> Job:
        """
        Create an optimization job.

        Args:
            base_model: Base model name
            dataset_path: Path to training dataset
            num_trials: Number of optimization trials
            experiment_name: Name of experiment
            experiment_epochs: Epochs per trial (use 1 for speed)

        Returns:
            Created optimization job
        """
        config = OptimizationJobConfig(
            base_model=base_model,
            dataset_path=dataset_path,
            num_trials=num_trials,
            experiment_name=experiment_name,
            experiment_epochs=experiment_epochs,
        )

        job = self.create_job(JobType.OPTIMIZATION, config.model_dump())
        self.update_job(job.id, log=f"Optimization job created with {num_trials} trials")

        return job

    def run_optimization_job(
        self,
        job_id: str,
        training_function,
    ):
        """
        Run an optimization job.

        Args:
            job_id: Job ID
            training_function: Function that takes parameters and returns (loss, sem)
        """
        from .optimization import AxOptimizer, OptimizationConfig

        job = self.get_job(job_id)
        if not job or job.type != JobType.OPTIMIZATION:
            return

        try:
            self.update_job(job_id, status=JobStatus.RUNNING, log="Starting optimization...")

            config = OptimizationJobConfig(**job.config)

            # Create optimizer config
            opt_config = OptimizationConfig(
                experiment_name=config.experiment_name,
                num_trials=config.num_trials,
                experiment_epochs=config.experiment_epochs,
            )

            # Create optimizer
            optimizer = AxOptimizer(config=opt_config)

            # Run optimization
            best_params = optimizer.optimize(training_function)

            # Get parameter importance
            importance = optimizer.get_parameter_importance()

            # Update job with results
            self.update_job(
                job_id,
                status=JobStatus.COMPLETED,
                progress=1.0,
                result={
                    "best_parameters": best_params,
                    "parameter_importance": importance,
                },
                log=f"Optimization complete. Best parameters: {best_params}",
            )

        except Exception as e:
            import traceback
            self.update_job(
                job_id,
                status=JobStatus.FAILED,
                error=str(e),
                log=f"Optimization failed: {str(e)}\n{traceback.format_exc()}",
            )


# Global job manager instance
_job_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """Get the global job manager instance."""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager
