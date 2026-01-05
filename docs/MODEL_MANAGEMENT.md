# Model Management Guide

## Overview

The AI Lab platform provides complete model lifecycle management for Apple Silicon, including downloading, registering, listing, and managing LLMs. All models are optimized for MLX acceleration on M1/M2/M3/M4 chips.

## Key Features

✅ **HuggingFace Integration** — Download directly from mlx-community
✅ **Automatic Registration** — Models auto-register in `registry.yaml`
✅ **Memory-Aware Loading** — Smart memory estimation for 16GB systems
✅ **Multi-Backend Support** — MLX, GGUF, Ollama, Remote backends
✅ **4-bit Quantization** — Run large models in limited memory
✅ **CLI & API** — Manage models via command line or REST API

## Model Registry

All models are tracked in `registry.yaml`:

```yaml
models:
  qwen3-4b-instruct:
    name: qwen3-4b-instruct
    path: /Users/path/to/models/qwen3-4b-instruct-2507-4bit
    backend: mlx
    type: base
    parameters:
      context_length: 250000
      quantization: 4bit
    metadata:
      size_gb: 4.0
      architecture: qwen2
```

### Model Types

- **base** — Pre-trained foundation models
- **adapter** — LoRA fine-tuned models (require parent)

## Quick Start

### 1. List Available Models

```bash
# CLI
lab models list

# Output:
# NAME                    TYPE     BACKEND  SIZE    CONTEXT
# qwen3-4b-instruct       base     MLX     4.0GB   250K
# granite-micro-4bit      base     MLX     1.7GB   128K
```

### 2. Download a Model

```bash
# Search for models
lab models search "qwen"

# Download from HuggingFace
lab models download mlx-community/Qwen2.5-1.5B-Instruct-4bit

# Models download to: models/ directory
# Auto-registered and ready to use
```

### 3. Get Model Details

```bash
lab models info qwen3-4b-instruct

# Output:
# Model: qwen3-4b-instruct
# Backend: MLX
# Path: /path/to/models/qwen3-4b-instruct-2507-4bit
# Context Window: 250,000 tokens
# Quantization: 4-bit
# Memory Required: ~4.2 GB
```

## Downloading Models

### From HuggingFace

The platform uses **mlx-community** as the default hub for MLX-optimized models:

```bash
# Search for models
lab models search "mlx"

# Popular models:
lab models download mlx-community/Qwen2.5-1.5B-Instruct-4bit
lab models download mlx-community/Meta-Llama-3.1-8B-Instruct-4bit
lab models download mlx-community/granite-3.0-1b-a400m-instruct
```

### Supported Model Formats

- **MLX Models** — `.safetensors` format (recommended)
- **GGUF Models** — `.gguf` format (llama.cpp compatible)
- **Ollama Models** — Via Ollama backend
- **Remote Models** — Via API (OpenAI, Anthropic, etc.)

## Manual Registration

If you have models already downloaded:

```bash
# Register manually
lab models register \
  --name my-model \
  --path /path/to/model \
  --backend mlx \
  --type base \
  --context 32000
```

Or edit `registry.yaml` directly:

```yaml
models:
  my-custom-model:
    name: my-custom-model
    path: /absolute/path/to/model
    backend: mlx
    type: base
    parameters:
      context_length: 32000
    metadata:
      size_gb: 2.0
```

## Memory Management

### Understanding Memory Requirements

The platform automatically estimates memory usage:

```python
# Formula (memory.py):
# base_memory + (context_tokens / 4096) * kv_cache_per_4k

# Examples:
# Qwen3-4B (4-bit): ~4.2 GB @ 4K context
# Qwen3-4B (4-bit): ~6.8 GB @ 32K context
# Llama3-8B (4-bit): ~5.5 GB @ 4K context
```

### Memory-Safe Usage

```bash
# Check available memory
lab status

# Load model (automatically checks memory)
lab chat qwen3-4b-instruct

# If memory insufficient:
# ❌ Error: Insufficient memory
#    Required: 6.8 GB
#    Available: 5.2 GB
#    Solution: Use smaller context or quantized model
```

### Optimizing for 16GB Systems

```bash
# Use 4-bit quantization
lab models download mlx-community/Qwen3-4B-Instruct-4bit

# Limit context in chat
lab chat qwen3-4b-instruct --max-tokens 2048

# Close other apps before training
lab train start my-model --dataset data.jsonl --max-memory-gb 12
```

## Deleting Models

### Remove from Registry (Keep Files)

