# SDK Guide: Python Integration

## Overview

The AI Lab Python SDK provides a simple, type-safe interface for integrating the platform into your Python applications. Perfect for automated workflows, batch processing, and custom tools.

## Installation

```bash
# Install SDK (included in platform)
pip install -e sdk/

# Or install from requirements.txt
pip install -r requirements.txt
```

## Quick Start

```python
from ai_lab_sdk import AILabClient

# Initialize client
client = AILabClient(
    base_url="http://localhost:8000"
)

# Chat completion
response = client.chat.completions.create(
    model="qwen3-4b-instruct",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
# Output: "Hello! How can I help you today?"
```

---

## Client Initialization

### Basic Setup

```python
from ai_lab_sdk import AILabClient

client = AILabClient(
    base_url="http://localhost:8000",
    timeout=30  # Request timeout in seconds
)
```

### With Authentication (Future)

```python
client = AILabClient(
    base_url="https://your-platform.com",
    api_key="your-api-key-here"
)
```

---

## Chat Completions

### Simple Chat

```python
response = client.chat.completions.create(
    model="qwen3-4b-instruct",
    messages=[
        {"role": "user", "content": "Explain quantum computing"}
    ]
)

print(response.content)
# "Quantum computing is a type of computation..."
```

### Conversation History

```python
messages = [
    {"role": "user", "content": "What is the capital of France?"},
    {"role": "assistant", "content": "The capital of France is Paris."},
    {"role": "user", "content": "And what about Germany?"}
]

response = client.chat.completions.create(
    model="qwen3-4b-instruct",
    messages=messages
)

print(response.content)
# "The capital of Germany is Berlin."
```

### With Parameters

```python
response = client.chat.completions.create(
    model="qwen3-4b-instruct",
    messages=[{"role": "user", "content": "Write a story"}],
    temperature=0.8,      # Higher = more creative
    max_tokens=2000,       # Max response length
    top_p=0.9,            # Nucleus sampling
    stream=False          # No streaming
)
```

### Streaming Chat

```python
for chunk in client.chat.completions.stream(
    model="qwen3-4b-instruct",
    messages=[{"role": "user", "content": "Tell me a story"}]
):
    print(chunk.token, end="", flush=True)

# Output: Once upon a time... (streaming token by token)
```

### System Prompts

```python
response = client.chat.completions.create(
    model="qwen3-4b-instruct",
    messages=[
        {"role": "system", "content": "You are a helpful medical assistant."},
        {"role": "user", "content": "What are diabetes symptoms?"}
    ]
)
```

---

## Model Management

### List Models

```python
models = client.models.list()

for model in models:
    print(f"{model.name}: {model.type} ({model.backend})")
# Output:
# qwen3-4b-instruct: base (mlx)
# granite-micro-4bit: base (mlx)
# my-adapter: adapter (mlx)
```

### Get Model Details

```python
model = client.models.get("qwen3-4b-instruct")

print(f"Context: {model.context_length}")
print(f"Memory: {model.memory_required_gb} GB")
print(f"Size: {model.size_gb} GB")
```

### Download Model

```python
job = client.models.download(
    model_id="mlx-community/Qwen3-4B-Instruct-4bit",
    name="qwen3-4b-instruct"
)

# Monitor download progress
while True:
    status = client.models.get_download_status(job.job_id)
    print(f"Progress: {status.progress}%")
    if status.status == "completed":
        break
    time.sleep(5)
```

### Delete Model

```python
# Delete from registry only
client.models.delete("my-adapter", keep_files=True)

# Delete from registry and disk
client.models.delete("my-model", keep_files=False)
```

---

## Training

### Start Training Job

```python
job = client.training.start(
    model="qwen3-4b-instruct",
    dataset_path="training_data.jsonl",
    output_name="my-finetuned-model",
    epochs=3,
    batch_size=4,
    learning_rate=1e-4,
    lora_rank=8,
    lora_alpha=16,
    validation_dataset_path="validation_data.jsonl"
)

print(f"Training job started: {job.job_id}")
```

### Monitor Training Progress

```python
# Poll for status
while True:
    status = client.training.get_status(job.job_id)

    print(f"Progress: {status.progress}%")
    print(f"Epoch: {status.current_epoch}/{status.total_epochs}")
    print(f"Loss: {status.train_loss:.4f}")

    if status.status == "completed":
        print("Training complete!")
        break
    elif status.status == "failed":
        print(f"Training failed: {status.error}")
        break

    time.sleep(10)
```

### List Training Jobs

```python
jobs = client.training.list()

for job in jobs:
    print(f"{job.output_name}: {job.status}")
    if job.status == "completed":
        print(f"  Final loss: {job.final_train_loss:.4f}")
```

### Get Training Logs

```python
logs = client.training.get_logs(job.job_id)

for log in logs:
    print(f"{log.timestamp}: {log.message}")
```

### Use Trained Model

```python
# Model is auto-registered after training
response = client.chat.completions.create(
    model="my-finetuned-model",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## Optimization

### Start Optimization Job

```python
from ai_lab_sdk import optimization as opt

