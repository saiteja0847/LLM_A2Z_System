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
  id: string
  name: string
  type: 'base' | 'adapter'
  backend: string
  path: string
  parent?: string
  chat_template?: string
  size_gb?: number
  parameters?: string
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
  status: 'pending' | 'running' | 'completed' | 'failed'
  base_model: string
  output_name: string
  progress: number
  logs: string[]
  created_at: string
  started_at?: string
  completed_at?: string
  error?: string
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
