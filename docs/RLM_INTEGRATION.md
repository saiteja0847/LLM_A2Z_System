# RLM Integration Guide

## Overview

RLM (Recursive Language Models) enables your AI Lab platform to handle **near-infinite context lengths** by recursively chunking and processing inputs. This integration provides **two router implementations** to meet different needs:

- **SimpleRLMRouter** - Basic recursive chunking (fast, no server needed)
- **OpenAIRLMRouter** - Full RLM library with code execution (requires server)

## Key Features

✅ **Zero Registry Changes** - Works with existing models
✅ **Dual Router Architecture** - Choose between simple and full RLM
✅ **Backend Agnostic** - MLX, Remote, Ollama, GGUF all supported
✅ **CLI & API** - Both interfaces fully supported
✅ **Code Execution** - Full RLM can execute Python for analysis

## Installation

```bash
# Install RLM library
pip install git+https://github.com/alexzhang13/rlm.git

# Or install from requirements.txt
pip install -r requirements.txt
```

## Usage

### Mode 1: Standard (Direct)

For normal interactions within the model's context window:

```bash
# CLI
lab chat qwen3-4b-instruct

# API
POST /api/v1/chat
{
  "model": "qwen3-4b-instruct",
  "messages": [{"role": "user", "content": "Your prompt"}]
}
```

### Mode 2: Simple RLM (Fast Recursive Chunking)

For large documents needing quick processing:

```bash
# CLI
lab rlm qwen3-4b-instruct \
  --prompt "$(cat huge_document.txt)" \
  --root-prompt "Summarize the key findings"

# API
POST /api/v1/rlm/complete
{
  "model": "qwen3-4b-instruct",
  "prompt": "...100K+ character document...",
  "root_prompt": "Summarize the key findings"
}
```

**Characteristics:**
- ✅ No server needed (direct MLX access)
- ✅ Fast processing
- ✅ Basic chunking and aggregation
- ❌ No code execution
- ❌ Less sophisticated reasoning

### Mode 3: Full RLM (Advanced with Code Execution)

For complex tasks requiring code execution and sophisticated reasoning:

```bash
# CLI (requires API server running)
lab rlm-full qwen3-4b-instruct \
  --prompt "$(cat huge_log_file.txt)" \
  --root-prompt "Use Python to analyze error patterns" \
  --max-iterations 30

# API
POST /api/v1/rlm/full
{
  "model": "qwen3-4b-instruct",
  "prompt": "...100K+ character log file...",
  "root_prompt": "Use Python to find all error patterns and suggest fixes",
  "max_iterations": 30,
  "environment": "local"
}
```

**Characteristics:**
- ✅ Code execution in REPL environment
- ✅ Sophisticated multi-step reasoning
- ✅ Best for complex analytical tasks
- ❌ Requires API server
- ❌ Slower processing
- ❌ Higher resource usage

## Which Router Should I Use?

| Use Case | Recommended Router | Command |
|----------|-------------------|---------|
| Simple summaries | SimpleRLMRouter | `lab rlm` |
| Quick document analysis | SimpleRLMRouter | `lab rlm` |
| Log file analysis with Python | OpenAIRLMRouter | `lab rlm-full` |
| Complex data analysis | OpenAIRLMRouter | `lab rlm-full` |
| Tasks requiring code execution | OpenAIRLMRouter | `lab rlm-full` |
| Large text extraction | SimpleRLMRouter | `lab rlm` |
| Multi-step reasoning with computation | OpenAIRLMRouter | `lab rlm-full` |

## CLI Reference

### Simple RLM Command

```bash
# Basic usage
lab rlm <model> --prompt "<context>" --root-prompt "<task>"

# Options:
  --prompt, -p          Context/document (required)
  --root-prompt, -r     Task/question about context (optional)

# Example with file
lab rlm qwen3-4b-instruct \
  -p "$(cat document.txt)" \
  -r "Extract all citations"
```

### Full RLM Command (requires server)

```bash
# Basic usage
lab rlm-full <model> --prompt "<context>" --root-prompt "<task>"

# Options:
  --prompt, -p          Context/document (required)
  --root-prompt, -r     Task/question about context (optional)
  --max-iterations, -i  Maximum iterations (default: 30)
  --environment, -e     REPL environment: local, docker (default: local)
  --verbose, -v         Enable verbose output
  --log-dir             Directory for RLM trace logs

# Example with code execution
lab rlm-full qwen3-4b-instruct \
  -p "$(cat server_logs.txt)" \
  -r "Use Python to find all errors" \
  --max-iterations 50 \
  --verbose
```