job = client.optimization.start(
    model="qwen3-4b-instruct",
    dataset_path="training_data.jsonl",
    parameters={
        "learning_rate": opt.Range(
            bounds=[1e-5, 1e-3],
            log_scale=True
        ),
        "lora_rank": opt.Choice(values=[4, 8, 16, 32]),
        "batch_size": opt.Choice(values=[2, 4, 8])
    },
    experiment={
        "max_trials": 20,
        "parallel": 2,
        "objective_metric": "val_loss",
        "direction": "minimize"
    },
    fixed_params={
        "epochs": 3,
        "lora_alpha": 16
    }
)

print(f"Optimization started: {job.job_id}")
```

### Monitor Optimization

```python
# Check progress
status = client.optimization.get_status(job.job_id)

print(f"Progress: {status.completed_trials}/{status.total_trials}")
print(f"Best trial: {status.best_trial.trial_number}")
print(f"Best loss: {status.best_trial.objectives['val_loss']:.4f}")

# Get all trials
trials = client.optimization.get_trials(job.job_id)

for trial in trials:
    print(f"Trial {trial.trial_number}:")
    print(f"  Params: {trial.parameters}")
    print(f"  Val loss: {trial.objectives['val_loss']:.4f}")
```

### Train with Best Configuration

```python
# Get best configuration
best_trial = status.best_trial

# Train with best hyperparameters
job = client.training.start(
    model="qwen3-4b-instruct",
    dataset_path="training_data.jsonl",
    output_name="best-model",
    learning_rate=best_trial.parameters["learning_rate"],
    lora_rank=best_trial.parameters["lora_rank"],
    batch_size=best_trial.parameters["batch_size"]
)
```

---

## RLM (Recursive Language Models)

### Simple RLM

```python
# Fast recursive processing
result = client.rlm.complete(
    model="qwen3-4b-instruct",
    root_prompt="Summarize this document",
    prompt=long_document_text,
    max_context=8000,
    chunk_size=2000
)

print(result.summary)
# "Document summary here..."

print(f"Processed {result.chunks_processed} chunks")
print(f"Total tokens: {result.total_tokens}")
print(f"Time: {result.processing_time_seconds}s")
```

### Full RLM

```python
# With code execution
result = client.rlm.complete_full(
    model="qwen3-4b-instruct",
    root_prompt="Analyze this dataset",
    prompt=large_dataset_text,
    tools=["python"],
    max_iterations=10
)

print(result.answer)
# "Analysis results..."

print(f"Tools used: {result.tools_used}")
print(f"Iterations: {result.iterations}")
```

---

## Advanced Usage

### Batch Processing

```python
# Process multiple prompts
prompts = [
    "What is AI?",
    "Explain machine learning",
    "What is deep learning?"
]

responses = client.chat.completions.batch_create(
    model="qwen3-4b-instruct",
    messages=[[{"role": "user", "content": p}] for p in prompts]
)

for response in responses:
    print(response.content)
```

### Custom Error Handling

```python
from ai_lab_sdk.errors import (
    AILabError,
    ModelNotFoundError,
    InsufficientMemoryError
)

try:
    response = client.chat.completions.create(...)
except ModelNotFoundError:
    print("Model not found!")
except InsufficientMemoryError as e:
    print(f"Need {e.required_gb}GB, have {e.available_gb}GB")
except AILabError as e:
    print(f"Error: {e.message}")
```

### Async Client

```python
import asyncio
from ai_lab_sdk import AsyncAILabClient

async def main():
    client = AsyncAILabClient(base_url="http://localhost:8000")

    # Async chat
    response = await client.chat.completions.create(
        model="qwen3-4b-instruct",
        messages=[{"role": "user", "content": "Hello!"}]
    )

    print(response.content)

asyncio.run(main())
```

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def send_with_retry(message):
    return client.chat.completions.create(
        model="qwen3-4b-instruct",
        messages=[{"role": "user", "content": message}]
    )
```

---

## Integration Examples

### Example 1: Document Summarization Pipeline

```python
from ai_lab_sdk import AILabClient
import glob

client = AILabClient()

# Process all documents
for doc_path in glob.glob("documents/*.txt"):
    with open(doc_path) as f:
        text = f.read()

    # Summarize with RLM
    result = client.rlm.complete(
        model="qwen3-4b-instruct",
        root_prompt="Summarize this document",
        prompt=text,
        chunk_size=2000
    )

    # Save summary
    with open(f"summaries/{doc_path}.summary.txt", "w") as f:
        f.write(result.summary)

    print(f"Summarized {doc_path}")
```

### Example 2: Automated Fine-Tuning

