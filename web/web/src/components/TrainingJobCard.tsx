import type { TrainingJob } from '../types/api'

interface TrainingJobCardProps {
  job: TrainingJob
  onClick?: () => void
}

export function TrainingJobCard({ job, onClick }: TrainingJobCardProps) {
  // Status styling
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'running':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        )
      case 'running':
        return (
          <svg className="w-5 h-5 animate-spin" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"
              clipRule="evenodd"
            />
          </svg>
        )
      case 'failed':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
        )
      case 'pending':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
              clipRule="evenodd"
            />
          </svg>
        )
      default:
        return null
    }
  }

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleString()
  }

  // Calculate duration
  const getDuration = () => {
    if (!job.started_at) return null

    const start = new Date(job.started_at)
    const end = job.completed_at ? new Date(job.completed_at) : new Date()
    const durationMs = end.getTime() - start.getTime()

    const minutes = Math.floor(durationMs / 60000)
    const seconds = Math.floor((durationMs % 60000) / 1000)

    if (minutes > 0) {
      return `${minutes}m ${seconds}s`
    }
    return `${seconds}s`
  }

  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-lg shadow-md border-2 p-6 transition-all ${
        onClick ? 'hover:shadow-lg cursor-pointer hover:border-blue-400' : ''
      } ${getStatusColor(job.status).split(' ')[2]}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            {job.config.output_name}
          </h3>
          <p className="text-sm text-gray-600">Base: {job.config.base_model}</p>
        </div>
        <div className={`flex items-center space-x-2 px-3 py-1 rounded-full border ${getStatusColor(job.status)}`}>
          {getStatusIcon(job.status)}
          <span className="text-sm font-medium capitalize">{job.status}</span>
        </div>
      </div>

      {/* Progress Bar */}
      {job.status === 'running' && (
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Progress</span>
            <span>{Math.round(job.progress * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${job.progress * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Error Message */}
      {job.error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800 font-medium">Error:</p>
          <p className="text-sm text-red-700 mt-1">{job.error}</p>
        </div>
      )}

      {/* Training Configuration */}
      <div className="grid grid-cols-2 gap-3 mb-4 p-3 bg-gray-50 rounded-lg">
        <div>
          <p className="text-xs text-gray-500">Epochs</p>
          <p className="text-sm font-medium text-gray-900">{job.config.epochs}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Batch Size</p>
          <p className="text-sm font-medium text-gray-900">{job.config.batch_size}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">LoRA Rank</p>
          <p className="text-sm font-medium text-gray-900">{job.config.lora_rank}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Learning Rate</p>
          <p className="text-sm font-medium text-gray-900">{job.config.learning_rate}</p>
        </div>
      </div>

      {/* Timestamps */}
      <div className="text-xs text-gray-500 space-y-1">
        <div className="flex justify-between">
          <span>Created:</span>
          <span>{formatTimestamp(job.created_at)}</span>
        </div>
        {job.started_at && (
          <div className="flex justify-between">
            <span>Started:</span>
            <span>{formatTimestamp(job.started_at)}</span>
          </div>
        )}
        {job.completed_at && (
          <div className="flex justify-between">
            <span>Completed:</span>
            <span>{formatTimestamp(job.completed_at)}</span>
          </div>
        )}
        {getDuration() && (
          <div className="flex justify-between font-medium text-gray-700">
            <span>Duration:</span>
            <span>{getDuration()}</span>
          </div>
        )}
      </div>

      {/* Result (if completed) */}
      {job.result && job.status === 'completed' && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500 mb-1">Output Path:</p>
          <p className="text-sm text-gray-900 font-mono bg-gray-50 p-2 rounded truncate">
            {job.result.output_path}
          </p>
        </div>
      )}
    </div>
  )
}