## API Reference

### Endpoints

#### `POST /api/v1/rlm/complete`
Run Simple RLM completion on large context (fast, no server dependency).

**Request:**
```json
{
  "model": "qwen3-4b-instruct",
  "prompt": "...large context...",
  "root_prompt": "Summarize key points"
}
```

**Response:**
```json
{
  "response": "The summarized findings...",
  "model": "qwen3-4b-instruct",
  "prompt_size": 250000,
  "iterations": 0,
  "sub_calls": 5,
  "execution_time": 15.3,
  "usage_summary": {}
}
```

#### `POST /api/v1/rlm/full`
Run Full RLM completion with code execution (requires official RLM library).

**Request:**
```json
{
  "model": "qwen3-4b-instruct",
  "prompt": "...100K+ character document...",
  "root_prompt": "Use Python to analyze this data and extract patterns",
  "max_iterations": 30,
  "environment": "local",
  "verbose": false
}
```

**Response:**
```json
{
  "response": "Analysis complete. Found 3 main patterns...",
  "model": "qwen3-4b-instruct",
  "prompt_size": 150000,
  "iterations": 0,
  "sub_calls": 0,
  "execution_time": 120.5,
  "usage_summary": {}
}
```

**Difference:**
- `/complete` - Uses SimpleRLMRouter (direct MLX, fast)
- `/full` - Uses OpenAIRLMRouter (via API, code execution, slower)

#### `GET /api/v1/rlm/models`
List all RLM-compatible models (all registered models).

#### `GET /api/v1/rlm/status`
Check RLM installation and server status.

## Python API

### Using SimpleRLMRouter (Fast, Direct)

```python
from ai_lab.core.rlm import SimpleRLMRouter

# Create router with any model
router = SimpleRLMRouter("qwen3-4b-instruct")

# Process large document
with open("huge_document.txt") as f:
    large_doc = f.read()

result = router.complete(
    prompt=large_doc,
    root_prompt="Summarize the key findings"
)

print(result)
```

### Using OpenAIRLMRouter (Full RLM with Code Execution)

```python
from ai_lab.core.rlm import OpenAIRLMRouter, RLMConfig

# Create router (requires API server running)
router = OpenAIRLMRouter("qwen3-4b-instruct")

# Process complex task with code execution
with open("server_logs.txt") as f:
    logs = f.read()

result = router.complete(
    prompt=logs,
    root_prompt="Use Python to analyze error patterns and suggest fixes"
)

print(result)
```

### Custom Configuration

```python
from ai_lab.core.rlm import OpenAIRLMRouter, RLMConfig

config = RLMConfig(
    model_name="qwen3-4b-instruct",
    max_iterations=50,
    environment_type="docker",  # Isolated environment
    verbose=True,
    log_dir="./rlm_logs"
)

router = OpenAIRLMRouter("qwen3-4b-instruct", config=config)
result = router.complete(prompt, root_prompt="Analyze")
```

## Architecture

### Dual Router Design

```
┌─────────────────────────────────────────────────────────────┐
│  User Interface                                            │
│  • CLI: lab rlm <model>      (SimpleRLMRouter)            │
│  • CLI: lab rlm-full <model> (OpenAIRLMRouter)            │
│  • API: POST /api/v1/rlm/complete                         │
│  • API: POST /api/v1/rlm/full                             │
└──────────────────┬────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌──────────────────┐  ┌──────────────────────┐
│ SimpleRLMRouter  │  │ OpenAIRLMRouter      │
│ (Fast, Direct)   │  │ (Full RLM, via API)  │
└─────────┬────────┘  └──────────┬───────────┘
          │                      │
          ▼                      ▼
┌──────────────────┐  ┌──────────────────────┐
│ MLXClient        │  │ OpenAI-Compatible    │
│ (Direct Access)  │  │ API Endpoints        │
└──────────────────┘  └──────────┬───────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │  Official RLM        │
                      │  Library             │
                      │  (Code Execution)    │
                      └──────────────────────┘
```

## Comparison: All Three Modes