```python
from ai_lab_sdk import AILabClient

client = AILabClient()

# 1. Download base model
client.models.download(
    model_id="mlx-community/Qwen3-4B-Instruct-4bit",
    name="qwen3-4b-instruct"
)

# 2. Find best hyperparameters
opt_job = client.optimization.start(...)
# (wait for completion)

# 3. Train with best config
best_params = client.optimization.get_status(opt_job.job_id).best_trial.parameters
train_job = client.training.start(
    model="qwen3-4b-instruct",
    dataset_path="data.jsonl",
    output_name="domain-model",
    **best_params
)

# 4. Wait for training
while True:
    status = client.training.get_status(train_job.job_id)
    if status.status == "completed":
        break
    time.sleep(60)

# 5. Test the model
response = client.chat.completions.create(
    model="domain-model",
    messages=[{"role": "user", "content": "Test message"}]
)
print(response.content)
```

### Example 3: Chat Bot Application

```python
from ai_lab_sdk import AILabClient

class ChatBot:
    def __init__(self, model: str, system_prompt: str):
        self.client = AILabClient()
        self.model = model
        self.system_prompt = system_prompt
        self.conversation = []

    def chat(self, user_message: str) -> str:
        # Add system prompt if first message
        if not self.conversation:
            self.conversation.append({
                "role": "system",
                "content": self.system_prompt
            })

        # Add user message
        self.conversation.append({
            "role": "user",
            "content": user_message
        })

        # Get response
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.conversation
        )

        assistant_message = response.content

        # Add assistant response
        self.conversation.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def reset(self):
        self.conversation = []

# Usage
bot = ChatBot(
    model="qwen3-4b-instruct",
    system_prompt="You are a helpful assistant."
)

while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break

    response = bot.chat(user_input)
    print(f"Bot: {response}")
```

### Example 4: Automated Testing

```python
from ai_lab_sdk import AILabClient
import json

client = AILabClient()

# Test dataset
test_cases = [
    {"input": "What is 2+2?", "expected": "4"},
    {"input": "Capital of France?", "expected": "Paris"},
]

# Test base model
print("Testing base model...")
base_results = []
for case in test_cases:
    response = client.chat.completions.create(
        model="qwen3-4b-instruct",
        messages=[{"role": "user", "content": case["input"]}]
    )
    base_results.append({
        "input": case["input"],
        "output": response.content,
        "expected": case["expected"]
    })

# Test fine-tuned model
print("Testing fine-tuned model...")
finetuned_results = []
for case in test_cases:
    response = client.chat.completions.create(
        model="my-finetuned-model",
        messages=[{"role": "user", "content": case["input"]}]
    )
    finetuned_results.append({
        "input": case["input"],
        "output": response.content,
        "expected": case["expected"]
    })

# Save results
with open("test_results.json", "w") as f:
    json.dump({
        "base_model": base_results,
        "finetuned_model": finetuned_results
    }, f, indent=2)
```

---

## Type Hints

The SDK provides full type hints for IDE support:

```python
from ai_lab_sdk import AILabClient
from ai_lab_sdk.types import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ModelInfo,
    TrainingJob
)

client: AILabClient = AILabClient()

request: ChatCompletionRequest = ChatCompletionRequest(
    model="qwen3-4b-instruct",
    messages=[{"role": "user", "content": "Hello!"}]
)

response: ChatCompletionResponse = client.chat.completions.create(request)
```

---

## Error Handling

### Error Types

```python
from ai_lab_sdk.errors import (
    AILabError,                # Base error
    APIError,                  # API request failed
    ModelNotFoundError,        # Model doesn't exist
    InsufficientMemoryError,   # Not enough memory
    TrainingError,             # Training failed
    ValidationError            # Invalid parameters
)
```

### Error Attributes

```python
try:
    response = client.chat.completions.create(...)
except ModelNotFoundError as e:
    print(f"Model: {e.model_name}")
    print(f"Available models: {e.available_models}")

except InsufficientMemoryError as e:
    print(f"Required: {e.required_gb}GB")
    print(f"Available: {e.available_gb}GB")
```

---

## Best Practices

### 1. Reuse Client Instance

```python
# Good
client = AILabClient()
for msg in messages:
    client.chat.completions.create(...)

# Bad (creates new connection each time)
for msg in messages:
    client = AILabClient()
    client.chat.completions.create(...)
```

### 2. Use Context Managers

```python
# Good (auto-cleanup)
with AILabClient() as client:
    response = client.chat.completions.create(...)
```

### 3. Handle Timeouts

```python
client = AILabClient(timeout=120)  # 2 minutes for long tasks
```

### 4. Monitor Resources

```python
# Check system status before expensive operations
status = client.system.get_status()
if status.memory_available_gb < 8:
    print("Warning: Low memory")
```

### 5. Log Operations

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_lab")

logger.info("Starting training...")
job = client.training.start(...)
logger.info(f"Job ID: {job.job_id}")
```

---

## See Also

- [API Reference](API_REFERENCE.md) — Complete REST API docs
- [Training Guide](TRAINING_GUIDE.md) — Training concepts
- [Optimization Guide](OPTIMIZATION_GUIDE.md) — Optimization concepts
- [Web UI Guide](WEB_UI_GUIDE.md) — Visual interface guide
