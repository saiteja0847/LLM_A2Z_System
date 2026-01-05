# AI Lab Platform

<div align="center">

**Model, Train, Test, Use — Complete Local LLM Platform for Apple Silicon**

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%28Apple%20Silicon%29-lightgrey)](https://www.apple.com/mac/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[Features](#features) • [Quick Start](#quick-start) • [Documentation](#documentation) • [Architecture](#architecture)

</div>

---

## 🌟 Overview

**AI Lab Platform** is a comprehensive, production-ready system for running large language models locally on Apple Silicon. It provides everything you need to download, train, optimize, and deploy LLMs with an intuitive web interface and powerful CLI.

### 🎯 Key Capabilities

- **🚀 Model Management** — Download, register, and manage models from HuggingFace
- **⚡ Inference** — Run models with MLX acceleration (Metal Performance Shaders)
- **🎓 Training** — Fine-tune models with LoRA adapters and custom datasets
- **🔬 Optimization** — Hyperparameter tuning with the Ax platform
- **🔄 RLM** — Recursive Language Models for near-infinite context processing
- **🌐 Web UI** — Beautiful React-based interface for all operations
- **🔌 OpenAI API** — Drop-in compatible API for existing tools
- **💻 CLI** — Powerful command-line interface for automation

---

## ✨ Features

### Model Management
- **Multi-Backend Support** — MLX, GGUF, Ollama, and remote APIs
- **Smart Downloads** — Automatic model fetching from HuggingFace with progress tracking
- **Model Registry** — YAML-based configuration for easy management
- **Memory Estimation** — Automatic memory requirements calculation
- **Flexible Quantization** — Support for INT4, INT8, FP16, and more

### Training Pipeline
- **LoRA Fine-tuning** — Efficient adapter-based training
- **Custom Datasets** — JSONL format support with validation
- **Job Management** — Track training progress with real-time status
- **Adapter Management** — Save, load, and combine trained adapters
- **MLX Backend** — GPU-accelerated training on Apple Silicon

### Hyperparameter Optimization
- **Ax Platform Integration** — Bayesian optimization for efficient tuning
- **Parallel Trials** — Run multiple experiments simultaneously
- **Best Trial Selection** — Automatically identify optimal parameters
- **Job History** — Track all optimization runs with detailed metrics

### Recursive Language Models (RLM)
- **Simple RLM** — Fast chunked recursion for large documents (15-30s)
- **Full RLM** — Advanced processing with code execution (2+ min)
- **Near-Infinite Context** — Process documents of any size
- **Dual Router Architecture** — Choose between speed and capabilities

### API & Web Interface
- **FastAPI Backend** — Modern, async Python API
- **OpenAI-Compatible** — Drop-in replacement for OpenAI API
- **WebSocket Streaming** — Real-time token streaming for chat
- **React Frontend** — Modern, responsive UI with Tailwind CSS
- **Markdown Rendering** — Beautiful formatted responses

---

## 🚀 Quick Start

### Prerequisites

- **macOS** with Apple Silicon (M1/M2/M3/M4)
- **Python 3.11+** (we recommend using pyenv or conda)
- **Node.js 18+** and npm (for web UI)
- **8GB+ RAM** (16GB+ recommended for training)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/LLM_A2Z_System.git
cd LLM_A2Z_System

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -e .

# Install RLM library (optional, for advanced RLM features)
pip install git+https://github.com/alexzhang13/rlm.git

# Install web UI dependencies
cd web/web
npm install
cd ../..
```

### Start the Platform

```bash
# Launch both backend and frontend with one command
./start.sh
```

This will start:
- **Backend API** at `http://localhost:8000`
- **Web UI** at `http://localhost:5174`
- **API Docs** at `http://localhost:8000/docs`

Press `Ctrl+C` to stop both servers.

### Your First Model

```bash
# Download a model
lab models download qwen2.5-1.5b-instruct-4bit

# Register it in the registry
lab models register \
  --name qwen-1.5b \
  --backend mlx \
  --path ./models/qwen2.5-1.5b-instruct-4bit \
  --type base \
  --quantization int4

# List all models
lab models list

# Start chatting!
lab chat qwen-1.5b
```

---

## 📚 Documentation

### CLI Reference

#### Model Commands

```bash
# List all registered models
lab models list

# Download a model from HuggingFace
lab models download <model_id>

# Register a model in the registry
lab models register \
  --name <name> \
  --backend <mlx|gguf|ollama|remote> \
  --path <path> \
  --type <base|instruct>

# Update model configuration
lab models update <name> --description "New description"

# Remove a model from registry
lab models delete <name>

# Check model memory requirements
lab models check-memory <name>
```

#### Chat Commands

```bash
# Start interactive chat
lab chat <model-name>

# Chat with streaming enabled
lab chat <model-name> --stream

# Use specific generation parameters
lab chat <model-name> \
  --temperature 0.7 \
  --max-tokens 512 \
  --top-p 0.9
```

#### Training Commands

```bash
# Start a training job
lab train start <base-model> \
  --dataset ./datasets/my_data.jsonl \
  --output-adapter ./adapters/my_adapter

# List all training jobs
lab train list

# Check job status
lab train status <job-id>

# View job details
lab train inspect <job-id>

# Cancel a running job
lab train cancel <job-id>
```

#### Optimization Commands

```bash
# Run hyperparameter optimization
lab optimize run <model> \
  --dataset ./datasets/data.jsonl \
  --parameters learning_rate,rank,lora_alpha \
  --trials 10 \
  --output ./optimization/results

# List optimization jobs
lab optimize list

# View job details
lab optimize inspect <job-id>

# Get best trial
lab optimize best <job-id>
```

#### RLM Commands

```bash
# Simple RLM (fast, for large documents)
lab rlm <model> \
  --prompt "$(cat large_document.txt)" \
  --root-prompt "Summarize the key findings"

# Full RLM with code execution
lab rlm-full <model> \
  --prompt "$(cat logs.txt)" \
  --root-prompt "Use Python to analyze error patterns" \
  --max-iterations 30
```

### API Reference

#### OpenAI-Compatible Endpoints

```bash
# Chat completions (OpenAI format)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-1.5b",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'

# Streaming chat
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-1.5b",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": true
  }'

# List available models
curl http://localhost:8000/v1/models
```

#### Native API Endpoints

```bash
# Chat with custom model
curl -X POST http://localhost:8000/api/v1/chat/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-1.5b",
    "messages": [{"role": "user", "content": "Explain quantum computing"}]
  }'

# Start training job
curl -X POST http://localhost:8000/api/v1/training/train \
  -H "Content-Type: application/json" \
  -d '{
    "base_model": "qwen-1.5b",
    "dataset_path": "./datasets/data.jsonl",
    "output_adapter_path": "./adapters/my_adapter"
  }'

# Run optimization
curl -X POST http://localhost:8000/api/v1/optimization/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-1.5b",
    "dataset_path": "./datasets/data.jsonl",
    "parameters": ["learning_rate", "rank"],
    "n_trials": 10
  }'

# Simple RLM completion
curl -X POST http://localhost:8000/api/v1/rlm/complete \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-1.5b",
    "prompt": "...large context...",
    "root_prompt": "Summarize this"
  }'
```

For complete API documentation, visit `/docs` when the server is running.

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Web UI (React)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  Models  │ │  Chat    │ │ Training │ │   RLM    │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐             │
│  │    API     │ │   Routers  │ │  WebSocket │             │
│  │  Gateway   │ │            │ │  Streaming │             │
│  └────────────┘ └────────────┘ └────────────┘             │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   MLX        │ │   Training   │ │  Optimization│
│   Backend    │ │   Pipeline   │ │     (Ax)     │
└──────────────┘ └──────────────┘ └──────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                ┌──────────────┐
                │  Model       │
                │  Registry    │
                │  (YAML)      │
                └──────────────┘
```

### Core Components

#### **Backend (`src/ai_lab/`)**

- **`api/`** — FastAPI application and routers
  - `app.py` — Main application setup
  - `routers/openai.py` — OpenAI-compatible endpoints
  - `routers/models.py` — Model management
  - `routers/training.py` — Training operations
  - `routers/optimization.py` — Hyperparameter optimization
  - `routers/rlm.py` — Recursive Language Model endpoints
  - `routers/stream.py` — WebSocket streaming

- **`core/`** — Core business logic
  - `registry.py` — Model registry management
  - `inference.py` — Inference client factory
  - `downloader.py` — HuggingFace model downloader
  - `jobs.py` — Job queue and management
  - `rlm/` — Recursive Language Model implementation
    - `simple_router.py` — Fast chunked recursion
    - `openai_router.py` — Full RLM with code execution
  - `optimization/` — Hyperparameter optimization
    - `ax_optimizer.py` — Ax platform integration

- **`backends/`** — Model inference backends
  - `mlx_backend.py` — MLX-accelerated inference
  - `gguf_backend.py` — GGUF quantized models
  - `ollama_backend.py` — Ollama integration
  - `remote_backend.py` — Remote API calls

- **`utils/`** — Utilities
  - `memory.py` — Memory estimation and tracking

#### **Frontend (`web/web/src/`)**

- **`components/`** — React components
  - `ModelList.tsx` — Model browser
  - `ChatInterface.tsx` — Chat UI
  - `TrainingForm.tsx` — Training configuration
  - `OptimizationInterface.tsx` — Optimization UI
  - `RLMInterface.tsx` — RLM interface
  - `DownloadModel.tsx` — Model downloader

- **`lib/`** — Core libraries
  - `api.ts` — API client with axios

---

## 🎮 Usage Examples

### Example 1: Chat with a Local Model

```bash
# Start interactive chat
lab chat qwen-1.5b

# Try some prompts
>>> Explain quantum computing in simple terms
>>> Write a Python function to calculate fibonacci numbers
>>> Translate to Spanish: "Hello, how are you?"
```

### Example 2: Fine-tune a Model

```bash
# Create a training dataset
cat > datasets/sentiment.jsonl << EOF
{"text": "I love this product!", "label": "positive"}
{"text": "This is terrible.", "label": "negative"}
{"text": "It's okay, not great.", "label": "neutral"}
EOF

# Start training
lab train start qwen-1.5b \
  --dataset datasets/sentiment.jsonl \
  --rank 8 \
  --learning-rate 1e-4 \
  --epochs 3 \
  --output-adapter adapters/sentiment

# Monitor progress
lab train list
lab train status <job-id>

# Use the trained adapter
lab chat qwen-1.5b --adapter adapters/sentiment
```

### Example 3: Hyperparameter Optimization

```bash
# Run optimization with multiple trials
lab optimize run qwen-1.5b \
  --dataset datasets/sentiment.jsonl \
  --parameters learning_rate,rank,lora_alpha \
  --learning_rate-range 1e-5,1e-3 \
  --rank-range 4,16 \
  --lora_alpha-range 8,32 \
  --trials 10 \
  --output optimization_results

# Get best parameters
lab optimize best <job-id>

# Use best parameters for training
lab train start qwen-1.5b \
  --dataset datasets/sentiment.jsonl \
  --learning-rate 0.0003 \
  --rank 16 \
  --lora-alpha 32
```

### Example 4: Process Large Documents with RLM

```bash
# Simple RLM for quick summarization
lab rlm qwen-1.5b \
  --prompt "$(cat research_paper.txt)" \
  --root-prompt "Summarize the key findings and methodology"

# Full RLM for complex analysis
lab rlm-full qwen-1.5b \
  --prompt "$(cat server_logs.txt)" \
  --root-prompt "Use Python to analyze error patterns and suggest fixes" \
  --max-iterations 50
```

### Example 5: Use as OpenAI API Replacement

```bash
# Set environment variable
export OPENAI_API_BASE="http://localhost:8000/v1"
export OPENAI_API_KEY="dummy"  # Not used but required by some clients

# Use with any OpenAI-compatible tool
# OpenAI Python SDK
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"
)

