#!/usr/bin/env python3
"""Test script for model downloader."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ai_lab.core.downloader import ModelDownloader
from rich.console import Console

console = Console()

# Test name generation
downloader = ModelDownloader()

test_cases = [
    "mlx-community/Qwen2.5-1.5B-Instruct-4bit",
    "mlx-community/phi-2-4bit",
    "mistralai/Mistral-7B-v0.1",
]

console.print("\n[bold cyan]Testing Name Generation[/bold cyan]\n")

for repo_id in test_cases:
    name = downloader._generate_name(repo_id)
    console.print(f"  {repo_id}")
    console.print(f"  → [green]{name}[/green]\n")

# Test search
console.print("[bold cyan]Testing Search[/bold cyan]\n")
results = downloader.search_models("qwen", limit=3)

for r in results:
    console.print(f"  [cyan]{r['id']}[/cyan]")
    console.print(f"    Downloads: {r['downloads']:,}, Likes: {r['likes']}")

console.print("\n[green]✅ Downloader validation complete![/green]")
