import { useEffect, useState } from 'react'
import { modelsApi } from '../lib/api'
import type { Model } from '../types/api'
import { ModelCard } from './ModelCard'

export function ModelList() {
  const [models, setModels] = useState<Model[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedModel, setSelectedModel] = useState<Model | null>(null)

  useEffect(() => {
    loadModels()
  }, [])

  const loadModels = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await modelsApi.list()
      // API returns array directly, add id field for compatibility
      const modelsWithId = (response.data || []).map((model: Model) => ({
        ...model,
        id: model.name,
      }))
      setModels(modelsWithId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load models')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading models...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-red-900 font-semibold mb-2">Failed to load models</h3>
        <p className="text-red-700 text-sm">{error}</p>
        <button
          onClick={loadModels}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    )
  }

  if (models.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
        <h3 className="text-yellow-900 font-semibold mb-2">No models found</h3>
        <p className="text-yellow-700 text-sm">
          Download a model from HuggingFace to get started
        </p>
      </div>
    )
  }

  // Separate base models and adapters
  const baseModels = models.filter((m) => m.type === 'base')
  const adapterModels = models.filter((m) => m.type === 'adapter')

  return (
    <div className="space-y-8">
      {/* Base Models */}
      {baseModels.length > 0 && (
        <div>
          <h3 className="text-xl font-semibold text-gray-900 mb-4">
            Base Models ({baseModels.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {baseModels.map((model) => (
              <ModelCard
                key={model.id}
                model={model}
                onSelect={setSelectedModel}
              />
            ))}
          </div>
        </div>
      )}

      {/* Adapter Models */}
      {adapterModels.length > 0 && (
        <div>
          <h3 className="text-xl font-semibold text-gray-900 mb-4">
            Fine-tuned Models ({adapterModels.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {adapterModels.map((model) => (
              <ModelCard
                key={model.id}
                model={model}
                onSelect={setSelectedModel}
              />
            ))}
          </div>
        </div>
      )}

      {/* Model Details Modal */}
      {selectedModel && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedModel(null)}
        >
          <div
            className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-2xl font-bold text-gray-900">
                {selectedModel.name}
              </h2>
              <button
                onClick={() => setSelectedModel(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-sm font-semibold text-gray-600">ID</label>
                <p className="text-gray-900 font-mono text-sm">{selectedModel.id}</p>
              </div>
              <div>
                <label className="text-sm font-semibold text-gray-600">Type</label>
                <p className="text-gray-900">{selectedModel.type}</p>
              </div>
              <div>
                <label className="text-sm font-semibold text-gray-600">Backend</label>
                <p className="text-gray-900">{selectedModel.backend}</p>
              </div>
              <div>
                <label className="text-sm font-semibold text-gray-600">Path</label>
                <p className="text-gray-900 font-mono text-sm break-all">
                  {selectedModel.path}
                </p>
              </div>
              {selectedModel.parameters && (
                <div>
                  <label className="text-sm font-semibold text-gray-600">Parameters</label>
                  <p className="text-gray-900">{selectedModel.parameters}</p>
                </div>
              )}
              {selectedModel.size_gb && (
                <div>
                  <label className="text-sm font-semibold text-gray-600">Size</label>
                  <p className="text-gray-900">{selectedModel.size_gb} GB</p>
                </div>
              )}
              {selectedModel.parent && (
                <div>
                  <label className="text-sm font-semibold text-gray-600">Parent Model</label>
                  <p className="text-gray-900">{selectedModel.parent}</p>
                </div>
              )}
              {selectedModel.chat_template && (
                <div>
                  <label className="text-sm font-semibold text-gray-600">Chat Template</label>
                  <p className="text-gray-900">{selectedModel.chat_template}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
