# Training Guide: LoRA Fine-Tuning

## Overview

The AI Lab platform provides complete LoRA (Low-Rank Adaptation) training capabilities for Apple Silicon using MLX. Fine-tune large language models on your custom datasets with minimal computational overhead.

## Key Features

✅ **LoRA Training** — Efficient fine-tuning with minimal memory
✅ **MLX Acceleration** — GPU-optimized training on Apple Silicon
✅ **Background Jobs** — Train asynchronously, monitor progress
✅ **Hyperparameter Control** — Full control over rank, alpha, learning rate
✅ **Validation Tracking** — Monitor loss on validation dataset
✅ **CLI & Web UI** — Train via command line or web interface
✅ **Automatic Registration** — Trained adapters auto-register for inference

## What is LoRA?

LoRA (Low-Rank Adaptation) is a parameter-efficient fine-tuning method:

- **Instead of**: Updating all billions of parameters (expensive, slow)
- **LoRA adds**: Small adapter layers (~1-2% of model size)
- **Benefits**: Train in GBs instead of 100s of GBs, faster training

```python
# Example: Training a 4B parameter model
# Full fine-tuning: 4B parameters × 4 bytes = 16 GB
# LoRA fine-tuning: ~10M parameters × 4 bytes = 40 MB
# Memory savings: 99.75%
```

## Quick Start

### 1. Prepare Training Data

Create a JSONL file with training examples:

```jsonl
{"text": "User: What is the capital of France?\nAssistant: Paris."}
{"text": "User: Explain photosynthesis.\nAssistant: Photosynthesis is the process..."}
{"text": "User: How do I bake a cake?\nAssistant: To bake a cake, you need..."}
```

**Format Options:**

```jsonl
// Format 1: Simple text
{"text": "Your training text here"}

// Format 2: Instruction format
{"instruction": "Explain quantum computing", "output": "Quantum computing uses..."}

// Format 3: Conversation format
{"messages": [
  {"role": "user", "content": "Question"},
  {"role": "assistant", "content": "Answer"}
]}
```

### 2. Start Training (CLI)

```bash
lab train start \
  --model qwen3-4b-instruct \
  --dataset my_training_data.jsonl \
  --output my-finetuned-model \
  --epochs 3 \
  --batch-size 4 \
  --learning-rate 1e-4 \
  --rank 8
```

**What Happens:**

1. Dataset loads and validates
2. Model loads into memory
3. Training starts in background
4. Progress logged to console
5. Adapter saves to `models/my-finetuned-model/`
6. Auto-registers in registry

### 3. Monitor Training

```bash
# List all training jobs
lab train list

# Get job details
lab train status <job-id>

# Watch live logs
lab train logs <job-id>

# Output:
# Job: a1b2c3d4-5678-90ab-cdef-1234567890ab
# Status: training
# Progress: 45% (Epoch 2/3, Step 450/1000)
# Loss: train=0.234, val=0.312
# Throughput: 45 tokens/sec
```

### 4. Use Trained Model

```bash
# Use immediately (auto-registered)
lab chat my-finetuned-model

# Or via API
POST /api/chat/chat
{
  "model": "my-finetuned-model",
  "messages": [{"role": "user", "content": "Your question"}]
}
```

## Training Parameters

### Core Parameters

```bash
--model MODEL              # Base model to fine-tune
--dataset DATASET          # Training data file (JSONL)
--output OUTPUT            # Name for trained adapter
```

### Training Configuration

```bash
--epochs N                 # Number of training epochs (default: 3)
--batch-size N             # Batch size (default: 4, reduce if OOM)
--learning-rate LR         # Learning rate (default: 1e-4)
--grad-accumulation N      # Gradient accumulation steps (default: 1)
--max-seq-length N         # Max sequence length (default: 2048)
```

### LoRA Configuration

```bash
--rank N                   # LoRA rank (default: 8)
                           # Higher = more capacity, more memory
                           # Common: 4, 8, 16, 32

--alpha N                  # LoRA alpha (default: 16)
                           # Scaling factor for LoRA weights
                           # Usually 2x rank

--dropout RATE             # Dropout rate (default: 0.0)
                           # Regularization to prevent overfitting
                           # Common: 0.0, 0.05, 0.1

--target-modules LAYERS    # Which layers to apply LoRA
                           # Default: "q_proj,v_proj"
                           # Options: all, q_proj, v_proj, k_proj, o_proj
```

### Validation

```bash
--val-dataset DATASET      # Validation dataset (JSONL)
--val-batches N            # Validation batches per check (default: 10)
--steps-per-eval N         # Evaluation frequency (default: 100)
```

### Memory Management

