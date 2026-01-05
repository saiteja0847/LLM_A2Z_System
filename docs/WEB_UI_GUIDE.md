# Web UI Guide

## Overview

The AI Lab platform provides a modern React-based web interface for managing models, training, optimization, and RLM features. Built with TypeScript, Tailwind CSS, and Vite.

## Accessing the Web UI

### Start the Platform

```bash
# Start both backend and frontend
./start.sh

# Or start individually:
# Backend (FastAPI)
python3 -m uvicorn src.ai_lab.api.app:app --host 0.0.0.0 --port 8000

# Frontend (React)
cd web/web && npm run dev
```

### Open in Browser

```
Frontend: http://localhost:5173
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
```

---

## Pages Overview

### 1. Home Page

**URL:** `http://localhost:5173/`

**Features:**
- System status dashboard
- Quick stats (models loaded, active jobs)
- Navigation to all features
- API health check indicator

**Components:**
- `SystemStatus` — Real-time health monitoring
- Navigation sidebar
- Welcome banner

---

### 2. Models Page

**URL:** `http://localhost:5173/models`

**Features:**
- List all registered models
- View model details (size, context, backend)
- Download new models from HuggingFace
- Delete models (with confirmation)

#### Model List

- **Grid Layout:** Card-based display
- **Model Card Shows:**
  - Model name and type
  - Backend icon (MLX, GGUF, Ollama)
  - Size and context window
  - Memory requirement
  - Delete button (adapters only)

#### Download Model

Click "Download Model" button:

- **HuggingFace Model ID:** `mlx-community/Qwen3-4B-Instruct-4bit`
- **Model Name:** Auto-generated or custom
- **Progress Bar:** Real-time download progress
- **Time Estimate:** ETA for completion

**Example Download:**
```
Model ID: mlx-community/Qwen3-4B-Instruct-4bit
Name: qwen3-4b-instruct
Progress: 45% (1.8 GB / 4.0 GB)
Speed: 25 MB/s
ETA: 1 min 32 sec
```

#### Model Details Modal

Click any model card to view:

- Full configuration
- Parameters (context, quantization)
- File path
- Memory estimation
- Metadata

---

### 3. Chat Page

**URL:** `http://localhost:5173/chat`

**Features:**
- Interactive chat interface
- Model selection dropdown
- Temperature and max tokens controls
- Markdown rendering for responses
- Character count and statistics

#### Chat Interface

**Components:**

1. **Model Selector** (`ModelSelector`)
   - Dropdown with all registered models
   - Shows model type (base/adapter)
   - Delete button for adapters
   - Auto-refreshes after training

2. **Chat Controls** (`ChatControls`)
   - Temperature slider (0.0 - 2.0)
   - Max tokens slider (100 - 8000)
   - Reset to defaults button

3. **Message Display** (`Message`)
   - User messages (right-aligned, blue)
   - Assistant messages (left-aligned, gray)
   - Markdown rendering (code blocks, lists, headers)
   - Copy button for code blocks

4. **Input Area**
   - Large text area for prompts
   - Send button (or Cmd+Enter)
   - Character count
   - Clear conversation button

**Example Chat Flow:**
```
User: Explain quantum computing in simple terms

Assistant: Quantum computing is like having a magical coin...
[markdown rendered with proper formatting]

User: Can you give an example?

Assistant: Sure! Imagine you're lost in a maze...
```

**Features:**
- Streaming responses (tokens appear in real-time)
- Error handling with user-friendly messages
- First-load info banner (20-30s model loading)
- Auto-scroll to latest message

---

### 4. Training Page

**URL:** `http://localhost:5173/training`

**Features:**
- Create training jobs
- Monitor training progress
- View training history
- Analyze training curves

#### Training Form (`TrainingForm`)

**Input Fields:**

1. **Base Model**
   - Dropdown selection
   - Only base models (not adapters)

2. **Dataset Upload**
   - File input (JSONL format)
   - Dataset preview
   - Validation dataset (optional)

3. **Output Name**
   - Text input for adapter name
   - Auto-suggestions based on dataset

4. **Training Parameters**
   - **Epochs:** 1-10 (default: 3)
   - **Batch Size:** 1-8 (default: 4)
   - **Learning Rate:** 1e-5 to 1e-3 (default: 1e-4)
   - **LoRA Rank:** 4, 8, 16, 32 (default: 8)
   - **LoRA Alpha:** 8, 16, 32, 64 (default: 16)
   - **Dropout:** 0.0 - 0.2 (default: 0.0)

5. **Advanced Options**
   - Gradient checkpointing toggle
   - Max sequence length
   - Validation frequency
   - Max memory limit

