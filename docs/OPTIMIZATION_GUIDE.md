# Optimization Guide: Hyperparameter Tuning

## Overview

The AI Lab platform integrates the **Ax platform** for intelligent hyperparameter optimization. Automatically find the best training parameters (learning rate, rank, batch size, etc.) using state-of-the-art optimization algorithms.

## Key Features

✅ **Automated Search** — Ax finds optimal hyperparameters automatically
✅ **Multi-Objective** — Optimize for multiple metrics (loss, time, memory)
✅ **Parallel Trials** — Run multiple experiments concurrently
✅ **Smart Algorithms** — Bayesian optimization, MOO, adaptive strategies
✅ **MLX Integration** — Direct integration with MLX training backend
✅ **Web UI** — Visualize optimization results and progress
✅ **CLI & API** — Run optimizations from command line or API

## What is Hyperparameter Optimization?

Hyperparameter optimization (HPO) automatically finds the best training configuration:

```python
# Manual approach (slow):
Try learning_rate=1e-4 → 80% accuracy
Try learning_rate=1e-3 → 85% accuracy
Try learning_rate=1e-2 → 60% accuracy
Best: 1e-3

# Ax approach (fast, smart):
Tell Ax: Optimize learning_rate, rank, batch_size
Ax runs 20 trials intelligently
Returns: Best configuration found
```

## Quick Start

### 1. Define Search Space

Create a configuration file `optimization_config.yaml`:

```yaml
# search_config.yaml
parameters:
  learning_rate:
    type: range
    bounds: [1e-5, 1e-3]
    log_scale: true

  lora_rank:
    type: choice
    values: [4, 8, 16, 32]

  batch_size:
    type: choice
    values: [2, 4, 8]

  lora_alpha:
    type: fixed
    value: 16  # alpha = 2 * rank

experiment:
  model: qwen3-4b-instruct
  dataset: training_data.jsonl
  epochs: 3
  max_trials: 20
  objective_metric: val_loss
  direction: minimize  # lower is better
```

### 2. Run Optimization (CLI)

```bash
lab optimize start \
  --config search_config.yaml \
  --output optimization-results \
  --trials 20 \
  --parallel 2
```

**What Happens:**

1. Ax generates intelligent trial configurations
2. Multiple training jobs run in parallel (2 at a time)
3. Each trial evaluates different hyperparameters
4. Progress updates in real-time
5. Best configuration saved to `optimization-results/`

### 3. Monitor Progress

```bash
# List all optimization jobs
lab optimize list

# Check job status
lab optimize status <job-id>

# View trials
lab optimize trials <job-id>

# Output:
# Trial 1/20: lr=1e-4, rank=8, batch=4 → val_loss=0.312 ✓
# Trial 2/20: lr=5e-5, rank=16, batch=2 → val_loss=0.298 ✓
# Trial 3/20: lr=2e-4, rank=4, batch=8 → val_loss=0.345 ✓
# ...
# Best: Trial 7 → val_loss=0.234
```

### 4. Use Best Configuration

```bash
# Train with best hyperparameters
lab train start \
  --model qwen3-4b-instruct \
  --dataset training_data.jsonl \
  --output best-model \
  --learning-rate 0.000123 \
  --lora-rank 16 \
  --batch-size 4
```

## Search Space Parameters

### Range Parameters

Continuous or integer ranges:

```yaml
parameters:
  learning_rate:
    type: range
    bounds: [1e-5, 1e-3]
    log_scale: true  # Sample log-uniformly

  dropout_rate:
    type: range
    bounds: [0.0, 0.2]

  max_seq_length:
    type: range
    bounds: [512, 2048]
    log_scale: false
```

### Choice Parameters

Discrete options:

```yaml
parameters:
  lora_rank:
    type: choice
    values: [4, 8, 16, 32]

  batch_size:
    type: choice
    values: [2, 4, 8]

  optimizer:
    type: choice
    values: ["adamw", "sgd", "adam"]
```

### Fixed Parameters

Values that don't change:

```yaml
parameters:
  lora_alpha:
    type: fixed
    value: 16

  epochs:
    type: fixed
    value: 3
```

### Conditional Parameters

Dependent on other parameters:

```yaml
parameters:
  batch_size:
    type: choice
    values: [2, 4, 8]

  grad_accumulation:
    type: choice
    values: [1, 2, 4]
    depends_on:
      parameter: batch_size
      # Only test certain combinations
```

## Optimization Strategies

### Bayesian Optimization (Default)

Smart exploration using Gaussian Process models:

```yaml
strategy:
  type: bayesian
  initial_trials: 5  # Random trials first
```

**Best for:** Expensive evaluations, smooth parameter spaces

### Random Search

Simple random sampling:

```yaml
strategy:
  type: random
```

**Best for:** Baseline comparison, quick tests

