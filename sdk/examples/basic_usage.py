"""Basic usage examples for AI Lab SDK."""
from ai_lab_sdk import AILabClient, ChatMessage

# Initialize client
client = AILabClient("http://localhost:8000")

# Check API health
health = client.health_check()
print(f"API Status: {health['status']}")

# List all models
print("\n=== Available Models ===")
models = client.models.list()
for model in models:
    print(f"- {model.name} ({model.type}, {model.backend})")

# Get specific model
if models:
    model = client.models.get(models[0].name)
    print(f"\nModel Details: {model.name}")
    print(f"  Size: {model.size_gb} GB")
    print(f"  Memory: {model.estimated_memory_gb} GB")
    print(f"  Context: {model.context_length} tokens")

# Chat completion
print("\n=== Chat Example ===")
messages = [
    ChatMessage(role="user", content="What is machine learning?")
]

response = client.chat.complete(
    model=models[0].name,
    messages=messages,
    temperature=0.7,
    max_tokens=100
)

print(f"Response: {response.content}")
if response.total_tokens:
    print(f"Tokens used: {response.total_tokens}")