**Start Training:**
- Validates all inputs
- Checks dataset format
- Estimates memory usage
- Shows warning if insufficient memory
- Starts job in background

#### Training Job List (`TrainingJobList`)

- **Card-based layout** for each job
- **Job status badges:**
  - 🟡 Queued
  - 🔵 Training
  - ✅ Completed
  - ❌ Failed

**Job Card Shows:**
- Job ID
- Model and adapter name
- Status and progress
- Start time and duration
- Current epoch/step
- Loss metrics (train/val)

#### Training Job Details (`TrainingJobDetails`)

Click a job card to expand:

**Progress Section:**
- Progress bar (0-100%)
- Current epoch (X/Y)
- Current step (X/Y)
- ETA calculation

**Metrics Section:**
- Training loss curve (live plot)
- Validation loss curve (live plot)
- Current values displayed
- Best epoch marked

**Logs Section:**
- Live log streaming
- Color-coded by level (info, warning, error)
- Auto-scroll to latest
- Copy logs button

**Actions:**
- "Stop Training" button (with confirmation)
- "Download Adapter" button (when complete)
- "Use in Chat" button (redirects to chat page)

---

### 5. Optimization Page

**URL:** `http://localhost:5173/optimization`

**Features:**
- Create optimization jobs
- Monitor parallel trials
- View convergence plots
- Compare configurations

#### Optimization Interface (`OptimizationInterface`)

**Setup Section:**

1. **Model Selection**
   - Dropdown of base models

2. **Dataset Upload**
   - JSONL file input

3. **Search Space Configuration**
   - Add parameter button
   - Parameter types:
     - Range (min, max, log scale)
     - Choice (list of values)
     - Fixed (constant value)

4. **Parameter Cards**
   - Learning rate: range [1e-5, 1e-3], log scale
   - LoRA rank: choice [4, 8, 16, 32]
   - Batch size: choice [2, 4, 8]
   - LoRA dropout: range [0.0, 0.1]

5. **Experiment Settings**
   - Max trials: 10-100 (default: 20)
   - Parallel jobs: 1-4 (default: 2)
   - Objective metric: val_loss (default)
   - Direction: minimize/maximize

**Start Optimization:**
- Validates search space
- Estimates total time
- Shows memory warning if needed
- Starts Ax optimizer

#### Progress Monitoring

**Trials Table:**
- Trial number
- Parameter values
- Objective value
- Status (running, completed, failed)
- Duration

**Best Trial Highlight:**
- ⭐ marker for best configuration
- Bold text
- Green background

**Convergence Plot:**
- X-axis: Trial number
- Y-axis: Objective value
- Best trial marked
- Running average line
- Interactive tooltips

**Parallel Jobs Display:**
- Number of active trials
- Progress bars for each
- Total progress (X/Y trials)

#### Results Section

**After Completion:**

1. **Best Configuration**
   - Parameter values
   - Objective score
   - Trial number

2. **Comparison Table**
   - Sortable by column
   - Filter by status
   - Export to CSV

3. **Convergence Analysis**
   - Plot of objective over time
   - Improvement percentage
   - Convergence detection

4. **Actions**
   - "Train with Best Config" button
   - Export results JSON
   - Copy best config to clipboard

---

### 6. RLM Page

**URL:** `http://localhost:5173/rlm`

**Features:**
- Simple RLM (fast recursive processing)
- Full RLM (with code execution)
- Mode switcher
- Configuration options

#### RLM Interface (`RLMInterface`)

**Mode Selector:**

1. **Simple RLM** (Blue theme)
   - Fast recursive chunking
   - Direct MLX access
   - 15-30 seconds for documents
   - No code execution

2. **Full RLM** (Purple theme)
   - Complete RLM library
   - Python code execution
   - 2+ minutes for complex tasks
   - Tool support

**Input Section:**

1. **Model Selector**
   - All registered models
   - RLM-compatible indicator

2. **Root Prompt**
   - Large text area
   - Task instructions
   - Examples:
     - "Summarize this document"
     - "Extract key insights"
     - "Analyze the data"

3. **Document/Prompt**
   - Large text area for content
   - Character count (up to 1M+)
   - Paste large documents

4. **Configuration**
   - Max context: 1000 - 32000 tokens
   - Chunk size: 500 - 8000 tokens
   - Max iterations: 1 - 20 (Full RLM only)
   - Tools: Python, calculator (Full RLM only)

**Execute RLM:**

**Simple RLM Flow:**
```
1. Validate inputs
2. Split document into chunks
3. Process each chunk recursively
4. Combine results
5. Return final answer (15-30s)
```