### Multi-Objective Optimization

Optimize multiple metrics simultaneously:

```yaml
objectives:
  - name: val_loss
    direction: minimize
    weight: 1.0

  - name: training_time
    direction: minimize
    weight: 0.5

  - name: memory_usage
    direction: minimize
    weight: 0.3

strategy:
  type: moo  # Multi-objective optimization
  algorithm: ehvi  # Expected Hypervolume Improvement
```

**Best for:** Balancing accuracy, speed, and memory

## Configuration Examples

### Example 1: Learning Rate Search

```yaml
# lr_search.yaml
parameters:
  learning_rate:
    type: range
    bounds: [1e-5, 1e-3]
    log_scale: true

experiment:
  model: qwen3-4b-instruct
  dataset: instruction_data.jsonl
  fixed_params:
    lora_rank: 8
    batch_size: 4
    epochs: 3
  max_trials: 15
  parallel: 2
```

### Example 2: Full Architecture Search

```yaml
# full_search.yaml
parameters:
  learning_rate:
    type: range
    bounds: [5e-5, 5e-4]
    log_scale: true

  lora_rank:
    type: choice
    values: [4, 8, 16, 32]

  lora_alpha:
    type: choice
    values: [8, 16, 32, 64]

  lora_dropout:
    type: range
    bounds: [0.0, 0.1]

  batch_size:
    type: choice
    values: [2, 4, 8]

experiment:
  model: qwen3-4b-instruct
  dataset: domain_data.jsonl
  epochs: 3
  max_trials: 50
  parallel: 4  # Run 4 trials at once
  objective_metrics:
    - val_loss
    - training_time
  direction: minimize
```

### Example 3: Memory-Constrained Search

```yaml
# memory_optimized.yaml
parameters:
  learning_rate:
    type: range
    bounds: [1e-5, 1e-3]
    log_scale: true

  lora_rank:
    type: choice
    values: [4, 8]  # Smaller ranks only

  batch_size:
    type: choice
    values: [1, 2]  # Smaller batches

  max_seq_length:
    type: choice
    values: [512, 1024, 2048]

experiment:
  model: qwen3-4b-instruct
  dataset: training_data.jsonl
  epochs: 2
  max_trials: 20
  parallel: 2
  constraints:
    max_memory_gb: 8  # Reject trials using >8GB
```

## Web UI Optimization

### 1. Navigate to Optimization Page

Open http://localhost:5173 and click "Optimization"

### 2. Create Optimization Job

- **Model**: Select base model
- **Dataset**: Upload or select dataset
- **Search Space**: Configure parameters
  - Add range parameters
  - Add choice parameters
  - Set bounds/values

### 3. Configure Experiment