```bash
# CLI
lab models delete qwen3-4b-instruct --keep-files

# API
DELETE /api/models/qwen3-4b-instruct?keep_files=true
```

### Delete Files Permanently

```bash
# Remove from registry and delete files
lab models delete qwen3-4b-instruct --delete-files

# Or manually:
rm -rf models/qwen3-4b-instruct/
# Then remove from registry.yaml
```

## Managing Adapters

Trained LoRA adapters are managed as special model types:

```bash
# List all models (including adapters)
lab models list

# Adapters show parent model:
# NAME                      TYPE     PARENT
# qwen3-4b-instruct         base     -
# my-adapter               adapter  qwen3-4b-instruct
```

### Adapter Memory

Adapters add minimal overhead (~100MB) to parent model:

```yaml
models:
  my-adapter:
    name: my-adapter
    parent: qwen3-4b-instruct  # Required
    path: models/my-adapter
    backend: mlx
    type: adapter
    # Memory = parent_memory + 0.1GB
```

## Model Backends

### MLX Backend (Primary)

Optimized for Apple Silicon:

```yaml
backend: mlx
parameters:
  context_length: 250000
  quantization: 4bit  # Supports: 4bit, 8bit
```

**Advantages:**
- Fastest inference on Apple Silicon
- Lowest memory footprint
- LoRA training support
- Quantization (4-bit, 8-bit)

### GGUF Backend

For llama.cpp compatible models:

```yaml
backend: gguf
parameters:
  model_path: models/model.gguf
  n_ctx: 8192
  n_gpu_layers: -1  # -1 = all layers to GPU
```

**Advantages:**
- Wide model compatibility
- CPU+GPU hybrid inference
- Community quantized models

### Ollama Backend

Use Ollama-managed models:

```yaml
backend: ollama
parameters:
  model: llama3.1
  host: localhost
  port: 11434
```

**Advantages:**
- No manual downloads
- Automatic model management
- Simple setup

### Remote Backend

Use API-based models:

```yaml
backend: remote
parameters:
  provider: openai
  model: gpt-4
  api_key: your-api-key
```

## Troubleshooting

### Model Not Found

```bash
# Error: Model not found in registry
# Solution: Check model name and register if needed
lab models list
lab models register --name my-model --path /path/to/model
```

### Insufficient Memory

```bash
# Error: Insufficient memory to load model
# Solutions:
1. Close other applications
2. Use smaller context window
3. Use 4-bit quantized model
4. Use smaller base model
```

### Download Failures

```bash
# Error: Failed to download model
# Solutions:
1. Check internet connection
2. Verify HuggingFace model ID
3. Try different mirror:
   lab models download mlx-community/Qwen3-4B-Instruct-4bit --mirror hf-mirror.com
```

### Corrupted Model Files

```bash
# Error: Failed to load model
# Solution: Re-download
rm -rf models/qwen3-4b-instruct/
lab models download mlx-community/Qwen3-4B-Instruct-4bit
```

## Best Practices

1. **Start Small** — Begin with 1B-4B models for testing
2. **Use 4-bit** — Default to 4-bit quantization for memory efficiency
3. **Monitor Memory** — Check `lab status` before loading models
4. **Organize Models** — Keep all models in `models/` directory
5. **Backup Registry** — Commit `registry.yaml` to version control
6. **Document Custom Models** — Add notes in `metadata` section

## API Reference

### List Models

```bash
GET /api/models

Response:
{
  "models": [
    {
      "name": "qwen3-4b-instruct",
      "type": "base",
      "backend": "mlx",
      "path": "/path/to/model",
      "parameters": {...},
      "metadata": {...}
    }
  ]
}
```

### Get Model Details

```bash
GET /api/models/{model_name}

Response:
{
  "name": "qwen3-4b-instruct",
  "type": "base",
  "backend": "mlx",
  "context_length": 250000,
  "size_gb": 4.0,
  "memory_required_gb": 4.2,
  ...
}
```

### Download Model

```bash
POST /api/models/download

Body:
{
  "model_id": "mlx-community/Qwen3-4B-Instruct-4bit",
  "name": "qwen3-4b-instruct"  # optional, auto-generated
}
```

### Delete Model

```bash
DELETE /api/models/{model_name}?keep_files=false
```

## See Also

- [Training Guide](TRAINING_GUIDE.md) — Create custom adapters
- [Optimization Guide](OPTIMIZATION_GUIDE.md) — Hyperparameter tuning
- [API Reference](API_REFERENCE.md) — Complete REST API docs
- [Web UI Guide](WEB_UI_GUIDE.md) — Visual model management
