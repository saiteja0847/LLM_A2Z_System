"""Command-line interface for AI Lab."""
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
from typing import Optional
import sys

from .core.registry import (
    Registry,
    ModelEntry,
    ModelBackend,
    ModelStatus,
    ModelType,
    Quantization,
    TrainingBackend,
    ModelNotFoundError
)
from .core.inference import get_inference_client
from .core.downloader import ModelDownloader
from .core.jobs import (
    get_job_manager,
    JobStatus,
    JobType,
    OptimizationJobConfig,
)
from .utils.memory import (
    get_memory_status,
    estimate_model_memory,
    estimate_training_memory,
    check_memory_available,
    format_memory_gb
)

app = typer.Typer(
    name="lab",
    help="AI Lab - Local LLM Platform for Apple Silicon",
    no_args_is_help=True
)
console = Console()

# Sub-command groups
models_app = typer.Typer(help="Model registry management")
train_app = typer.Typer(help="Training operations")
serve_app = typer.Typer(help="Model serving")
optimize_app = typer.Typer(help="Hyperparameter optimization with Ax")

app.add_typer(models_app, name="models")
app.add_typer(train_app, name="train")
app.add_typer(serve_app, name="serve")
app.add_typer(optimize_app, name="optimize")


# ─────────────────────────────────────────────────────────────
# MODELS COMMANDS
# ─────────────────────────────────────────────────────────────