```bash
--max-memory-gb N          # Max memory to use (default: auto)
--gradient-checkpointing   # Enable to save memory (slower)
--max-seq-length N         # Limit sequence length to save memory
```

## Parameter Tuning Guide

### Choosing LoRA Rank

```bash
# Rank 4: Minimal changes, least memory
--rank 4                   # Good for: style transfer, simple tasks

# Rank 8: Balanced (recommended starting point)
--rank 8                   # Good for: domain adaptation, instruction tuning

# Rank 16: More capacity
--rank 16                  # Good for: complex reasoning, knowledge injection

# Rank 32+: Maximum capacity
--rank 32                  # Good for: significant task changes, requires more data
```

**Rule of thumb:** Start with rank=8, increase if underfitting.

### Choosing Learning Rate

```bash
# Conservative (safer)
--learning-rate 5e-5       # Good for: large models, small datasets

# Standard (recommended)
--learning-rate 1e-4       # Good for: most cases

# Aggressive
--learning-rate 2e-4       # Good for: large datasets, fast convergence
```

**Rule of thumb:** Start with 1e-4, reduce if loss is unstable.

### Choosing Batch Size

```bash
# Based on available memory:
# 16GB system: batch-size 2-4
# 32GB system: batch-size 4-8
# 64GB+ system: batch-size 8-16

--batch-size 4             # Default, good for most
--batch-size 2             # If out of memory errors
--batch-size 8             # If plenty of memory
```

**Memory Tip:** Use gradient accumulation for larger effective batch size:
```bash
--batch-size 2 --grad-accumulation 4  # Effective batch = 8
```

## Training Examples

### Example 1: Instruction Tuning

```bash
# Dataset: instruction_tuning.jsonl
{"instruction": "Explain quantum computing", "output": "Quantum computing uses..."}
{"instruction": "What is machine learning?", "output": "Machine learning is..."}

# Training:
lab train start \
  --model qwen3-4b-instruct \
  --dataset instruction_tuning.jsonl \
  --output instruction-tuned-model \
  --epochs 3 \
  --rank 8 \
  --learning-rate 1e-4 \
  --batch-size 4
```

### Example 2: Chat Style Transfer

```bash
# Dataset: chat_style.jsonl
{"text": "User: Hi!\nModel: Hello there! How may I assist you today?"}
{"text": "User: What's up?\nModel: I'm doing well, thank you for asking!"}

# Training:
lab train start \
  --model qwen3-4b-instruct \
  --dataset chat_style.jsonl \
  --output friendly-chat-model \
  --epochs 5 \
  --rank 4 \
  --learning-rate 5e-5
```

### Example 3: Domain Adaptation (Medical)

```bash
# Dataset: medical_qa.jsonl
{"text": "Patient: What are diabetes symptoms?\nDoctor: Common symptoms include..."}
{"text": "Patient: How does insulin work?\nDoctor: Insulin helps regulate..."}

# Training:
lab train start \
  --model qwen3-4b-instruct \
  --dataset medical_qa.jsonl \
  --output medical-assistant \
  --epochs 5 \
  --rank 16 \
  --learning-rate 1e-4 \
  --batch-size 2 \
  --val-dataset medical_val.jsonl
```

### Example 4: Memory-Constrained Training

```bash
# For 16GB system:
lab train start \
  --model qwen3-4b-instruct \
  --dataset my_data.jsonl \
  --output my-model \
  --epochs 3 \
  --batch-size 2 \
  --grad-accumulation 4 \
  --gradient-checkpointing \
  --max-seq-length 1024 \
  --rank 4
```

## Training Output

### Directory Structure

```
models/my-finetuned-model/
├── adapters.safetensors           # Final trained adapter
├── adapter_config.json            # Adapter configuration
├── lora_config.json               # LoRA parameters
├── 0000100_adapters.safetensors   # Checkpoint (step 100)
├── 0000200_adapters.safetensors   # Checkpoint (step 200)
├── ...
└── training_results.json          # Training metrics
```

### Training Results

```json
{
  "job_id": "a1b2c3d4...",
  "model": "qwen3-4b-instruct",
  "adapter": "my-finetuned-model",
  "status": "completed",
  "epochs_completed": 3,
  "final_train_loss": 0.123,
  "final_val_loss": 0.234,
  "training_time_seconds": 1800,
  "peak_memory_gb": 6.5,
  "throughput_tokens_per_sec": 45
}
```

## Web UI Training

### 1. Navigate to Training Page

Open http://localhost:5173 and click "Training"

### 2. Configure Training

- **Model**: Select base model from dropdown
- **Dataset**: Upload JSONL file or use existing
- **Output Name**: Enter name for adapter
- **Parameters**:
  - Epochs: 3
  - Batch Size: 4
  - Learning Rate: 1e-4
  - LoRA Rank: 8
  - LoRA Alpha: 16