response = client.chat.completions.create(
    model="qwen-1.5b",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

---

## ⚙️ Configuration

### Model Registry (`registry.yaml`)

Models are registered in `registry.yaml`:

```yaml
models:
  - name: qwen-1.5b
    description: Qwen2.5 1.5B Instruct (4-bit)
    type: base
    backend: mlx
    path: ./models/qwen2.5-1.5b-instruct-4bit
    quantization: int4
    context_length: 32768
    status: ready
    tags:
      - instruct
      - chat
      - qwen
```

### Environment Variables

```bash
# API Configuration
export AI_LAB_HOST="0.0.0.0"
export AI_LAB_PORT="8000"
export AI_LAB_LOG_LEVEL="info"

# Model Paths
export AI_LAB_MODEL_DIR="./models"
export AI_LAB_ADAPTER_DIR="./adapters"

# Training
export AI_LAB_DATASET_DIR="./datasets"
export AI_LAB_JOB_DIR="./jobs"
```

---

## 🔧 Development

### Project Structure

```
LLM_A2Z_System/
├── src/ai_lab/           # Python backend
│   ├── api/              # FastAPI application
│   ├── backends/         # Inference backends
│   ├── core/             # Core business logic
│   ├── utils/            # Utilities
│   └── cli.py            # Command-line interface
├── web/web/              # React frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   └── lib/          # API client
│   └── package.json
├── tests/                # Test suite
├── docs/                 # Documentation
├── registry.yaml         # Model registry
├── pyproject.toml        # Python package config
├── requirements.txt      # Python dependencies
└── start.sh              # Launch script
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=src/ai_lab --cov-report=html

# Run specific test file
pytest tests/test_registry.py
```

### Code Style

```bash
# Format code with ruff
ruff format src/

# Lint code
ruff check src/

# Type checking
mypy src/
```

### Building for Production

```bash
# Build frontend
cd web/web
npm run build
cd ../..

# The built files will be in web/web/dist/
# Configure FastAPI to serve static files
```

---

## 📖 Advanced Topics

### RLM Integration

The platform includes advanced Recursive Language Model capabilities for processing near-infinite context:

```bash
# Simple RLM (15-30 seconds)
lab rlm qwen-1.5b -p "large_doc.txt" -r "Summarize"

# Full RLM with code execution (2+ minutes)
lab rlm-full qwen-1.5b -p "logs.txt" -r "Analyze with Python"
```

See [docs/RLM_INTEGRATION.md](docs/RLM_INTEGRATION.md) for complete RLM documentation.

### Custom Training Datasets

Create JSONL files with your training data:

```jsonl
{"text": "User message here", "label": "category"}
{"text": "Another example", "label": "another_category"}
```

Supported formats:
- **Classification** — `text` + `label`
- **QA** — `question` + `answer`
- **Instruction** — `instruction` + `output` + `input` (optional)

### Memory Optimization

For systems with limited RAM:

```bash
# Check memory requirements before downloading
lab models check-memory <model-name>

# Use smaller models or quantization
lab models download tinyllama-1b-chat  # ~1GB

# Monitor memory during training
lab train start ... --max-memory-gb 8
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 🙏 Acknowledgments

- **MLX Team** — For the excellent MLX framework
- **HuggingFace** — For the model hub and datasets
- **Ax Platform** — For hyperparameter optimization tools
- **RLM Project** — For the Recursive Language Model implementation
- **Qwen Team** — For the amazing Qwen models

---

## 📞 Support

- **Documentation** — See the [docs/](docs/) directory for detailed technical documentation

---

## 🗺️ Roadmap

- [ ] WebUI-based training configuration
- [ ] Model comparison and benchmarking tools
- [ ] Multi-GPU support (when available in MLX)
- [ ] Advanced RLM features (Python REPL, sub-LLM delegation)
- [ ] Model versioning and A/B testing
- [ ] Export trained models to GGUF format
- [ ] Collaborative training (distributed LoRA)

---

<div align="center">

**Built with ❤️ for the Apple Silicon community**

[⬆ Back to Top](#ai-lab-platform)

</div>
