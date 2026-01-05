"""Training management."""
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path
import time


@dataclass
class TrainingJob:
    """
    Represents a training job.

    Attributes:
        id: Job ID
        type: Job type (training)
        status: Job status (pending, running, completed, failed)
        config: Training configuration dict
        created_at: Creation timestamp
        started_at: Start timestamp (optional)
        completed_at: Completion timestamp (optional)
        progress: Progress (0.0 - 1.0)
        error: Error message if failed
        result: Result dict if completed
    """

    id: str
    type: str
    status: str
    config: dict
    created_at: str
    progress: float
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    result: Optional[dict] = None


class TrainingManager:
    """
    Manages training jobs.

    Example:
        >>> client = AILabClient()
        >>> job = client.training.train(
        ...     base_model="qwen-1-5b",
        ...     output_name="my-model",
        ...     dataset_path="data.jsonl",
        ...     epochs=3
        ... )
        >>> job = client.training.wait_for_completion(job.id)
    """

    def __init__(self, client):
        self.client = client

    def train(
        self,
        base_model: str,
        output_name: str,
        dataset_path: str,
        epochs: int = 3,
        batch_size: int = 2,
        lora_rank: int = 8,
        lora_layers: int = 16,
        learning_rate: float = 0.0001,
    ) -> TrainingJob:
        """
        Start a training job.

        Args:
            base_model: Name of base model to fine-tune
            output_name: Name for the fine-tuned model
            dataset_path: Path to training dataset (JSONL)
            epochs: Number of training epochs (default: 3)
            batch_size: Training batch size (default: 2)
            lora_rank: LoRA rank (default: 8)
            lora_layers: Number of layers for LoRA (default: 16)
            learning_rate: Learning rate (default: 0.0001)

        Returns:
            TrainingJob object

        Example:
            >>> job = client.training.train(
            ...     base_model="qwen-1-5b",
            ...     output_name="my-finetuned-model",
            ...     dataset_path="/path/to/data.jsonl",
            ...     epochs=5
            ... )
            >>> print(job.id)
        """
        dataset_file = Path(dataset_path)
        if not dataset_file.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")

        # Upload file and start training
        with open(dataset_file, "rb") as f:
            files = {"dataset": (dataset_file.name, f, "application/x-jsonlines")}
            data = {
                "base_model": base_model,
                "output_name": output_name,
                "epochs": epochs,
                "batch_size": batch_size,
                "lora_rank": lora_rank,
                "lora_layers": lora_layers,
                "learning_rate": learning_rate,
            }

            # Use requests directly for multipart/form-data
            response = self.client.session.post(
                f"{self.client.base_url}/api/training/train",
                files=files,
                data=data,
                timeout=self.client.timeout,
            )
            response.raise_for_status()

        job_data = response.json()
        return TrainingJob(**job_data)

    def list_jobs(self, status: Optional[str] = None, limit: int = 50) -> List[TrainingJob]:
        """
        List training jobs.

        Args:
            status: Filter by status (pending, running, completed, failed)
            limit: Maximum number of jobs to return (default: 50)

        Returns:
            List of TrainingJob objects

        Example:
            >>> jobs = client.training.list_jobs(status="running")
            >>> for job in jobs:
            ...     print(f"{job.id}: {job.progress * 100}%")
        """
        params = {"limit": limit}
        if status:
            params["status"] = status

        response = self.client.get("/api/training/jobs", params=params)
        data = response.json()

        return [TrainingJob(**job_data) for job_data in data["jobs"]]

    def get_job(self, job_id: str) -> TrainingJob:
        """
        Get a specific training job.

        Args:
            job_id: Job ID

        Returns:
            TrainingJob object

        Example:
            >>> job = client.training.get_job("abc123")
            >>> print(job.status)
        """
        response = self.client.get(f"/api/training/jobs/{job_id}")
        return TrainingJob(**response.json())

    def get_logs(self, job_id: str, tail: int = 100) -> List[str]:
        """
        Get training job logs.

        Args:
            job_id: Job ID
            tail: Number of log lines to return (default: 100)

        Returns:
            List of log lines

        Example:
            >>> logs = client.training.get_logs("abc123", tail=50)
            >>> for log in logs:
            ...     print(log)
        """
        response = self.client.get(
            f"/api/training/jobs/{job_id}/logs",
            params={"tail": tail},
        )
        data = response.json()
        return data["logs"]

    def wait_for_completion(
        self,
        job_id: str,
        poll_interval: int = 5,
        timeout: Optional[int] = None,
    ) -> TrainingJob:
        """
        Wait for a training job to complete.

        Args:
            job_id: Job ID
            poll_interval: Seconds between status checks (default: 5)
            timeout: Maximum seconds to wait (default: None - no timeout)

        Returns:
            Completed TrainingJob object

        Raises:
            TimeoutError: If timeout is reached
            RuntimeError: If job fails

        Example:
            >>> job = client.training.train(...)
            >>> completed_job = client.training.wait_for_completion(
            ...     job.id,
            ...     poll_interval=10,
            ...     timeout=3600  # 1 hour
            ... )
            >>> print(completed_job.result)
        """
        start_time = time.time()

        while True:
            job = self.get_job(job_id)

            if job.status == "completed":
                return job
            elif job.status == "failed":
                raise RuntimeError(f"Training failed: {job.error}")

            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Training job {job_id} did not complete within {timeout}s")

            # Wait before next poll
            time.sleep(poll_interval)