| Aspect | Standard Mode | Simple RLM | Full RLM |
|--------|--------------|-----------|----------|
| **Context Limit** | Model's context window (e.g., 32K) | Large (~100K chars) | Near-infinite |
| **Speed** | Fastest (1-5s) | Fast (15-30s) | Slowest (60-180s) |
| **Server Required** | No | No | Yes |
| **Code Execution** | No | No | Yes |
| **Use Case** | Chat, Q&A | Large docs | Complex analysis |
| **Complexity** | Simple | Medium | High |
| **Command** | `lab chat` | `lab rlm` | `lab rlm-full` |

## When to Use Each Router

### Standard Mode (`lab chat`)
✅ **Use when:**
- Simple questions within context limit
- Fast response needed
- Interactive chat sessions
- Token efficiency matters
- Single-pass processing sufficient

❌ **Don't use when:**
- Input exceeds context window
- Complex document analysis needed

### Simple RLM (`lab rlm`)
✅ **Use when:**
- Input is large but manageable (<100K chars)
- Quick document processing needed
- No server available or wanted
- Basic summarization or extraction
- Faster processing is priority

❌ **Don't use when:**
- Code execution required
- Very complex multi-step reasoning
- Input >100K characters

### Full RLM (`lab rlm-full`)
✅ **Use when:**
- Input is very large (>100K chars)
- Code execution needed (e.g., "Use Python to...")
- Complex multi-step analysis required
- Sophisticated reasoning needed
- Server is available

❌ **Don't use when:**
- Quick results needed
- Server not running
- Simple task sufficient

## Examples

### Example 1: Summarizing a Book

```bash
# Book is 500K characters (way beyond 32K context)
lab rlm qwen3-4b-instruct \
  --prompt "$(cat book.txt)" \
  --root-prompt "Summarize each chapter and provide overall themes"
```

### Example 2: Analyzing Logs (Simple RLM)

```bash
# Server logs are 200K lines
lab rlm llama3-8b \
  --prompt "$(cat server.log)" \
  --root-prompt "Find all errors and patterns, suggest fixes"
```

### Example 3: Log Analysis with Python (Full RLM)

```bash
# Server logs with complex error patterns requiring code analysis
lab rlm-full qwen3-4b-instruct \
  --prompt "$(cat application.log)" \
  --root-prompt "Use Python to: 1) Parse all timestamps, 2) Find error clusters, 3) Calculate time between errors" \
  --environment local \
  --verbose
```

### Example 4: Processing Datasets

**Simple RLM (Basic extraction):**
```python
from ai_lab.core.rlm import SimpleRLMRouter

router = SimpleRLMRouter("qwen3-4b-instruct")

# Dataset has 1000 JSON records
with open("dataset.jsonl") as f:
    dataset = f.read()

result = router.complete(
    prompt=dataset,
    root_prompt="Extract all unique entities and their relationships"
)
```

**Full RLM (With code execution):**
```python
from ai_lab.core.rlm import OpenAIRLMRouter

router = OpenAIRLMRouter("qwen3-4b-instruct")

# Dataset requiring statistical analysis
with open("sales_data.jsonl") as f:
    data = f.read()

result = router.complete(
    prompt=data,
    root_prompt="Use Python to calculate: mean, median, std dev, and identify outliers"
)
```

## Troubleshooting

### Server Not Running (OpenAIRLMRouter)

```bash
ConnectionError: Cannot connect to API server at http://localhost:8000
Make sure the server is running:
  python -m uvicorn ai_lab.api.app:app --host 0.0.0.0 --port 8000
```

**Solution:**
```bash
# Start the API server
python -m uvicorn ai_lab.api.app:app --host 0.0.0.0 --port 8000

# Or use SimpleRLMRouter instead (no server needed)
lab rlm <model> -p "<prompt>" -r "<task>"
```

### RLM Not Installed

```bash
ImportError: RLM library not installed

# Solution:
pip install git+https://github.com/alexzhang13/rlm.git
```

### Model Not Found

```bash
Model 'xyz' not found in registry

# Solution:
lab models list  # See available models
lab models register ...  # Add your model
```

### Memory Issues

```bash
Insufficient memory

# Solution:
# Use a smaller model or quantization
lab rlm tiny-llama -p "doc.txt" -r "summarize"
```

### Slow Performance

```bash
# RLM makes multiple calls - this is normal!

# To speed up:
# 1. Reduce max_iterations
lab rlm model -p "doc.txt" -r "task" -i 10

# 2. Use faster model
lab rlm faster-model -p "doc.txt" -r "task"
```

## Technical Details

### How RLM Works

