import { useEffect, useState } from 'react'
import { modelsApi } from '../lib/api'
import type { Model } from '../types/api'

interface ModelSelectorProps {
  selectedModel: string | null
  onModelChange: (modelId: string) => void
}

export function ModelSelector({ selectedModel, onModelChange }: ModelSelectorProps) {
  const [models, setModels] = useState<Model[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadModels()
  }, [])

  const loadModels = async () => {
    try {
      setLoading(true)
      const response = await modelsApi.list()
      const modelsWithId = (response.data || []).map((model: Model) => ({
        ...model,
        id: model.name,
      }))
      setModels(modelsWithId)

      // Auto-select first model if none selected
      if (!selectedModel && modelsWithId.length > 0) {
        onModelChange(modelsWithId[0].name)
      }
    } catch (err) {
      console.error('Failed to load models:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (modelName: string) => {
    if (!confirm(`Are you sure you want to delete "${modelName}"? This will remove it from the registry but keep the files on disk.`)) {
      return
    }

    try {
      await modelsApi.delete(modelName)
      // Reload models after deletion
      await loadModels()
      // If deleted model was selected, clear selection
      if (selectedModel === modelName) {
        const remaining = models.filter(m => m.name !== modelName)
        if (remaining.length > 0) {
          onModelChange(remaining[0].name)
        }
      }
    } catch (err) {
      alert(`Failed to delete model: ${err instanceof Error ? err.message : 'Unknown error'}`)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center space-x-2">
        <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <span className="text-gray-600">Loading models...</span>
      </div>
    )
  }

  if (models.length === 0) {
    return (
      <div className="text-red-600">
        No models available. Please download a model first.
      </div>
    )
  }

  // Group models by type
  const baseModels = models.filter((m) => m.type === 'base')
  const adapterModels = models.filter((m) => m.type === 'adapter')

  // Check if selected model is an adapter
  const selectedModelObj = models.find((m) => m.name === selectedModel)
  const canDelete = selectedModelObj?.type === 'adapter'

  return (
    <div className="flex items-center space-x-3">
      <label htmlFor="model-select" className="text-sm font-medium text-gray-700">
        Model:
      </label>
      <select
        id="model-select"
        value={selectedModel || ''}
        onChange={(e) => onModelChange(e.target.value)}
        className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
      >
        {baseModels.length > 0 && (
          <optgroup label="Base Models">
            {baseModels.map((model) => (
              <option key={model.name} value={model.name}>
                {model.name}
              </option>
            ))}
          </optgroup>
        )}
        {adapterModels.length > 0 && (
          <optgroup label="Fine-tuned Models (LoRA)">
            {adapterModels.map((model) => (
              <option key={model.name} value={model.name}>
                {model.name} {model.parent && `(based on ${model.parent})`}
              </option>
            ))}
          </optgroup>
        )}
      </select>
      {canDelete && selectedModel && (
        <button
          onClick={() => handleDelete(selectedModel)}
          className="px-3 py-2 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors border border-red-200 hover:border-red-300"
          title="Delete this adapter"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
        </button>
      )}
    </div>
  )
}
