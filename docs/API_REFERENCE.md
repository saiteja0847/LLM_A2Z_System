# API Reference

## Overview

The AI Lab platform provides a comprehensive REST API for all platform features. Includes OpenAI-compatible endpoints for drop-in replacement with existing tools.

## Base URL

```
Local development: http://localhost:8000
Production: https://your-domain.com
```

## Authentication

Currently, the API does not require authentication. For production use, implement API keys:

```bash
# Add to request headers
Authorization: Bearer YOUR_API_KEY
```

---

## Core API Endpoints

### Models

#### List Models

```bash
GET /api/models
```

**Response:**
```json
{
  "models": [
    {
      "name": "qwen3-4b-instruct",
      "type": "base",
      "backend": "mlx",
      "path": "/path/to/model",
      "parameters": {
        "context_length": 250000,
        "quantization": "4bit"
      },
      "metadata": {
        "size_gb": 4.0,
        "architecture": "qwen2"
      }
    }
  ]
}
```

#### Get Model Details

```bash
GET /api/models/{model_name}
```

**Response:**
```json
{
  "name": "qwen3-4b-instruct",
  "type": "base",
  "backend": "mlx",
  "path": "/path/to/model",
  "context_length": 250000,
  "size_gb": 4.0,
  "memory_required_gb": 4.2,
  "quantization": "4bit",
  "metadata": {...}
}
```

#### Download Model

```bash
POST /api/models/download
```

**Request Body:**
```json
{
  "model_id": "mlx-community/Qwen3-4B-Instruct-4bit",
  "name": "qwen3-4b-instruct"
}
```

**Response:**
```json
{
  "status": "downloading",
  "model_id": "mlx-community/Qwen3-4B-Instruct-4bit",
  "name": "qwen3-4b-instruct",
  "progress_url": "/api/models/download/status/{job_id}"
}
```

#### Delete Model

```bash
DELETE /api/models/{model_name}?keep_files=false
```

**Response:**
```json
{
  "status": "deleted",
  "model": "qwen3-4b-instruct",
  "files_deleted": true
}
```

---

### Chat & Completions

#### Chat Completion

```bash
POST /api/chat/chat
```

**Request Body:**
```json
{
  "model": "qwen3-4b-instruct",
  "messages": [
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false
}
```

**Response:**
```json
{
  "model": "qwen3-4b-instruct",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "I'm doing well, thank you for asking!"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 8,
    "completion_tokens": 12,
    "total_tokens": 20
  }
}
```

#### Streaming Chat

```bash
POST /api/chat/chat
```

**Request Body:**
```json
{
  "model": "qwen3-4b-instruct",
  "messages": [
    {"role": "user", "content": "Tell me a story"}
  ],
  "stream": true
}
```

**Response (Server-Sent Events):**
```
data: {"token": "Once", "index": 0}

data: {"token": " upon", "index": 0}

data: {"token": " a", "index": 0}

data: [DONE]
```

---

### OpenAI-Compatible Endpoints

#### Chat Completions (OpenAI Format)

```bash
POST /v1/chat/completions
```

**Request Body (OpenAI Format):**
```json
{
  "model": "qwen3-4b-instruct",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain quantum computing"}
  ],
  "temperature": 0.7,
  "max_tokens": 2000,
  "stream": false
}
```

**Response (OpenAI Format):**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "qwen3-4b-instruct",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Quantum computing is..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 150,
    "total_tokens": 175
  }
}
```

**Python OpenAI SDK Example:**
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"  # Not used but required by SDK
)

response = client.chat.completions.create(
    model="qwen3-4b-instruct",
    messages=[
      {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

**JavaScript Example:**
```javascript
import OpenAI from 'openai';

const openai = new OpenAI({
  baseURL: 'http://localhost:8000/v1',
  apiKey: 'dummy'
});

const response = await openai.chat.completions.create({
  model: 'qwen3-4b-instruct',
  messages: [{ role: 'user', content: 'Hello!' }]
});