1. **Chunking**: Large input is intelligently chunked
2. **Processing**: Each chunk processed with sub-LLM calls
3. **Aggregation**: Results combined across iterations
4. **Final Answer**: Aggregated results synthesized into final response

### Adapter Pattern

The `InferenceClientAdapter` bridges your existing `InferenceClient` implementations (MLXClient, RemoteClient, etc.) with RLM's `BaseLM` interface. This allows ANY backend to work with RLM without modification.

### REPL Environments

RLM executes code in a REPL environment to process chunks:
- **local**: Same process (default, fastest)
- **docker**: Isolated container (safer)
- **modal**: Cloud sandbox (most isolated)

## Performance Tips

1. **Start with local environment** - fastest for development
2. **Use appropriate iteration limits** - 30 is default, reduce for speed
3. **Choose right model** - smaller models for simple tasks
4. **Enable verbose** - understand what's happening during development
5. **Monitor sub-calls** - more calls = more time/cost

## Future Enhancements

Potential improvements to consider:
- [ ] Streaming support for RLM responses
- [ ] Custom chunking strategies
- [ ] Parallel sub-call optimization
- [ ] Caching for repeated queries
- [ ] Progress callbacks for long-running tasks
- [ ] Integration with job manager for async processing

---

## Future Upgrade Path: True RLM Implementation

### Current State Analysis