@models_app.command("list")
def models_list(
    status: Optional[ModelStatus] = typer.Option(None, "--status", "-s"),
    backend: Optional[ModelBackend] = typer.Option(None, "--backend", "-b"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t"),
):
    """List all registered models."""
    registry = Registry()
    models = registry.list(status=status, backend=backend, tag=tag)

    if not models:
        console.print("[dim]No models registered. Use 'lab models register' to add one.[/dim]")
        return

    table = Table(title="Registered Models", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Type", style="green")
    table.add_column("Backend", style="yellow")
    table.add_column("Status", style="magenta")
    table.add_column("Quant", style="blue")
    table.add_column("Memory", justify="right")
    table.add_column("Description", style="dim", max_width=30)

    for m in models:
        mem = estimate_model_memory(m)
        desc = (m.description or "-")[:30]
        table.add_row(
            m.name,
            m.type.value,
            m.backend.value,
            m.status.value,
            m.quantization.value,
            format_memory_gb(mem),
            desc
        )

    console.print(table)

    # Memory status footer
    mem_status = get_memory_status()
    console.print(
        f"\n[dim]System Memory: {format_memory_gb(mem_status.available_gb)} available / "
        f"{format_memory_gb(mem_status.total_gb)} total "
        f"({mem_status.percent_used:.0f}% used)[/dim]"
    )


@models_app.command("register")
def models_register(
    name: str = typer.Argument(..., help="Unique model identifier (lowercase, hyphens only)"),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Local path to model"),
    backend: ModelBackend = typer.Option(ModelBackend.MLX, "--backend", "-b"),
    model_type: ModelType = typer.Option(ModelType.BASE, "--type", "-t"),
    parent: Optional[str] = typer.Option(None, "--parent", help="Parent model for adapters"),
    quant: Quantization = typer.Option(Quantization.INT4, "--quant", "-q"),
    size: Optional[float] = typer.Option(None, "--size", help="Model size in GB"),
    context: int = typer.Option(4096, "--context", "-c"),
    ollama_name: Optional[str] = typer.Option(None, "--ollama-name"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated tags"),
):
    """Register a new model in the registry."""
    registry = Registry()

    try:
        entry = ModelEntry(
            name=name,
            description=description,
            path=path,
            backend=backend,
            type=model_type,
            parent=parent,
            quantization=quant,
            size_gb=size,
            context_length=context,
            ollama_name=ollama_name,
            tags=tags.split(",") if tags else [],
        )

        # Estimate memory if not provided
        entry.estimated_memory_gb = estimate_model_memory(entry)

        registry.add(entry)
        console.print(f"[green]✓[/green] Registered model: [cyan]{name}[/cyan]")
        console.print(f"  Backend: {backend.value}")
        console.print(f"  Estimated memory: {format_memory_gb(entry.estimated_memory_gb)}")

    except Exception as e:
        console.print(f"[red]✗ Failed to register:[/red] {e}")
        raise typer.Exit(1)


@models_app.command("info")
def models_info(name: str = typer.Argument(..., help="Model name")):
    """Show detailed information about a model."""
    registry = Registry()

    try:
        entry = registry.get(name)

        console.print(f"\n[bold cyan]Model: {entry.name}[/bold cyan]")
        console.print(f"[dim]{'-' * 60}[/dim]")

        # Basic info
        console.print(f"Description: {entry.description or '-'}")
        console.print(f"Type: {entry.type.value}")
        console.print(f"Status: [{_status_color(entry.status)}]{entry.status.value}[/]")
        console.print(f"Backend: {entry.backend.value}")

        # Backend-specific info
        if entry.path:
            console.print(f"Path: {entry.path}")
        if entry.ollama_name:
            console.print(f"Ollama Name: {entry.ollama_name}")
        if entry.parent:
            console.print(f"Parent Model: {entry.parent}")

        # Specs
        console.print(f"\n[bold]Specifications:[/bold]")
        if entry.size_gb:
            console.print(f"  Size: {format_memory_gb(entry.size_gb)}")
        console.print(f"  Quantization: {entry.quantization.value}")
        console.print(f"  Context Length: {entry.context_length:,} tokens")
        mem = estimate_model_memory(entry)
        console.print(f"  Estimated Memory: {format_memory_gb(mem)}")

        # Metadata
        if entry.tags:
            console.print(f"\nTags: {', '.join(entry.tags)}")
        console.print(f"\nCreated: {entry.created_at.strftime('%Y-%m-%d %H:%M')}")
        console.print(f"Updated: {entry.updated_at.strftime('%Y-%m-%d %H:%M')}")

        if entry.notes:
            console.print(f"\nNotes: {entry.notes}")

    except ModelNotFoundError:
        console.print(f"[red]✗ Model not found:[/red] {name}")
        raise typer.Exit(1)


@models_app.command("remove")
def models_remove(
    name: str = typer.Argument(..., help="Model name"),
    force: bool = typer.Option(False, "--force", "-f", help="Force remove even with dependents"),
):
    """Remove a model from the registry."""
    registry = Registry()

    try:
        # Confirm deletion
        if not force:
            confirm = typer.confirm(f"Remove model '{name}'?")
            if not confirm:
                console.print("[yellow]Cancelled[/yellow]")
                return

        registry.remove(name, force=force)
        console.print(f"[green]✓[/green] Removed model: [cyan]{name}[/cyan]")

    except ValueError as e:
        console.print(f"[red]✗ Cannot remove:[/red] {e}")
        console.print("[dim]Use --force to remove anyway[/dim]")
        raise typer.Exit(1)
    except ModelNotFoundError:
        console.print(f"[red]✗ Model not found:[/red] {name}")
        raise typer.Exit(1)


@models_app.command("download")
def models_download(
    repo_id: str = typer.Argument(..., help="HuggingFace repo ID (e.g., mlx-community/Qwen2.5-1.5B-Instruct-4bit)"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Local model name (auto-generated if not provided)"),
    backend: ModelBackend = typer.Option(ModelBackend.MLX, "--backend", "-b"),
    quantization: Quantization = typer.Option(Quantization.INT4, "--quant", "-q"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated tags"),
):
    """Download a model from HuggingFace Hub."""
    downloader = ModelDownloader()

    try:
        console.print(f"[cyan]Downloading[/cyan] {repo_id}...")

        entry = downloader.download(
            repo_id=repo_id,
            name=name,
            backend=backend,
            quantization=quantization,
            auto_register=True,
            tags=tags.split(",") if tags else None,
        )

        console.print(f"\n[green]✓ Model downloaded and registered:[/green] [cyan]{entry.name}[/cyan]")
        console.print(f"  Path: {entry.path}")
        console.print(f"  Size: {format_memory_gb(entry.size_gb or 0)}")
        console.print(f"  Estimated Memory: {format_memory_gb(entry.estimated_memory_gb or 0)}")
        console.print(f"\n[dim]Use 'lab chat {entry.name}' to start chatting![/dim]")

    except ValueError as e:
        console.print(f"[red]✗ Download failed:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ Unexpected error:[/red] {e}")
        raise typer.Exit(1)


@models_app.command("search")
def models_search(
    query: str = typer.Argument(..., help="Search query (e.g., 'qwen', 'llama')"),
    organization: str = typer.Option("mlx-community", "--org", "-o", help="HuggingFace organization"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum results"),
):
    """Search for models on HuggingFace Hub."""
    downloader = ModelDownloader()

    try:
        console.print(f"[cyan]Searching[/cyan] {organization} for '{query}'...\n")

        results = downloader.search_models(query, organization, limit)

        if not results:
            console.print("[yellow]No models found[/yellow]")
            return

        table = Table(title=f"Search Results for '{query}'", show_header=True, header_style="bold cyan")
        table.add_column("Repository", style="cyan", no_wrap=True)
        table.add_column("Downloads", justify="right", style="green")
        table.add_column("Likes", justify="right", style="yellow")
        table.add_column("Tags", style="dim", max_width=40)

        for result in results:
            tags_str = ", ".join(result["tags"][:5]) if result["tags"] else "-"
            table.add_row(
                result["id"],
                f"{result['downloads']:,}",
                str(result["likes"]),
                tags_str
            )

        console.print(table)
        console.print(f"\n[dim]Use 'lab models download <repo-id>' to download a model[/dim]")

    except ValueError as e:
        console.print(f"[red]✗ Search failed:[/red] {e}")
        raise typer.Exit(1)


# ─────────────────────────────────────────────────────────────
# RLM COMMAND
# ─────────────────────────────────────────────────────────────

@app.command("rlm")
def rlm(
    model: str = typer.Argument(..., help="Model name from registry"),
    prompt: str = typer.Option(..., "--prompt", "-p", help="Prompt context (can be very large)"),
    root_prompt: str = typer.Option(None, "--root-prompt", "-r",
                                   help="Optional task/question about the context"),
    max_iterations: int = typer.Option(30, "--max-iterations", "-i",
                                       help="Maximum RLM iterations", min=1, max=100),
    environment: str = typer.Option("local", "--environment", "-e",
                                    help="REPL environment (local, docker)"),
    verbose: bool = typer.Option(False, "--verbose", "-v",
                                 help="Enable verbose output"),
    log_dir: str = typer.Option(None, "--log-dir", help="Log directory for RLM traces"),
):
    """
    RLM mode - handle near-infinite context through recursion.

    Recursive Language Models (RLM) can process inputs that far exceed
    the model's context window by intelligently chunking, processing
    each chunk, and aggregating results.

    Use this for:
    • Documents larger than model's context window
    • Complex multi-step analysis tasks
    • Tasks requiring chunking and aggregation

    Example:
        lab rlm qwen3-4b-instruct -p "huge_document.txt" -r "Summarize key points"

    This uses the same model as 'lab chat' but adds recursive capabilities.
    """
    from .core.rlm import SimpleRLMRouter, RLMConfig

    registry = Registry()

    # Validate model exists
    try:
        entry = registry.get(model)
    except ModelNotFoundError:
        console.print(f"[red]✗ Model not found:[/red] {model}")
        console.print("[dim]Run 'lab models list' to see available models[/dim]")
        raise typer.Exit(1)

    # Memory check
    required = estimate_model_memory(entry)
    ok, msg = check_memory_available(required)
    if not ok:
        console.print(f"[red]✗ Insufficient memory:[/red] {msg}")
        console.print("[yellow]Tip:[/yellow] Try a smaller or more quantized model")
        raise typer.Exit(1)

    console.print(f"[cyan]🔄 RLM Mode[/cyan]")
    console.print(f"[dim]{'='*60}[/dim]\n")
    console.print(f"  Model: [cyan]{model}[/cyan] ({entry.backend.value})")
    console.print(f"  Max iterations: [yellow]{max_iterations}[/yellow]")
    console.print(f"  Environment: [yellow]{environment}[/yellow]")
    console.print(f"  Context size: [yellow]{len(prompt):,}[/yellow] characters")
    if root_prompt:
        console.print(f"  Task: [cyan]{root_prompt}[/cyan]")
    console.print()

    try:
        # Create RLM config
        config = RLMConfig(
            model_name=model,
            max_iterations=max_iterations,
            environment_type=environment,
            verbose=verbose,
            log_dir=log_dir,
        )

        # Create router
        router = SimpleRLMRouter(model, config=config)

        console.print("[green]✓[/green] RLM initialized\n")
        console.print("[dim]Processing... (this may take a while for large inputs)[/dim]\n")

        # Run RLM completion
        result = router.complete(
            prompt=prompt,
            root_prompt=root_prompt,
        )

        console.print("[bold green]✓ RLM Complete[/bold green]\n")
        console.print(f"[bold]Result:[/bold]\n")
        console.print(result)
        console.print()

        # Show usage summary
        usage = router.get_usage_summary()
        console.print(f"\n[dim]Calls made: {usage.model_usage_summaries[model].total_calls}[/dim]")

    except ImportError as e:
        console.print(f"[red]✗ RLM library not installed:[/red]")
        console.print(f"[dim]{e}[/dim]")
        console.print("\n[yellow]Install RLM:[/yellow]")
        console.print("  pip install git+https://github.com/alexzhang13/rlm.git")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ RLM failed:[/red] {e}")
        raise typer.Exit(1)


# ─────────────────────────────────────────────────────────────
# RLM-FULL COMMAND (Full RLM with OpenAI backend)
# ─────────────────────────────────────────────────────────────

@app.command("rlm-full")
def rlm_full(
    model: str = typer.Argument(..., help="Model name from registry"),
    prompt: str = typer.Option(..., "--prompt", "-p", help="Prompt context (can be very large)"),
    root_prompt: str = typer.Option(None, "--root-prompt", "-r",
                                   help="Task/question about the context (required for best results)"),
    max_iterations: int = typer.Option(30, "--max-iterations", "-i",
                                       help="Maximum RLM iterations", min=1, max=100),
    environment: str = typer.Option("local", "--environment", "-e",
                                    help="REPL environment (local, docker, modal)"),
    verbose: bool = typer.Option(True, "--verbose", "-v",
                                 help="Enable verbose output (default: True for rlm-full)"),
    log_dir: str = typer.Option(None, "--log-dir", help="Log directory for RLM traces"),
):
    """
    RLM-Full mode - Full RLM capabilities with code execution.

    This uses the official RLM library via your OpenAI-compatible API,
    providing advanced features like code execution in REPL environments
    and sophisticated multi-step reasoning.

    **IMPORTANT:**
    • API server must be running: python -m uvicorn ai_lab.api.app:app
    • Best for complex analytical tasks requiring code execution
    • Use regular 'lab rlm' for simpler tasks

    When to use:
    • Processing very large documents (>100K characters)
    • Complex analysis requiring Python code execution
    • Tasks needing multi-step reasoning with sub-calls
    • Extracting patterns from logs/data using code

    Example:
        # Analyze logs using Python
        lab rlm-full qwen-1-5b \\
          --prompt "$(cat server.log)" \\
          --root-prompt "Use Python to find all error patterns and suggest fixes"

        # Extract citations from research paper
        lab rlm-full qwen-1-5b \\
          -p "$(cat paper.txt)" \\
          -r "Extract all citations and format as JSON"

    This provides full RLM capabilities vs 'lab rlm' which uses a simpler approach.
    """
    from .core.rlm import OpenAIRLMRouter, RLMConfig

    registry = Registry()

    # Validate model exists
    try:
        entry = registry.get(model)
    except ModelNotFoundError:
        console.print(f"[red]✗ Model not found:[/red] {model}")
        console.print("[dim]Run 'lab models list' to see available models[/dim]")
        raise typer.Exit(1)

    # Memory check
    required = estimate_model_memory(entry)
    ok, msg = check_memory_available(required)
    if not ok:
        console.print(f"[red]✗ Insufficient memory:[/red] {msg}")
        console.print("[yellow]Tip:[/yellow] Try a smaller or more quantized model")
        raise typer.Exit(1)

    console.print(f"[cyan]🔄 RLM-Full Mode (Official RLM Library)[/cyan]")
    console.print(f"[dim]{'='*60}[/dim]\n")
    console.print(f"  Model: [cyan]{model}[/cyan] ({entry.backend.value})")
    console.print(f"  Max iterations: [yellow]{max_iterations}[/yellow]")
    console.print(f"  Environment: [yellow]{environment}[/yellow]")
    console.print(f"  Context size: [yellow]{len(prompt):,}[/yellow] characters")
    if root_prompt:
        console.print(f"  Task: [cyan]{root_prompt}[/cyan]")
    console.print()

    try:
        # Create RLM config
        config = RLMConfig(
            model_name=model,
            max_iterations=max_iterations,
            environment_type=environment,
            verbose=verbose,
            log_dir=log_dir,
        )

        # Create router (this will check if server is running)
        router = OpenAIRLMRouter(model, config=config)

        console.print("[green]✓[/green] RLM-Full initialized (server connected)\n")
        console.print("[dim]Processing with full RLM capabilities...[/dim]")
        console.print("[dim](This may take a while - RLM performs multi-step reasoning)[/dim]\n")

        # Run RLM completion
        result = router.complete(
            prompt=prompt,
            root_prompt=root_prompt,
        )

        console.print("[bold green]✓ RLM-Full Complete[/bold green]\n")
        console.print(f"[bold]Result:[/bold]\n")
        console.print(result)
        console.print()

    except ConnectionError as e:
        console.print(f"[red]✗ Cannot connect to API server:[/red]")
        console.print(f"[dim]{e}[/dim]")
        console.print("\n[yellow]Start the server:[/yellow]")
        console.print("  python -m uvicorn ai_lab.api.app:app --host 0.0.0.0 --port 8000")
        console.print("\n[yellow]Or use simple RLM (no server needed):[/yellow]")
        console.print(f"  lab rlm {model} -p \"<prompt>\" -r \"<task>\"")
        raise typer.Exit(1)
    except ImportError as e:
        console.print(f"[red]✗ RLM library not installed:[/red]")
        console.print(f"[dim]{e}[/dim]")
        console.print("\n[yellow]Install RLM:[/yellow]")
        console.print("  pip install git+https://github.com/alexzhang13/rlm.git")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ RLM-Full failed:[/red] {e}")
        raise typer.Exit(1)


# ─────────────────────────────────────────────────────────────
# CHAT COMMAND
# ─────────────────────────────────────────────────────────────

@app.command("chat")
def chat(
    model_name: str = typer.Argument(..., help="Model to chat with"),
    max_tokens: int = typer.Option(512, "--max-tokens", "-m"),
    temperature: float = typer.Option(0.7, "--temp", "-t"),
):
    """Start an interactive chat session with a model."""
    registry = Registry()

    try:
        entry = registry.get(model_name)
    except ModelNotFoundError:
        console.print(f"[red]✗ Model not found:[/red] {model_name}")
        console.print("[dim]Run 'lab models list' to see available models[/dim]")
        raise typer.Exit(1)

    # Memory check
    required = estimate_model_memory(entry)
    ok, msg = check_memory_available(required)
    if not ok:
        console.print(f"[red]✗ Insufficient memory:[/red] {msg}")
        console.print("[yellow]Tip:[/yellow] Try a smaller or more quantized model")
        raise typer.Exit(1)

    console.print(f"[green]Loading[/green] {model_name} ({entry.backend.value})...")

    try:
        client = get_inference_client(entry)
    except Exception as e:
        console.print(f"[red]✗ Failed to load model:[/red] {e}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Model loaded")
    console.print("[dim]Type 'exit' or press Ctrl+C to quit[/dim]\n")

    # Chat loop
    while True:
        try:
            user_input = console.input("[bold blue]You:[/bold blue] ")
            if user_input.lower() in ("exit", "quit", "q"):
                break

            if not user_input.strip():
                continue

            console.print("[bold green]AI:[/bold green] ", end="")

            # Generate response
            response = client.complete(
                user_input,
                max_tokens=max_tokens,
                temperature=temperature
            )

            console.print(response)
            console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"\n[red]✗ Error:[/red] {e}")


# ─────────────────────────────────────────────────────────────
# OPTIMIZATION COMMANDS
# ─────────────────────────────────────────────────────────────

@optimize_app.command("start")
def optimize_start(
    model: str = typer.Argument(..., help="Base model to optimize"),
    dataset: str = typer.Argument(..., help="Path to training dataset (JSONL)"),
    trials: int = typer.Option(20, "--trials", "-t", help="Number of optimization trials", min=1, max=100),
    epochs: int = typer.Option(1, "--epochs", "-e", help="Epochs per trial (use 1 for speed)", min=1, max=5),
    name: str = typer.Option("lora_optimization", "--name", "-n", help="Experiment name"),
):
    """Start hyperparameter optimization to find best LoRA parameters."""
    job_manager = get_job_manager()
    registry = Registry()

    # Validate model exists
    try:
        registry.get(model)
    except ModelNotFoundError:
        console.print(f"[red]✗ Model not found:[/red] {model}")
        console.print("[dim]Run 'lab models list' to see available models[/dim]")
        raise typer.Exit(1)

    # Validate dataset exists
    dataset_path = Path(dataset)
    if not dataset_path.exists():
        console.print(f"[red]✗ Dataset not found:[/red] {dataset}")
        raise typer.Exit(1)

    console.print("\n[bold cyan]Starting Hyperparameter Optimization[/bold cyan]")
    console.print(f"[dim]{'='*60}[/dim]\n")
    console.print(f"  Model: [cyan]{model}[/cyan]")
    console.print(f"  Dataset: [cyan]{dataset}[/cyan]")
    console.print(f"  Trials: [yellow]{trials}[/yellow]")
    console.print(f"  Epochs per trial: [yellow]{epochs}[/yellow]")
    console.print(f"  Experiment: [cyan]{name}[/cyan]")
    console.print()

    # Create optimization job
    job = job_manager.create_optimization_job(
        base_model=model,
        dataset_path=str(dataset_path),
        num_trials=trials,
        experiment_name=name,
        experiment_epochs=epochs,
    )

    # Mock training function for now
    def mock_training_function(parameters):
        import random
        loss = 2.0 + random.uniform(-0.5, 0.5)
        return (loss, 0.0)

    # Start optimization in background
    job_manager.start_job_thread(job.id, job_manager.run_optimization_job, mock_training_function)

    console.print(f"[green]✓[/green] Optimization job started: [cyan]{job.id}[/cyan]")
    console.print(f"\n[dim]Track progress:[/dim]")
    console.print(f"  [dim]lab optimize status {job.id}[/dim]")
    console.print(f"  [dim]lab optimize results {job.id}[/dim]\n")


@optimize_app.command("status")
def optimize_status(
    job_id: str = typer.Argument(..., help="Optimization job ID"),
):
    """Show optimization job status."""
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job:
        console.print(f"[red]✗ Job not found:[/red] {job_id}")
        raise typer.Exit(1)

    if job.type != JobType.OPTIMIZATION:
        console.print(f"[red]✗ Not an optimization job:[/red] {job_id}")
        raise typer.Exit(1)

    # Status colors
    status_colors = {
        JobStatus.PENDING: "yellow",
        JobStatus.RUNNING: "blue",
        JobStatus.COMPLETED: "green",
        JobStatus.FAILED: "red",
        JobStatus.CANCELLED: "dim",
    }
    status_color = status_colors.get(job.status, "white")

    console.print(f"\n[bold]Optimization Job[/bold]")
    console.print(f"[dim]{'='*40}[/dim]\n")
    console.print(f"  ID: [cyan]{job.id}[/cyan]")
    console.print(f"  Status: [{status_color}]{job.status.value}[/{status_color}]")
    console.print(f"  Progress: [yellow]{job.progress*100:.1f}%[/yellow]")

    if job.started_at:
        console.print(f"  Started: {job.started_at.strftime('%Y-%m-%d %H:%M:%S')}")

    if job.completed_at:
        console.print(f"  Completed: {job.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")

    if job.error:
        console.print(f"\n[red]Error:[/red] {job.error}")

    # Show recent logs
    if job.logs:
        console.print(f"\n[bold]Recent Logs:[/bold]")
        for log in job.logs[-5:]:
            console.print(f"  [dim]{log}[/dim]")


@optimize_app.command("results")
def optimize_results(
    job_id: str = typer.Argument(..., help="Optimization job ID"),
):
    """Show optimization results and best parameters."""
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job:
        console.print(f"[red]✗ Job not found:[/red] {job_id}")
        raise typer.Exit(1)

    if job.type != JobType.OPTIMIZATION:
        console.print(f"[red]✗ Not an optimization job:[/red] {job_id}")
        raise typer.Exit(1)

    if job.status != JobStatus.COMPLETED:
        console.print(f"[yellow]⚠[/yellow] Job has not completed. Status: {job.status.value}")
        raise typer.Exit(1)

    if not job.result:
        console.print(f"[red]✗ No results available[/red]")
        raise typer.Exit(1)

    console.print("\n[bold green]✓ Optimization Complete[/bold green]")
    console.print(f"[dim]{'='*60}[/dim]\n")

    # Best parameters
    best_params = job.result.get("best_parameters", {})
    console.print("[bold]Best Parameters:[/bold]\n")

    param_display_names = {
        "learning_rate": "Learning Rate",
        "lora_r": "LoRA Rank",
        "lora_alpha": "LoRA Alpha",
        "batch_size": "Batch Size",
        "epochs": "Epochs",
        "warmup_ratio": "Warmup Ratio",
    }

    for key, value in best_params.items():
        name = param_display_names.get(key, key.replace("_", " ").title())
        if isinstance(value, float):
            console.print(f"  [cyan]{name}:[/cyan] {value:.6f}")
        else:
            console.print(f"  [cyan]{name}:[/cyan] {value}")

    # Parameter importance
    importance = job.result.get("parameter_importance", {})
    if importance:
        console.print(f"\n[bold]Parameter Importance:[/bold]\n")
        for param, score in sorted(importance.items(), key=lambda x: x[1], reverse=True):
            console.print(f"  [yellow]{param}:[/yellow] {score:.2%}")

    console.print(f"\n[dim]Use these parameters with 'lab train start' command[/dim]\n")


@optimize_app.command("list")
def optimize_list(
    status: Optional[JobStatus] = typer.Option(None, "--status", "-s"),
    limit: int = typer.Option(20, "--limit", "-l", min=1, max=100),
):
    """List all optimization jobs."""
    job_manager = get_job_manager()

    jobs = job_manager.list_jobs(status=status, job_type=JobType.OPTIMIZATION, limit=limit)

    if not jobs:
        console.print("[dim]No optimization jobs found[/dim]")
        return

    table = Table(title="Optimization Jobs", show_header=True, header_style="bold cyan")
    table.add_column("Job ID", style="cyan", no_wrap=True, max_width=8)
    table.add_column("Status", style="magenta")
    table.add_column("Model", style="green")
    table.add_column("Trials", justify="right")
    table.add_column("Progress", justify="right")
    table.add_column("Created", style="dim")

    for job in jobs:
        # Status color
        status_colors = {
            JobStatus.PENDING: "yellow",
            JobStatus.RUNNING: "blue",
            JobStatus.COMPLETED: "green",
            JobStatus.FAILED: "red",
        }
        status_color = status_colors.get(job.status, "white")

        table.add_row(
            job.id[:8],
            f"[{status_color}]{job.status.value}[/{status_color}]",
            job.config.get("base_model", "-"),
            str(job.config.get("num_trials", "-")),
            f"{job.progress*100:.0f}%",
            job.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)


# ─────────────────────────────────────────────────────────────
# SYSTEM COMMANDS
# ─────────────────────────────────────────────────────────────

@app.command("status")
def system_status():
    """Show system status and resource usage."""
    mem = get_memory_status()
    registry = Registry()
    models = registry.list()

    console.print("\n[bold]AI Lab System Status[/bold]")
    console.print("[dim]" + "=" * 60 + "[/dim]\n")

    # Memory
    console.print("[bold]Memory:[/bold]")
    console.print(f"  Total: {format_memory_gb(mem.total_gb)}")
    console.print(f"  Used: {format_memory_gb(mem.used_gb)} ({mem.percent_used:.1f}%)")
    console.print(f"  Available: {format_memory_gb(mem.available_gb)}")

    # Models
    console.print(f"\n[bold]Models:[/bold]")
    console.print(f"  Total: {len(models)}")

    by_status = {}
    for m in models:
        status = m.status.value
        by_status[status] = by_status.get(status, 0) + 1

    for status, count in by_status.items():
        console.print(f"  {status.capitalize()}: {count}")

    # Registry
    console.print(f"\n[bold]Registry:[/bold]")
    console.print(f"  Location: registry.yaml")
    console.print(f"  Models directory: models/")

    console.print()


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def _status_color(status: ModelStatus) -> str:
    """Get color for status."""
    colors = {
        ModelStatus.READY: "green",
        ModelStatus.PRODUCTION: "bold green",
        ModelStatus.CANDIDATE: "yellow",
        ModelStatus.DOWNLOADING: "blue",
        ModelStatus.ARCHIVED: "dim",
        ModelStatus.FAILED: "red",
    }
    return colors.get(status, "white")


if __name__ == "__main__":
    app()