console.log(response.choices[0].message.content);
```

#### List Models (OpenAI Format)

```bash
GET /v1/models
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "qwen3-4b-instruct",
      "object": "model",
      "created": 1234567890,
      "owned_by": "mlx-community"
    },
    {
      "id": "granite-micro-4bit",
      "object": "model",
      "created": 1234567890,
      "owned_by": "mlx-community"
    }
  ]
}
```

---

### Training

#### Start Training Job

```bash
POST /api/training/train
```

**Request Body:**
```json
{
  "model": "qwen3-4b-instruct",
  "dataset_path": "training_data.jsonl",
  "output_name": "my-finetuned-model",
  "epochs": 3,
  "batch_size": 4,
  "learning_rate": 1e-4,
  "lora_rank": 8,
  "lora_alpha": 16,
  "validation_dataset_path": "validation_data.jsonl",
  "max_memory_gb": 12
}
```

**Response:**
```json
{
  "job_id": "train-a1b2c3d4...",
  "status": "started",
  "model": "qwen3-4b-instruct",
  "output_name": "my-finetuned-model",
  "message": "Training job started in background"
}
```

#### Get Training Job Status

```bash
GET /api/training/jobs/{job_id}
```

**Response:**
```json
{
  "job_id": "train-a1b2c3d4...",
  "status": "training",
  "progress": 45,
  "current_epoch": 2,
  "total_epochs": 3,
  "current_step": 450,
  "total_steps": 1000,
  "train_loss": 0.234,
  "val_loss": 0.312,
  "eta_seconds": 900,
  "started_at": "2025-01-05T10:30:00Z",
  "updated_at": "2025-01-05T11:00:00Z"
}
```

#### List All Training Jobs

```bash
GET /api/training/jobs
```

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "train-a1b2c3d4...",
      "model": "qwen3-4b-instruct",
      "output_name": "my-model",
      "status": "completed",
      "created_at": "2025-01-05T10:00:00Z",
      "completed_at": "2025-01-05T10:30:00Z",
      "final_train_loss": 0.123,
      "final_val_loss": 0.234
    }
  ]
}
```

#### Get Training Logs

```bash
GET /api/training/jobs/{job_id}/logs
```

**Response:**
```json
{
  "job_id": "train-a1b2c3d4...",
  "logs": [
    {
      "timestamp": "2025-01-05T10:30:00Z",
      "level": "info",
      "message": "Starting training..."
    },
    {
      "timestamp": "2025-01-05T10:30:05Z",
      "level": "info",
      "message": "Epoch 1/3, Step 50/1000, Loss: 0.856"
    }
  ]
}
```

---

### Optimization

#### Start Optimization Job

```bash
POST /api/optimization/start
```

**Request Body:**
```json
{
  "model": "qwen3-4b-instruct",
  "dataset_path": "training_data.jsonl",
  "parameters": {
    "learning_rate": {
      "type": "range",
      "bounds": [1e-5, 1e-3],
      "log_scale": true
    },
    "lora_rank": {
      "type": "choice",
      "values": [4, 8, 16, 32]
    },
    "batch_size": {
      "type": "choice",
      "values": [2, 4, 8]
    }
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
```

**Response:**
```json
{
  "job_id": "opt-xyz789...",
  "status": "started",
  "message": "Optimization job started"
}
```

#### Get Optimization Status

```bash
GET /api/optimization/jobs/{job_id}
```