Our current implementation provides **"Recursive Processing"** but not the full **"Recursive Language Model"** paradigm as described by Prime Intellect (https://www.primeintellect.ai/blog/rlm).

**What We Have:**
- **SimpleRLMRouter**: Basic chunked recursion (15-30 seconds)
  - Splits text into chunks
  - Processes chunks sequentially
  - Aggregates results
  - Direct MLX access

- **OpenAIRLMRouter**: Uses official RLM library via API (2+ minutes)
  - Can execute Python code
  - Has access to REPL environment
  - But lacks critical RLM features (see below)

### What True RLM Requires

Based on Prime Intellect's implementation, a **complete RLM system** requires:

#### 1. **Persistent Python REPL**
```
Current: Input data loaded into context (causes context rot)
True RLM: Input data lives in Python variables (context stays clean)

Benefits:
- Near-infinite input data (PDFs, datasets, videos)
- No context rot from large inputs
- LLM can inspect/transform data programmatically
```

#### 2. **Sub-LLM Delegation**
```python
# Current: Sequential chunking
for chunk in chunks:
    result = process_chunk(chunk)

# True RLM: Parallel sub-LLM calls
def llm_batch(prompts: List[str]) -> List[str]:
    """Process multiple prompts in parallel"""
    return [sub_llm(p) for p in prompts]

# Example usage:
research_questions = decompose_complex_query(question)
answers = llm_batch(research_questions)  # Parallel!
synthesized = synthesize(answers)
```

**Critical Design Decision:**
- **Tools only available to sub-LLMs** (not main RLM)
- Main model never sees verbose tool outputs
- Avoids context bloat from web scraping, file reading, etc.

#### 3. **Answer via Environment Variable**
```python
# Current: Direct text response
return "The answer is..."

# True RLM: Iterative answer building
answer = {"content": "", "ready": False}

# Model can iteratively refine:
answer["content"] = "Initial thoughts..."
print(answer["content"])  # Check work
answer["content"] = answer["content"].replace("error", "fix")  # Edit
answer["ready"] = True  # Signal completion
```

#### 4. **Context Folding, Not Summarization**
```
Current Approach (Chunking):
  Large doc → Summarize chunks → Aggregate summaries
  Problem: Information loss at each summarization

True RLM (Context Folding):
  Large doc → Delegate to Python/sub-LLMs → No summarization
  Benefit: Zero information loss, near-infinite context
```

### Implementation Roadmap: Option A - True RLM Upgrade

#### Phase 1: Infrastructure (Foundation)
```python
# src/ai_lab/core/rlm/true_rlm_router.py

class TrueRLMRouter:
    """
    Complete RLM implementation per Prime Intellect architecture.

    Key components:
    1. Persistent Python REPL
    2. Sub-LLM delegation with llm_batch()
    3. Answer variable pattern
    4. Context folding (no summarization)
    """

    def __init__(self, model: str):
        self.repl = PersistentPythonREPL()
        self.sub_llm_pool = SubLLMPool()
        self.answer_var = {"content": "", "ready": False}

    def llm_batch(self, prompts: List[str]) -> List[str]:
        """Parallel sub-LLM calls"""
        # Distribute across available models
        # Return aggregated results
        pass
```

**Tasks:**
- [ ] Create `PersistentPythonREPL` class
- [ ] Implement `llm_batch()` parallelization
- [ ] Add answer variable management
- [ ] Design sub-LLM pool architecture

#### Phase 2: Tool Separation
```python
# src/ai_lab/core/rlm/tools.py

class SubLLMTools:
    """
    Tools ONLY available to sub-LLMs, not main RLM.

    This prevents context bloat in main model.
    """

    @sub_llm_only
    def search_web(self, query: str) -> str:
        """Web search - verbose output goes to sub-LLM only"""
        pass

    @sub_llm_only
    def read_file(self, path: str) -> str:
        """File reading - large content stays in sub-LLM"""
        pass

    @sub_llm_only
    def execute_code(self, code: str) -> str:
        """Code execution - results only summarized to main RLM"""
        pass
```

**Tasks:**
- [ ] Implement tool decorators (`@sub_llm_only`)
- [ ] Create tool registry
- [ ] Add tool filtering for main RLM vs sub-LLMs
- [ ] Design result summarization strategy

#### Phase 3: Environment Tips System
```python
# src/ai_lab/core/rlm/env_tips.py

class EnvironmentTips:
    """
    Environment-specific guidance for RLM usage.

    Based on Prime Intellect findings: Tips are CRITICAL for performance.
    """

    TIPS = {
        "deep_research": """
        Strategy for deep research tasks:
        1. Decompose the question into smaller sub-tasks
        2. Use llm_batch() to dispatch in parallel
        3. Synthesize findings from sub-LLM responses
        4. Iterate if needed until sufficient evidence
        """,

        "long_context": """
        Strategy for long-context information retrieval:
        1. Split context into chunks (by paragraphs/windows)
        2. Write prompt for what to look for
        3. Append prompt to each chunk
        4. Call llm_batch() to scan in parallel
        5. Aggregate relevant findings
        """,

        "math_analysis": """
        Strategy for math problems:
        1. Use Python for calculations (numpy, scipy, sympy)
        2. Use llm_batch() for reasoning steps
        3. Validate intermediate results
        4. Check logic before final answer
        """
    }
```

**Tasks:**
- [ ] Create environment tip templates
- [ ] Add tip injection system
- [ ] Implement tip selection logic
- [ ] Design tip customization API

#### Phase 4: Performance Optimizations
```python
# src/ai_lab/core/rlm/optimizations.py

class RLMOptimizations:
    """
    Performance optimizations based on Prime Intellect findings.
    """

    def optimize_sub_llm_calls(self):
        """
        Finding: Models don't always parallelize effectively.
        Solution: Smart batching and load balancing.
        """
        pass

    def cache_repeated_queries(self):
        """
        Finding: Same sub-queries often repeated.
        Solution: Intelligent caching with TTL.
        """
        pass

    def estimate_token_usage(self):
        """
        Finding: Token costs hard to predict.
        Solution: Pre-flight estimation and budgeting.
        """
        pass
```

**Tasks:**
- [ ] Implement smart batching
- [ ] Add query caching
- [ ] Build token estimation
- [ ] Create cost prediction API

#### Phase 5: Training Integration
```python
# src/ai_lab/core/rlm/training.py

class RLMTraining:
    """
    Training models to use RLM effectively.

    Key Finding: Current models NOT trained to use RLM scaffolding.
    Solution: Reinforcement learning on RLM environments.
    """

    def create_rl_dataset(self):
        """
        Generate training data from successful RLM rollouts.
        """
        pass

    def fine_tune_for_rlm(self):
        """
        Fine-tune models to:
        - Use llm_batch() effectively
        - Delegate to sub-LLMs appropriately
        - Manage context folding
        - Use environment tips
        """
        pass
```

**Tasks:**
- [ ] Design RL environment for RLM usage
- [ ] Create reward functions
- [ ] Collect training data from rollouts
- [ ] Implement fine-tuning pipeline

### Expected Performance Improvements

Based on Prime Intellect's experimental results:

| Metric | Current RLM | True RLM (Expected) |
|--------|------------|---------------------|
| **Main Model Tokens** | High | **2-10x reduction** |
| **Context Window** | ~100K chars | **Near-infinite** |
| **Parallelization** | Sequential | **Parallel sub-LLMs** |
| **Tool Usage** | Main model sees all | **Sub-LLMs only (cleaner context)** |
| **Information Loss** | Summarization loss | **Zero loss (context folding)** |
| **Speed** | 15-180s | **Similar or faster** (parallelization) |
| **Training Required** | None (zero-shot) | **RL training for optimal use** |

### Critical Design Decisions

#### 1. **Tools for Sub-LLMs Only**
```python
# WHY: Prevent context bloat in main RLM
# Tools produce verbose output (web pages, files, etc.)
# Only sub-LLMs see this, main RLM gets summaries

@sub_llm_only
def web_search(query):
    # Returns 10K tokens of web content
    # Only sub-LLM sees this
    # Main RLM gets 100-token summary
    pass
```

#### 2. **Environment Tips Are Critical**
```python
# FINDING: RLM fails without proper guidance
# SOLUTION: Provide environment-specific tips

# Without tips: Poor performance
rlm.complete(prompt, root_prompt="Analyze")

# With tips: Huge performance boost
rlm.complete(
    prompt,
    root_prompt="Analyze",
    env_tip="Use llm_batch() to parallelize analysis"
)
```

#### 3. **Training Required**
```
Current State: Zero-shot (models not trained for RLM)
Future State: RL-trained models (optimal RLM usage)

Training Focus:
- Effective llm_batch() usage
- Proper context folding
- Strategic sub-LLM delegation
- Environment tip following
```

### Migration Path

#### Step 1: Add True RLM Alongside Current (No Breaking Changes)
```python
# New router, existing ones unchanged
from ai_lab.core.rlm import TrueRLMRouter

# User can choose
lab rlm-simple <model>    # Current SimpleRLMRouter
lab rlm-full <model>      # Current OpenAIRLMRouter
lab rlm-true <model>      # NEW: TrueRLMRouter
```

#### Step 2: A/B Testing
```python
# Compare performance on same tasks
simple_result = SimpleRLMRouter("model").complete(prompt)
true_result = TrueRLMRouter("model").complete(prompt)

# Measure:
# - Token usage
# - Execution time
# - Answer quality
# - Context management
```

#### Step 3: Gradual Migration
```python
# Start with use cases that benefit most:
# 1. Deep research (web search heavy)
# 2. Long-context analysis (>100K chars)
# 3. Tasks requiring code execution

# Keep simple RLM for:
# - Basic summarization
# - Quick document processing
# - Simple extraction tasks
```

### Use Case Alignment

#### When to Use True RLM:
- ✅ **Deep Research**: Web searches, multi-source analysis
- ✅ **Long Context**: >100K characters, complex documents
- ✅ **Code Analysis**: Log files, datasets requiring computation
- ✅ **Multi-step Reasoning**: Complex decomposable tasks
- ✅ **Tool-Heavy Tasks**: When tools produce verbose output

#### When Current RLM is Sufficient:
- ✅ **Simple Summarization**: Basic document summarization
- ✅ **Quick Analysis**: Fast turnaround needed
- ✅ **Basic Extraction**: Simple information extraction
- ✅ **Small Context**: <50K characters

#### When to Use Standard Mode:
- ✅ **Chat**: Interactive conversations
- ✅ **Q&A**: Questions within context
- ✅ **Speed Critical**: Fast response required
- ✅ **Simple Tasks**: Single-pass sufficient

### Implementation Priority

**High Priority (Quick Wins):**
1. Add `llm_batch()` for parallel sub-LLM calls
2. Implement tool separation (`@sub_llm_only`)
3. Add environment tips system

**Medium Priority (Core Features):**
4. Create persistent Python REPL
5. Implement answer variable pattern
6. Add context folding logic

**Lower Priority (Advanced):**
7. Training integration
8. Advanced optimizations
9. Custom environment support

### References

- [Prime Intellect RLM Article](https://www.primeintellect.ai/blog/rlm)
- [Original RLM Paper](https://arxiv.org/abs/2512.24601)
- [RLM GitHub](https://github.com/alexzhang13/rlm)
- [Prime Intellect Environments Hub](https://github.com/prime-intellect/verifiers)

## References

- [RLM Paper](https://arxiv.org/abs/2512.24601)
- [RLM GitHub](https://github.com/alexzhang13/rlm)
- [RLM Blog Post](https://alexzhang13.github.io/blog/2025/rlm/)

## Support

For issues or questions:
1. Check this guide's troubleshooting section
2. Review RLM library documentation
3. Check model availability: `lab models list`
4. Verify RLM status: Check `/api/v1/rlm/status`
