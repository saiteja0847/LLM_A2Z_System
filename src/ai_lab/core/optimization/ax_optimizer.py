"""Ax hyperparameter optimizer for LoRA fine-tuning."""

from pathlib import Path
from typing import Dict, Any, Callable, Optional, Tuple
from pydantic import BaseModel, Field
import json


class OptimizationConfig(BaseModel):
    """Configuration for Ax optimization experiment."""

    # Experiment settings
    experiment_name: str = "lora_optimization"
    num_trials: int = 20
    objective_metric: str = "loss"

    # LoRA parameter search space
    learning_rate_range: Tuple[float, float] = (1e-5, 1e-3)
    lora_rank_choices: list[int] = [4, 8, 16, 32, 64]
    lora_alpha_range: Tuple[int, int] = (8, 128)
    batch_size_choices: list[int] = [1, 2, 4]
    epochs_range: Tuple[int, int] = (1, 10)
    warmup_ratio_range: Tuple[float, float] = (0.0, 0.2)

    # Training settings for fast experiments
    experiment_epochs: int = 1  # Use 1 epoch for fast trials


class OptimizationResult(BaseModel):
    """Results from an optimization trial."""

    trial_index: int
    parameters: Dict[str, Any]
    objective_mean: float
    objective_sem: float = 0.0
    training_time_seconds: float = 0.0


class AxOptimizer:
    """
    Bayesian optimization using Ax for LoRA hyperparameter tuning.

    Example:
        optimizer = AxOptimizer()
        best_params = optimizer.optimize(
            model="qwen-1-5b",
            dataset="data.jsonl",
            training_function=train_with_params
        )
    """

    def __init__(
        self,
        config: Optional[OptimizationConfig] = None,
        output_dir: Path = Path("jobs/optimization"),
    ):
        """
        Initialize Ax optimizer.

        Args:
            config: Optimization configuration
            output_dir: Directory to save optimization results
        """
        self.config = config or OptimizationConfig()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Ax client (lazy import to avoid slow startup)
        self.ax_client = None
        self.trials: list[OptimizationResult] = []

    def create_experiment(self):
        """Create Ax experiment with LoRA search space."""
        from ax.service.ax_client import AxClient
        from ax.service.utils.instantiation import ObjectiveProperties

        self.ax_client = AxClient()

        self.ax_client.create_experiment(
            name=self.config.experiment_name,
            parameters=[
                {
                    "name": "learning_rate",
                    "type": "range",
                    "bounds": self.config.learning_rate_range,
                    "log_scale": True,
                    "value_type": "float",
                },
                {
                    "name": "lora_r",
                    "type": "choice",
                    "values": self.config.lora_rank_choices,
                    "value_type": "int",
                    "is_ordered": True,
                },
                {
                    "name": "lora_alpha",
                    "type": "range",
                    "bounds": self.config.lora_alpha_range,
                    "value_type": "int",
                },
                {
                    "name": "batch_size",
                    "type": "choice",
                    "values": self.config.batch_size_choices,
                    "value_type": "int",
                    "is_ordered": True,
                },
                {
                    "name": "epochs",
                    "type": "range",
                    "bounds": self.config.epochs_range,
                    "value_type": "int",
                },
                {
                    "name": "warmup_ratio",
                    "type": "range",
                    "bounds": self.config.warmup_ratio_range,
                    "value_type": "float",
                },
            ],
            objectives={
                self.config.objective_metric: ObjectiveProperties(minimize=True)
            },
        )

    def run_trial(
        self,
        parameters: Dict[str, Any],
        training_function: Callable[[Dict[str, Any]], Tuple[float, float]],
    ) -> OptimizationResult:
        """
        Run a single optimization trial.

        Args:
            parameters: Trial parameters from Ax
            training_function: Function that trains model and returns (loss, sem)

        Returns:
            OptimizationResult with trial results
        """
        import time

        start_time = time.time()

        # Call training function with parameters
        objective_mean, objective_sem = training_function(parameters)

        training_time = time.time() - start_time

        result = OptimizationResult(
            trial_index=len(self.trials),
            parameters=parameters,
            objective_mean=objective_mean,
            objective_sem=objective_sem,
            training_time_seconds=training_time,
        )

        self.trials.append(result)
        return result

    def optimize(
        self,
        training_function: Callable[[Dict[str, Any]], Tuple[float, float]],
    ) -> Dict[str, Any]:
        """
        Run full optimization loop.

        Args:
            training_function: Function that takes parameters and returns (loss, sem)

        Returns:
            Best parameters found
        """
        # Create experiment
        self.create_experiment()

        print(f"🔍 Running {self.config.num_trials} optimization trials...")

        # Run trials
        for i in range(self.config.num_trials):
            print(f"  Trial {i + 1}/{self.config.num_trials}...", end=" ")

            # Get next trial parameters from Ax
            parameters, trial_index = self.ax_client.get_next_trial()

            # Run training with these parameters
            result = self.run_trial(parameters, training_function)

            # Complete trial in Ax
            self.ax_client.complete_trial(
                trial_index=trial_index,
                raw_data=result.objective_mean,
            )

            print(f"loss={result.objective_mean:.4f}")

        # Get best parameters
        best_parameters, best_values = self.ax_client.get_best_parameters()

        print(f"\n✅ Optimization complete!")
        print(f"   Best {self.config.objective_metric}: {best_values[0][self.config.objective_metric]:.4f}")

        # Save results
        self._save_results(best_parameters, best_values[0])

        return best_parameters

    def get_best_parameters(self) -> Dict[str, Any]:
        """Get best parameters from completed optimization."""
        if self.ax_client is None:
            raise RuntimeError("No experiment has been run. Call optimize() first.")

        best_parameters, best_values = self.ax_client.get_best_parameters()
        return best_parameters

    def get_parameter_importance(self) -> Dict[str, float]:
        """Get importance of each parameter."""
        if self.ax_client is None:
            raise RuntimeError("No experiment has been run. Call optimize() first.")

        try:
            importance = self.ax_client.get_feature_importances()
            return importance.get(self.config.objective_metric, {})
        except Exception:
            return {}

    def _save_results(self, best_parameters: Dict[str, Any], best_values: Dict[str, float]):
        """Save optimization results to disk."""
        results = {
            "config": self.config.model_dump(),
            "best_parameters": best_parameters,
            "best_values": best_values,
            "trials": [r.model_dump() for r in self.trials],
            "parameter_importance": self.get_parameter_importance(),
        }

        results_file = self.output_dir / f"{self.config.experiment_name}_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"   Results saved to: {results_file}")
