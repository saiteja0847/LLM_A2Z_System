"""
AI Lab SDK - Python client library for AI Lab platform.

Usage:
    from ai_lab_sdk import AILabClient

    client = AILabClient("http://localhost:8000")

    # List models
    models = client.models.list()

    # Chat with a model
    response = client.chat.complete(
        model="qwen-1-5b",
        messages=[{"role": "user", "content": "Hello!"}]
    )

    # Start training
    job = client.training.train(
        base_model="qwen-1-5b",
        output_name="my-model",
        dataset_path="data.jsonl"
    )
"""

from .client import AILabClient
from .models import ModelManager, Model
from .chat import ChatClient, ChatMessage
from .training import TrainingManager, TrainingJob

__version__ = "0.1.0"

__all__ = [
    "AILabClient",
    "ModelManager",
    "Model",
    "ChatClient",
    "ChatMessage",
    "TrainingManager",
    "TrainingJob",
]
