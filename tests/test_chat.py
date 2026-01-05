#!/usr/bin/env python3
"""Test script for CLI chat command."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ai_lab.core.registry import Registry
from src.ai_lab.core.inference import get_inference_client
from src.ai_lab.utils.memory import estimate_model_memory, check_memory_available
from rich.console import Console

console = Console()

# Load model
registry = Registry()
model = registry.get("qwen-1-5b")

# Memory check
required = estimate_model_memory(model)
ok, msg = check_memory_available(required)

console.print(f"\n[bold cyan]AI Lab Chat Test[/bold cyan]")
console.print(f"Model: {model.name}")
console.print(f"Memory check: {msg}")

if not ok:
    console.print(f"[red]Cannot proceed: {msg}[/red]")
    sys.exit(1)

# Load client
console.print("\n[yellow]Loading model...[/yellow]")
client = get_inference_client(model)
console.print("[green]✓ Model loaded![/green]\n")

# Test questions
questions = [
    "What is 2+2?",
    "Name three planets in our solar system.",
    "What is Python programming language used for?"
]

for i, question in enumerate(questions, 1):
    console.print(f"[bold blue]Q{i}:[/bold blue] {question}")
    console.print("[bold green]A{i}:[/bold green] ", end="")

    response = client.complete(question, max_tokens=100, temperature=0.7)
    console.print(response)
    console.print()

console.print("[green]✅ Chat test complete![/green]")
