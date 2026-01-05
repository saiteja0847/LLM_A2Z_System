// System types
export interface HealthResponse {
  status: string
  version: string
  mlx_available: boolean
}

export interface SystemInfo {
  version: string
  platform: string
  mlx_version?: string
  available_backends: string[]
}

// Model types
export interface Model {
  name: string
  description?: string
  backend: string
  type: 'base' | 'adapter'
  status: 'ready' | 'downloading' | 'error'
  quantization?: string
  size_gb?: number
  estimated_memory_gb?: number | null
  context_length?: number
  path: string
  tags?: string[]
  parent?: string
  chat_template?: string
  parameters?: string
  // Computed property for compatibility
  id?: string
}

// Chat types
export interface ChatMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export interface ChatCompletionResponse {
  model: string
  content: string
  usage?: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
}

// Training types
export interface TrainingJob {
  id: string
  type: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  config: {
    base_model: string
    output_name: string
    dataset_path: string
    epochs: number
    batch_size: number
    lora_rank: number
    lora_layers: number
    learning_rate: number
  }
  created_at: string
  started_at?: string
  completed_at?: string
  progress: number
  error?: string
  result?: {
    output_path: string
    base_model: string
    epochs: number
  }
}

export interface TrainingConfig {
  epochs?: number
  batchSize?: number
  loraRank?: number
  loraLayers?: number
  learningRate?: number
}

// OpenAI-compatible types
export interface OpenAIModel {
  id: string
  object: 'model'
  created: number
  owned_by: string
}

export interface OpenAIChatResponse {
  id: string
  object: 'chat.completion'
  created: number
  model: string
  choices: Array<{
    index: number
    message: ChatMessage
    finish_reason: string
  }>
  usage: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
}