### 3. Monitor Progress

Real-time updates:
- Progress bar
- Current epoch/step
- Live loss metrics
- ETA calculation

### 4. Review Results

After completion:
- View training curves
- Download adapter files
- Test model in chat interface

## API Training

### Start Training Job

```bash
POST /api/training/train

Body:
{
  "model": "qwen3-4b-instruct",
  "dataset_path": "my_training_data.jsonl",
  "output_name": "my-finetuned-model",
  "epochs": 3,
  "batch_size": 4,
  "learning_rate": 1e-4,
  "lora_rank": 8,
  "lora_alpha": 16,
  "validation_dataset_path": "my_val_data.jsonl"
}

Response:
{
  "job_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "started",
  "message": "Training job started successfully"
}
```

### Check Job Status

```bash
GET /api/training/jobs/{job_id}

Response:
{
  "job_id": "...",
  "status": "training",
  "progress": 45,
  "current_epoch": 2,
  "total_epochs": 3,
  "current_step": 450,
  "total_steps": 1000,
  "train_loss": 0.234,
  "val_loss": 0.312,
  "eta_seconds": 900
}
```

### List All Jobs

```bash
GET /api/training/jobs

Response:
{
  "jobs": [
    {
      "job_id": "...",
      "model": "qwen3-4b-instruct",
      "adapter": "my-model",
      "status": "completed",
      "created_at": "2025-01-05T10:30:00Z"
    }
  ]
}
```

## Troubleshooting

### Out of Memory Errors

```bash
# Error: Out of memory
# Solutions:
1. Reduce batch size: --batch-size 2
2. Enable gradient checkpointing: --gradient-checkpointing
3. Reduce sequence length: --max-seq-length 1024
4. Use smaller rank: --rank 4
5. Close other applications
```

### Loss Not Decreasing

```bash
# Problem: Loss stuck or increasing
# Solutions:
1. Lower learning rate: --learning-rate 5e-5
2. Check dataset quality and format
3. Increase epochs: --epochs 5
4. Increase model capacity: --rank 16
5. Add validation dataset to detect overfitting
```

### Overfitting

```bash
# Problem: Train loss ↓, Val loss ↑
# Solutions:
1. Increase dropout: --dropout 0.1
2. Reduce model capacity: --rank 4
3. Add more training data
4. Reduce epochs: --epochs 2
5. Add data augmentation
```

### Slow Training

```bash
# Problem: Training too slow
# Solutions:
1. Increase batch size (if memory allows): --batch-size 8
2. Reduce validation frequency: --steps-per-eval 500
3. Use gradient checkpointing: --gradient-checkpointing
4. Check MLX is using GPU: Activity Monitor
```

### Dataset Errors

```bash
# Error: Failed to load dataset
# Common issues:
1. Invalid JSONL format
   Solution: Validate with python -m json.tool dataset.jsonl

2. Empty lines in file
   Solution: Remove blank lines

3. Wrong field names
   Solution: Use "text", "instruction"/"output", or "messages"

4. Encoding issues
   Solution: Save as UTF-8
```

## Best Practices

1. **Start Small** — Test with subset of data first
2. **Monitor Validation** — Always use validation dataset
3. **Save Checkpoints** — Keep intermediate results
4. **Document Experiments** — Track hyperparameters and results
5. **Compare Baselines** — Compare to base model performance
6. **Use Appropriate Metrics** — Loss, perplexity, task-specific metrics
7. **Iterate** — Start simple, add complexity gradually

## Advanced Topics

### Multi-Task Learning

```jsonl
// Dataset with task identifiers
{"text": "Task: summarize. Text: ...", "task": "summarization"}
{"text": "Task: translate. Text: ...", "task": "translation"}
```

### Continued Training

```bash
# Resume from checkpoint
lab train start \
  --model qwen3-4b-instruct \
  --dataset new_data.jsonl \
  --output my-model-v2 \
  --resume-from models/my-model/adapters.safetensors
```

### Merging Adapters

```python
# Merge LoRA into base model (creates standalone model)
from ai_lab.core.training import merge_adapter

merge_adapter(
  base_model="qwen3-4b-instruct",
  adapter_path="models/my-model/adapters.safetensors",
  output_path="models/my-model-merged/"
)
```

## See Also

- [Model Management](MODEL_MANAGEMENT.md) — Managing base models and adapters
- [Optimization Guide](OPTIMIZATION_GUIDE.md) — Hyperparameter tuning
- [API Reference](API_REFERENCE.md) — Complete training API
- [Web UI Guide](WEB_UI_GUIDE.md) — Visual training interface