- **Max Trials**: 20-50 (more trials = better results)
- **Parallel Jobs**: 2-4 (don't exceed available memory)
- **Objective**: Select metric to optimize
- **Direction**: minimize (loss) or maximize (accuracy)

### 4. Monitor Progress

Real-time visualization:
- Trial progress bar
- Objective value over time
- Best configuration highlight
- Parallelization status

### 5. Analyze Results

After completion:
- View all trials table
- Sort by objective value
- Compare configurations
- View convergence plot
- Export best configuration

## API Reference

### Start Optimization

```bash
POST /api/optimization/start

Body:
{
  "model": "qwen3-4b-instruct",
  "dataset_path": "training_data.jsonl",
  "parameters": {
    "learning_rate": {"type": "range", "bounds": [1e-5, 1e-3], "log_scale": true},
    "lora_rank": {"type": "choice", "values": [4, 8, 16, 32]},
    "batch_size": {"type": "choice", "values": [2, 4, 8]}
  },
  "experiment": {
    "max_trials": 20,
    "parallel": 2,
    "objective_metric": "val_loss",
    "direction": "minimize"
  },
  "fixed_params": {
    "epochs": 3,
    "lora_alpha": 16
  }
}

Response:
{
  "job_id": "opt-abc123...",
  "status": "started",
  "message": "Optimization job started"
}
```

### Get Optimization Status

```bash
GET /api/optimization/jobs/{job_id}

Response:
{
  "job_id": "opt-abc123...",
  "status": "running",
  "progress": 45,
  "completed_trials": 9,
  "total_trials": 20,
  "best_trial": {
    "trial_number": 7,
    "parameters": {
      "learning_rate": 0.000123,
      "lora_rank": 16,
      "batch_size": 4
    },
    "objectives": {
      "val_loss": 0.234
    }
  }
}
```

### Get All Trials

```bash
GET /api/optimization/jobs/{job_id}/trials

Response:
{
  "trials": [
    {
      "trial_number": 1,
      "parameters": {"learning_rate": 0.0001, "lora_rank": 8, "batch_size": 4},
      "objectives": {"val_loss": 0.312},
      "status": "completed"
    },
    {
      "trial_number": 2,
      "parameters": {"learning_rate": 0.0002, "lora_rank": 16, "batch_size": 2},
      "objectives": {"val_loss": 0.298},
      "status": "completed"
    }
  ]
}
```

## Interpreting Results

### Trial Progression

```
Trial 1: lr=1e-4, rank=8, batch=4 → val_loss=0.312 (baseline)
Trial 2: lr=5e-5, rank=16, batch=2 → val_loss=0.298 (+4%)
Trial 3: lr=2e-4, rank=4, batch=8 → val_loss=0.345 (-10%)
Trial 4: lr=1.2e-4, rank=16, batch=4 → val_loss=0.276 (+12%)
Trial 5: lr=8e-5, rank=8, batch=2 → val_loss=0.301 (+3%)
Trial 6: lr=1.5e-4, rank=32, batch=4 → val_loss=0.267 (+14%)
Trial 7: lr=1.23e-4, rank=16, batch=4 → val_loss=0.234 (+25%) ⭐ BEST
```

### Convergence Analysis

```bash
# Check if optimization converged
lab optimize analyze <job-id>

# Output:
# Convergence: Trial 7 (35% through search)
# Plateau: Last 5 trials improved <2%
# Recommendation: Can stop early, best config found
```

### Parameter Importance

```python
# Ax provides sensitivity analysis
learning_rate: High importance (78%)
lora_rank: Medium importance (45%)
batch_size: Low importance (12%)

# Focus future search on learning_rate
```

## Best Practices

### 1. Start Simple

```yaml
# Begin with narrow search
learning_rate: [1e-4, 1e-3]  # Narrow range
lora_rank: [8, 16]            # 2 options
max_trials: 10               # Quick test
```

### 2. Expand Gradually

```yaml
# After initial search, expand around best
learning_rate: [best*0.5, best*2]  # Zoom in
lora_rank: [4, 8, 16, 32]          # Add options
max_trials: 30                     # More thorough
```

### 3. Use Constraints

```yaml
# Avoid invalid configurations
constraints:
  max_memory_gb: 8
  min_throughput: 20  # tokens/sec
  max_training_time: 3600  # seconds
```

### 4. Multi-Objective for Balance

```yaml
# Don't just optimize accuracy
objectives:
  val_loss: minimize (weight 1.0)
  training_time: minimize (weight 0.5)
  memory_usage: minimize (weight 0.3)

# Result: Best trade-off, not just best accuracy
```

### 5. Parallel Wisely

```yaml
# Rule: parallel = min(4, available_memory_gb / 4)
parallel: 2  # For 16GB system
parallel: 4  # For 32GB system
parallel: 1  # For 8GB system
```

## Troubleshooting

### No Improvement

```bash
# Problem: Best trial = first trial
# Solutions:
1. Expand search bounds
2. Try different parameter types (range vs choice)
3. Check if fixed parameters are limiting
4. Increase max_trials
```

### Slow Optimization

```bash
# Problem: Trials taking too long
# Solutions:
1. Reduce epochs per trial: epochs: 1
2. Use subset of data: dataset: train_10%.jsonl
3. Reduce max_seq_length
4. Increase parallel (if memory allows)
```

### Out of Memory

```bash
# Problem: Parallel trials OOM
# Solutions:
1. Reduce parallel: parallel: 1
2. Add memory constraint: max_memory_gb: 6
3. Reduce parameter ranges (smaller models)
```

### All Trials Failing

```bash
# Problem: Every trial errors out
# Common causes:
1. Invalid parameter ranges
2. Dataset formatting issues
3. Model loading problems
4. Insufficient memory for all configs

# Solution: Test one config manually first
lab train start --model ... --dataset ...
# If this works, problem is in search space
```

## Advanced Topics

### Warm-Starting Optimization

```python
# Use previous results to guide new search
from ai_lab.core.optimization import warm_start

warm_start(
  previous_results="optimization-results-1/",
  new_config="search_config_2.yaml"
)
```

### Early Stopping

```yaml
# Stop if no improvement
experiment:
  stopping_strategy:
    type: improvement
    patience: 5  # Stop after 5 trials without >1% improvement
```

### Multi-Fidelity Optimization

```yaml
# Use cheap approximations first
experiment:
  multi_fidelity:
    max_resource: "epochs: 3"
    min_resource: "epochs: 1"
    reduction_factor: 3  # SHA algorithm
```

## See Also

- [Training Guide](TRAINING_GUIDE.md) — LoRA fine-tuning basics
- [Model Management](MODEL_MANAGEMENT.md) — Base model setup
- [API Reference](API_REFERENCE.md) — Complete optimization API
- [Web UI Guide](WEB_UI_GUIDE.md) — Visual optimization interface
