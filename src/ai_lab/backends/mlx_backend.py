"""MLX backend for Apple Silicon inference and training."""
import logging
import subprocess
from typing import TYPE_CHECKING, Generator, Optional
from pathlib import Path

from ..core.inference import InferenceClient
from ..core.registry import ModelEntry, ModelType


if TYPE_CHECKING:
    from ..core.jobs import JobManager


logger = logging.getLogger(__name__)


class MLXClient(InferenceClient):
    """MLX inference backend for Apple Silicon."""

    def __init__(self, entry: ModelEntry):
        """
        Initialize MLX client.

        Args:
            entry: Model registry entry
        """
        super().__init__(entry)
        self._resolve_paths()

    def _resolve_paths(self):
        """Resolve base and adapter paths."""
        if self.entry.type == ModelType.ADAPTER:
            # For adapters, load parent model + adapter weights
            from ..core.registry import Registry
            registry = Registry()
            parent = registry.get(self.entry.parent)
            self.base_path = parent.path
            self.adapter_path = self.entry.path
        else:
            # For base models, just load the model
            self.base_path = self.entry.path
            self.adapter_path = None

    def complete(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate completion using mlx_lm.generate.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional mlx_lm parameters

        Returns:
            Generated text
        """
        cmd = [
            "python3", "-m", "mlx_lm.generate",
            "--model", str(self.base_path),
            "--prompt", prompt,
            "--max-tokens", str(max_tokens),
            "--temp", str(temperature),
        ]

        if self.adapter_path:
            cmd.extend(["--adapter-path", str(self.adapter_path)])

        # Add any extra kwargs as CLI args
        for key, value in kwargs.items():
            cmd.extend([f"--{key.replace('_', '-')}", str(value)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300  # 5 minute timeout
            )
            # Parse MLX output to extract just the generated text
            # MLX wraps the output in ========== markers
            output = result.stdout.strip()
            if "==========" in output:
                # Extract text between the ========== markers
                parts = output.split("==========")
                if len(parts) >= 3:
                    return parts[1].strip()
            return output
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"MLX generation failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("MLX generation timed out after 5 minutes")

    def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Stream completion tokens.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Yields:
            Generated token strings
        """
        cmd = [
            "python3", "-m", "mlx_lm.generate",
            "--model", str(self.base_path),
            "--prompt", prompt,
            "--max-tokens", str(max_tokens),
            "--temp", str(temperature),
        ]

        if self.adapter_path:
            cmd.extend(["--adapter-path", str(self.adapter_path)])

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Stream output line by line, filtering MLX debug output
            skip_patterns = ["Calling `python", "==========", "Prompt:", "Generation:", "Peak memory:"]
            for line in process.stdout:
                line = line.strip()
                if line and not any(pattern in line for pattern in skip_patterns):
                    yield line

            process.wait()
            if process.returncode != 0:
                stderr = process.stderr.read()
                raise RuntimeError(f"MLX streaming failed: {stderr}")

        except (OSError, subprocess.SubprocessError) as e:
            raise RuntimeError(f"MLX streaming error: {str(e)}")

    def chat(
        self,
        messages: list[dict],
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Generated response
        """
        # Format messages according to chat template
        prompt = self._format_chat(messages)
        return self.complete(prompt, max_tokens, temperature, **kwargs)

    def _format_chat(self, messages: list[dict]) -> str:
        """
        Format messages according to chat template.

        Args:
            messages: List of message dicts

        Returns:
            Formatted prompt string
        """
        template = self.entry.chat_template or "chatml"

        if template == "chatml":
            # ChatML format: <|im_start|>role\ncontent<|im_end|>
            formatted = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                formatted.append(f"<|im_start|>{role}\n{content}<|im_end|>")
            formatted.append("<|im_start|>assistant\n")
            return "\n".join(formatted)

        elif template == "llama2":
            # Llama 2 format: [INST] prompt [/INST]
            formatted = []
            for msg in messages:
                if msg.get("role") == "user":
                    formatted.append(f"[INST] {msg.get('content', '')} [/INST]")
                elif msg.get("role") == "assistant":
                    formatted.append(msg.get("content", ""))
            return " ".join(formatted)

        elif template == "alpaca":
            # Alpaca format
            formatted = []
            for msg in messages:
                if msg.get("role") == "system":
                    formatted.append(f"### Instruction:\n{msg.get('content', '')}\n")
                elif msg.get("role") == "user":
                    formatted.append(f"### Input:\n{msg.get('content', '')}\n")
                elif msg.get("role") == "assistant":
                    formatted.append(f"### Response:\n{msg.get('content', '')}\n")
            formatted.append("### Response:\n")
            return "\n".join(formatted)

        else:
            # Default: just concatenate with role prefixes
            formatted = []
            for msg in messages:
                role = msg.get("role", "user").capitalize()
                content = msg.get("content", "")
                formatted.append(f"{role}: {content}")
            formatted.append("Assistant:")
            return "\n".join(formatted)


class MLXTrainer:
    """MLX LoRA training for Apple Silicon."""

    def __init__(self, base_entry: ModelEntry):
        """
        Initialize trainer.

        Args:
            base_entry: Base model registry entry
        """
        self.base_entry = base_entry

    def train(
        self,
        dataset_path: Path,
        output_name: str,
        epochs: int = 1,
        batch_size: int = 1,
        lora_rank: int = 8,
        lora_layers: int = 16,
        learning_rate: float = 1e-5,
        job_id: Optional[str] = None,
        job_manager: Optional["JobManager"] = None,
        gradient_checkpoint: bool = True,
        max_seq_length: int = 2048,
        val_batches: int = 25,
        steps_per_eval: int = 100,
        **kwargs
    ) -> tuple[Path, dict[str, float]]:
        """
        Run optimized LoRA training and return output path with metrics.

        Args:
            dataset_path: Path to training dataset (JSONL)
            output_name: Name for output adapter
            epochs: Number of training epochs
            batch_size: Training batch size
            lora_rank: LoRA rank (default: 8)
            lora_layers: Number of layers to apply LoRA
            learning_rate: Learning rate
            job_id: Optional job ID for progress tracking
            job_manager: Optional job manager instance
            gradient_checkpoint: Enable gradient checkpointing for memory efficiency
            max_seq_length: Maximum sequence length for training
            val_batches: Number of validation batches
            steps_per_eval: Steps between evaluations
            **kwargs: Additional training parameters

        Returns:
            Tuple of (path to trained adapter weights, metrics dict with val_loss)

        Raises:
            RuntimeError: If training fails
        """
        output_path = Path("models") / output_name
        output_path.mkdir(parents=True, exist_ok=True)

        # Calculate iterations based on dataset size and epochs
        # For now, use conservative estimate - MLX will auto-adjust
        iters = epochs * 1000

        # Track validation loss from MLX output
        final_val_loss = None

        cmd = [
            "python3", "-m", "mlx_lm.lora",
            "--model", str(self.base_entry.path),
            "--train",  # Required flag for training mode
            "--data", str(dataset_path),
            "--adapter-path", str(output_path),
            "--iters", str(iters),
            "--batch-size", str(batch_size),
            "--num-layers", str(lora_layers),
            "--learning-rate", str(learning_rate),
            "--max-seq-length", str(max_seq_length),
            "--val-batches", str(val_batches),
            "--steps-per-eval", str(steps_per_eval),
        ]

        # Enable gradient checkpointing for memory efficiency (especially on M4 with 16GB)
        if gradient_checkpoint:
            cmd.append("--grad-checkpoint")

        # Create adapter config file for LoRA rank configuration
        import json
        adapter_config = {
            "lora_parameters": {
                "rank": lora_rank,
                "alpha": lora_rank * 2,  # Common practice: alpha = 2 * rank
                "dropout": 0.0,
                "scale": 20.0
            }
        }

        config_path = output_path / "lora_config.json"
        with open(config_path, 'w') as f:
            json.dump(adapter_config, f, indent=2)

        # Add any extra kwargs
        for key, value in kwargs.items():
            cmd.extend([f"--{key.replace('_', '-')}", str(value)])

        # Update job status if provided
        if job_id and job_manager:
            job_manager.update_job(job_id, log=f"Starting training with command: {' '.join(cmd)}")

        try:
            # Use Popen for real-time output monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Monitor output for progress
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break

                line = line.strip()
                if line:
                    # Log to console
                    logger.info(line)

                    # Parse validation loss from MLX output
                    # MLX outputs validation loss in format: "Val loss: X.XXX" or "Val Loss: X.XXX"
                    if "Val loss" in line.lower() or "val_loss" in line.lower():
                        try:
                            # Extract numeric value from line
                            # Expected formats: "Val loss: 2.345", "Val Loss: 2.345", etc.
                            parts = line.lower().split("val loss")
                            if len(parts) > 1:
                                colon_parts = parts[1].split(":")
                                if len(colon_parts) > 1:
                                    value_parts = colon_parts[1].strip().split()
                                    if len(value_parts) > 0:
                                        loss_str = value_parts[0]
                                        final_val_loss = float(loss_str)
                        except (ValueError, IndexError):
                            pass  # Failed to parse loss, continue

                    # Update job progress if manager provided
                    if job_id and job_manager:
                        # Parse progress from MLX output
                        # MLX outputs: "Iter X: ..." where X is iteration number
                        if "Iter" in line and ":" in line:
                            try:
                                iter_part = line.split("Iter")[1].split(":")[0].strip()
                                current_iter = int(iter_part)
                                progress = min(0.99, current_iter / iters)
                                job_manager.update_job(job_id, progress=progress, log=line)
                            except (ValueError, IndexError):
                                job_manager.update_job(job_id, log=line)
                        else:
                            job_manager.update_job(job_id, log=line)

            process.wait()

            if process.returncode != 0:
                raise RuntimeError(f"MLX training failed with code {process.returncode}")

            # Mark as complete
            if job_id and job_manager:
                job_manager.update_job(job_id, progress=1.0, log="Training completed successfully")

            # Return path and metrics
            metrics = {}
            if final_val_loss is not None:
                metrics["val_loss"] = final_val_loss
            else:
                # If we couldn't parse loss, use a default high value
                metrics["val_loss"] = 999.0

            return output_path, metrics

        except Exception as e:
            if job_id and job_manager:
                job_manager.update_job(job_id, log=f"Training failed: {str(e)}")
            raise RuntimeError(f"MLX training failed: {e}")

    def validate_dataset(self, dataset_path: Path) -> bool:
        """
        Validate dataset format.

        Args:
            dataset_path: Path to dataset

        Returns:
            True if valid

        Raises:
            ValueError: If dataset is invalid
        """
        if not dataset_path.exists():
            raise ValueError(f"Dataset not found: {dataset_path}")

        if not dataset_path.suffix == ".jsonl":
            raise ValueError("Dataset must be JSONL format")

        # TODO: Add more validation (check JSON structure, required fields)

        return True
