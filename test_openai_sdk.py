#!/usr/bin/env python3
"""Test OpenAI-compatible API with official OpenAI SDK."""
from openai import OpenAI
import json

# Create client pointing to local server
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"  # Local server doesn't require auth
)

print("=" * 70)
print("Testing OpenAI-Compatible API")
print("=" * 70)

# Test 1: List models
print("\n[Test 1] Listing available models...")
print("-" * 70)
models = client.models.list()
for model in models.data:
    print(f"  Model: {model.id}")
    print(f"  Owner: {model.owned_by}")
    print(f"  Created: {model.created}")
print()

# Test 2: Non-streaming completion
print("[Test 2] Non-streaming chat completion...")
print("-" * 70)
response = client.chat.completions.create(
    model="qwen-1-5b",
    messages=[
        {"role": "user", "content": "What is machine learning? Answer in one sentence."}
    ],
    max_tokens=100,
    temperature=0.3
)

print(f"Response:")
print(f"  ID: {response.id}")
print(f"  Model: {response.model}")
print(f"  Created: {response.created}")
print(f"  Finish Reason: {response.choices[0].finish_reason}")
print(f"  Message: {response.choices[0].message.content}")
print(f"  Usage:")
print(f"    Prompt tokens: {response.usage.prompt_tokens}")
print(f"    Completion tokens: {response.usage.completion_tokens}")
print(f"    Total tokens: {response.usage.total_tokens}")
print()

# Test 3: Streaming completion
print("[Test 3] Streaming chat completion...")
print("-" * 70)
print("Response: ", end="", flush=True)

stream = client.chat.completions.create(
    model="qwen-1-5b",
    messages=[
        {"role": "user", "content": "Explain neural networks in simple terms."}
    ],
    max_tokens=150,
    temperature=0.5,
    stream=True
)

collected_content = []
for chunk in stream:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        collected_content.append(content)
        print(content, end="", flush=True)

print("\n")
print(f"Total streamed: {len(''.join(collected_content))} characters")
print()

print("=" * 70)
print("✅ All tests passed!")
print("=" * 70)
print("\nThe OpenAI-compatible API is working correctly!")
print("You can now use this local server with any OpenAI-compatible tool.")
