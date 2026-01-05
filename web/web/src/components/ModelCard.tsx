import type { Model } from '../types/api'

interface ModelCardProps {
  model: Model
  onSelect?: (model: Model) => void
}

export function ModelCard({ model, onSelect }: ModelCardProps) {
  const typeColors = {
    base: 'bg-blue-100 text-blue-800',
    adapter: 'bg-purple-100 text-purple-800',
  }

  const backendColors = {
    mlx: 'bg-green-100 text-green-800',
    default: 'bg-gray-100 text-gray-800',
  }

  return (
    <div
      className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer"
      onClick={() => onSelect?.(model)}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{model.name}</h3>
          {model.description && (
            <p className="text-sm text-gray-600 mt-1">{model.description}</p>
          )}
        </div>
        <span
          className={`px-2 py-1 rounded text-xs font-medium ml-2 ${
            typeColors[model.type] || 'bg-gray-100 text-gray-800'
          }`}
        >
          {model.type}
        </span>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex items-center justify-between">
          <span className="text-gray-600">Backend:</span>
          <span
            className={`px-2 py-0.5 rounded text-xs font-medium ${
              backendColors[model.backend as keyof typeof backendColors] || backendColors.default
            }`}
          >
            {model.backend}
          </span>
        </div>

        {model.parameters && (
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Parameters:</span>
            <span className="text-gray-900 font-medium">{model.parameters}</span>
          </div>
        )}

        {model.size_gb && (
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Size:</span>
            <span className="text-gray-900 font-medium">{model.size_gb} GB</span>
          </div>
        )}

        {model.parent && (
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Parent Model:</span>
            <span className="text-gray-900 font-medium text-xs">{model.parent}</span>
          </div>
        )}

        {model.chat_template && (
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Chat Template:</span>
            <span className="text-gray-900 font-medium">{model.chat_template}</span>
          </div>
        )}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500 font-mono truncate" title={model.path}>
          {model.path}
        </p>
      </div>
    </div>
  )
}