**Full RLM Flow:**
```
1. Initialize RLM environment
2. Create recursive processing tree
3. Execute sub-tasks with tools
4. Aggregate results
5. Return final answer (2+ min)
```

**Results Display:**
- Final answer in large text area
- Processing statistics:
  - Chunks processed
  - Total tokens
  - Processing time
  - Tools used (Full RLM)
- Copy to clipboard button

---

## UI Components Reference

### SystemStatus

```typescript
<SystemStatus />
```

**Displays:**
- API status (healthy/unhealthy)
- Platform info (macOS, Apple Silicon)
- Memory usage
- Models loaded
- Active jobs

### ModelCard

```typescript
<ModelCard
  model={{
    name: "qwen3-4b-instruct",
    type: "base",
    backend: "mlx",
    size_gb: 4.0,
    context_length: 250000
  }}
  onDelete={handleDelete}
/>
```

### ChatInterface

```typescript
<ChatInterface
  models={models}
  selectedModel={selectedModel}
  onModelChange={setSelectedModel}
/>
```

### TrainingForm

```typescript
<TrainingForm
  models={models}
  onSubmit={startTraining}
/>
```

### OptimizationInterface

```typescript
<OptimizationInterface
  models={models}
  onStart={startOptimization}
/>
```

### RLMInterface

```typescript
<RLMInterface
  models={models}
  mode="simple"  // or "full"
/>
```

---

## Styling Guide

### Tailwind CSS

The UI uses Tailwind CSS v3 with custom configuration:

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: '#3b82f6',    // Blue
        secondary: '#8b5cf6',  // Purple
        success: '#10b981',    // Green
        danger: '#ef4444',     // Red
      }
    }
  }
}
```

### Color Schemes

- **Blue:** Chat, Simple RLM
- **Purple:** Full RLM
- **Green:** Success states
- **Red:** Error states
- **Gray:** Neutral UI elements

### Dark Mode

Currently, the UI uses a dark theme by default. To add light mode support:

```typescript
// Add to tailwind.config.js
darkMode: 'class',

// Use in components:
<div className="bg-white dark:bg-gray-800">
```

---

## Best Practices

### 1. Responsive Design

All pages are mobile-responsive:

```typescript
// Use Tailwind responsive classes
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
```

### 2. Error Handling

Always show user-friendly errors:

```typescript
try {
  await api.chat.completions.create({...});
} catch (error) {
  setError(
    error.response?.data?.detail ||
    "Failed to send message. Please try again."
  );
}
```

### 3. Loading States

Show loading indicators for async operations:

```typescript
{loading ? (
  <Spinner />
) : (
  <Content />
)}
```

### 4. Debouncing

Debounce user inputs for API calls:

```typescript
const debouncedSearch = useMemo(
  () => debounce(query => searchModels(query), 300),
  []
);
```

---

## Troubleshooting

### Frontend Not Starting

```bash
# Error: Port 5173 already in use
# Solution:
lsof -ti:5173 | xargs kill -9

# Or use different port:
npm run dev -- --port 5174
```

### API Connection Errors

```bash
# Error: Failed to fetch
# Check:
1. Backend is running (http://localhost:8000/health)
2. CORS is enabled in backend
3. No firewall blocking connections
```

### Page Not Updating

```bash
# Solution: Hard refresh
# Mac: Cmd+Shift+R
# Windows: Ctrl+Shift+R

# Or clear cache:
rm -rf node_modules/.vite
npm run dev
```

### Build Errors

```bash
# Error: TypeScript errors
# Solution:
npm run build  # Check build output
# Fix type errors in .tsx files

# Common issues:
# - Missing props in components
# - Incorrect types in API calls
# - Missing imports
```

---

## Development

### Project Structure

```
web/web/src/
├── components/          # React components
│   ├── ChatInterface.tsx
│   ├── ModelCard.tsx
│   ├── TrainingForm.tsx
│   └── ...
├── lib/
│   └── api.ts          # API client
├── types/
│   └── api.ts          # TypeScript types
├── App.tsx             # Main app
└── main.tsx            # Entry point
```

### Adding New Pages

1. Create component in `src/components/`
2. Add route in `App.tsx`
3. Add navigation link
4. Update API client if needed

### Adding New API Methods

```typescript
// src/lib/api.ts
export const myNewApi = {
  action: async (params: MyParams) => {
    const response = await api.post('/api/endpoint', params);
    return response.data;
  }
};
```

---

## See Also

- [Model Management](MODEL_MANAGEMENT.md) — Model backend details
- [Training Guide](TRAINING_GUIDE.md) — Training concepts
- [Optimization Guide](OPTIMIZATION_GUIDE.md) — Optimization concepts
- [API Reference](API_REFERENCE.md) — Backend API documentation
