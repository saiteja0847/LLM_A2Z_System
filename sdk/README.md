# AI Lab SDK

Python SDK for the AI Lab platform - manage models, chat with LLMs, and train custom adapters.

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from ai_lab_sdk import AILabClient, ChatMessage

# Initialize client
client = AILabClient("http://localhost:8000")

# List models
models = client.models.list()
print(f"Available models: {[m.name for m in models]}")

# Chat with a model
response = client.chat.complete(
    model="qwen-1-5b",
    messages=[
        ChatMessage(role="user", content="What is Python?")
    ]
)
print(response.content)

# Train a custom model
job = client.training.train(
    base_model="qwen-1-5b",
    output_name="my-model",
    dataset_path="data.jsonl",
    epochs=3
)

# Wait for completion
completed = client.training.wait_for_completion(job.id)
print(f"Model saved to: {completed.result['output_path']}")
```

## Features

### Model Management

```python
# Download a model from HuggingFace
model = client.models.download(
    repo_id="mlx-community/Qwen2.5-1.5B-Instruct-4bit",
    name="qwen-1-5b"
)

# Get model details
model = client.models.get("qwen-1-5b")
print(f"Size: {model.size_gb} GB")
print(f"Memory: {model.estimated_memory_gb} GB")

# List all models
models = client.models.list()
base_models = [m for m in models if m.type == "base"]
adapters = [m for m in models if m.type == "adapter"]

# Delete a model
client.models.delete("old-model")
```

### Chat Interface

```python
# Simple chat
response = client.chat.complete(
    model="qwen-1-5b",
    messages=[{"role": "user", "content": "Hello!"}],
    temperature=0.8,
    max_tokens=200
)

# Multi-turn conversation
messages = [
    ChatMessage(role="system", content="You are a helpful assistant"),
    ChatMessage(role="user", content="What is AI?"),
]

response = client.chat.complete("qwen-1-5b", messages)
messages.append(ChatMessage(role="assistant", content=response.content))
messages.append(ChatMessage(role="user", content="Tell me more"))

response = client.chat.complete("qwen-1-5b", messages)

# OpenAI-compatible API
response = client.chat.openai_complete(
    model="qwen-1-5b",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Training

```python
# Start training
job = client.training.train(
    base_model="qwen-1-5b",
    output_name="my-finetuned-model",
    dataset_path="./training_data.jsonl",
    epochs=5,
    batch_size=4,
    lora_rank=16,
    learning_rate=0.0001
)

# Monitor progress
while True:
    job = client.training.get_job(job.id)
    print(f"Progress: {job.progress * 100}%")

    if job.status in ["completed", "failed"]:
        break

    time.sleep(5)

# Or wait for completion
completed_job = client.training.wait_for_completion(
    job.id,
    poll_interval=10,
    timeout=3600  # 1 hour
)

# View logs
logs = client.training.get_logs(job.id, tail=50)
for log in logs:
    print(log)

# List all training jobs
jobs = client.training.list_jobs(status="running")
```

## API Reference

### AILabClient

Main client for interacting with AI Lab.

**Constructor:**
- `AILabClient(base_url: str, timeout: int = 30)`

**Methods:**
- `health_check() -> dict` - Check API health

**Properties:**
- `models: ModelManager` - Model management
- `chat: ChatClient` - Chat interface
- `training: TrainingManager` - Training jobs

### ModelManager

Manage models in the registry.

**Methods:**
- `list(status: str = None, backend: str = None) -> List[Model]`
- `get(name: str) -> Model`
- `download(repo_id: str, name: str = None, backend: str = "mlx") -> Model`
- `delete(name: str, force: bool = False) -> None`

### ChatClient

Chat with models.

**Methods:**
- `complete(model: str, messages: List, temperature: float = 0.7, max_tokens: int = 512) -> ChatResponse`
- `openai_complete(model: str, messages: List, **kwargs) -> dict`

### TrainingManager

Manage training jobs.

**Methods:**
- `train(base_model: str, output_name: str, dataset_path: str, **kwargs) -> TrainingJob`
- `list_jobs(status: str = None, limit: int = 50) -> List[TrainingJob]`
- `get_job(job_id: str) -> TrainingJob`
- `get_logs(job_id: str, tail: int = 100) -> List[str]`
- `wait_for_completion(job_id: str, poll_interval: int = 5, timeout: int = None) -> TrainingJob`

## Examples

See the `examples/` directory for complete examples:
- `basic_usage.py` - Model listing and chat
- `training_example.py` - Full training workflow

## Requirements

- Python 3.9+
- requests >= 2.28.0

## License

MIT