**Response:**
```json
{
  "job_id": "opt-xyz789...",
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

#### Get Optimization Trials

```bash
GET /api/optimization/jobs/{job_id}/trials
```

**Response:**
```json
{
  "trials": [
    {
      "trial_number": 1,
      "parameters": {
        "learning_rate": 0.0001,
        "lora_rank": 8,
        "batch_size": 4
      },
      "objectives": {
        "val_loss": 0.312
      },
      "status": "completed"
    }
  ]
}
```

---

### RLM (Recursive Language Models)

#### Simple RLM Completion

```bash
POST /api/v1/rlm/complete
```

**Request Body:**
```json
{
  "model": "qwen3-4b-instruct",
  "root_prompt": "Summarize the following document",
  "prompt": "Long document text here...",
  "max_context": 8000,
  "chunk_size": 2000
}
```

**Response:**
```json
{
  "result": "Document summary here...",
  "chunks_processed": 5,
  "total_tokens": 12500,
  "processing_time_seconds": 15
}
```

#### Full RLM Completion

```bash
POST /api/v1/rlm/full
```

**Request Body:**
```json
{
  "model": "qwen3-4b-instruct",
  "root_prompt": "Analyze this data",
  "prompt": "Large dataset here...",
  "tools": ["python"],
  "max_iterations": 10
}
```

**Response:**
```json
{
  "answer": "Analysis results...",
  "iterations": 3,
  "tools_used": ["python"],
  "execution_time_seconds": 120
}
```

#### Get RLM Status

```bash
GET /api/v1/rlm/status
```

**Response:**
```json
{
  "rlm_installed": true,
  "rlm_version": "0.1.0",
  "available_models": [
    "qwen3-4b-instruct",
    "granite-micro-4bit"
  ]
}
```

---

### System

#### Health Check

```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-05T12:00:00Z"
}
```

#### System Status

```bash
GET /api/system/status
```

**Response:**
```json
{
  "platform": "macos",
  "apple_silicon": true,
  "chip": "M4",
  "memory_total_gb": 16.0,
  "memory_available_gb": 8.5,
  "mlx_version": "0.16.0",
  "models_loaded": 1,
  "active_training_jobs": 0
}
```

---

## WebSocket Streaming

### Completion Stream

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/completions');

// Send request
ws.send(JSON.stringify({
  model: 'qwen3-4b-instruct',
  prompt: 'Tell me a story',
  max_tokens: 500
}));

// Receive tokens
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.token);  // Individual tokens
};

// Stream complete
ws.onclose = () => {
  console.log('Stream complete');
};
```

---

## Error Responses

All endpoints return consistent error format:

```json
{
  "error": {
    "message": "Model not found: unknown-model",
    "type": "model_not_found",
    "code": 404
  }
}
```

**Common Error Codes:**

- `400` — Bad Request (invalid parameters)
- `404` — Not Found (model/job doesn't exist)
- `500` — Internal Server Error
- `503` — Service Unavailable (insufficient memory)
- `507` — Insufficient Storage (out of memory)

---

## Rate Limiting

Currently, there are no rate limits. For production, implement:

```python
# Example: FastAPI rate limiting
from slowapi import Limiter

limiter = Limiter(key_func=get_api_key)

@app.post("/api/chat/chat")
@limiter.limit("60/minute")
async def chat_completion(request: Request):
    ...
```

---

## Python SDK

The platform includes a Python SDK for easier API integration:

```python
from ai_lab_sdk import AILabClient

# Initialize client
client = AILabClient(base_url="http://localhost:8000")

# Chat completion
response = client.chat.completions.create(
    model="qwen3-4b-instruct",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Training
job = client.training.start(
    model="qwen3-4b-instruct",
    dataset="training_data.jsonl",
    output_name="my-model"
)

# Check status
status = client.training.get_status(job.job_id)
```

See [SDK Guide](SDK_GUIDE.md) for complete SDK documentation.

---

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:

```
http://localhost:8000/openapi.json
```

Interactive API documentation (Swagger UI):

```
http://localhost:8000/docs
```

---

## See Also

- [Model Management](MODEL_MANAGEMENT.md) — Model endpoints details
- [Training Guide](TRAINING_GUIDE.md) — Training API usage
- [Optimization Guide](OPTIMIZATION_GUIDE.md) — Optimization API usage
- [SDK Guide](SDK_GUIDE.md) — Python SDK documentation
