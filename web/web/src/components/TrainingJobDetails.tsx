import { useState, useEffect } from 'react'
import { trainingApi } from '../lib/api'
import type { TrainingJob } from '../types/api'

interface TrainingJobDetailsProps {
  job: TrainingJob
  onClose: () => void
}

export function TrainingJobDetails({ job, onClose }: TrainingJobDetailsProps) {
  const [logs, setLogs] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentJob, setCurrentJob] = useState(job)

  // Fetch job details and logs
  const fetchJobDetails = async () => {
    try {
      setError(null)

      // Fetch updated job info
      const jobResponse = await trainingApi.getJob(job.id)
      setCurrentJob(jobResponse.data)

      // Fetch logs
      const logsResponse = await trainingApi.getJobLogs(job.id)
      setLogs(logsResponse.data.logs || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch job details')
    } finally {
      setLoading(false)
    }
  }

  // Initial fetch
  useEffect(() => {
    fetchJobDetails()
  }, [job.id])

  // Auto-refresh for running jobs
  useEffect(() => {
    if (currentJob.status !== 'running' && currentJob.status !== 'pending') {
      return
    }

    const interval = setInterval(() => {
      fetchJobDetails()
    }, 2000) // 2 seconds

    return () => clearInterval(interval)
  }, [currentJob.status])

  // Handle escape key to close
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [onClose])

  // Status styling
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'running':
        return 'bg-blue-100 text-blue-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gray-50 border-b border-gray-200 px-6 py-4">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                {currentJob.config.output_name}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Base: {currentJob.config.base_model}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Status Badge */}
          <div className="mt-4">
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(currentJob.status)}`}
            >
              {currentJob.status.toUpperCase()}
            </span>
          </div>

          {/* Progress Bar */}
          {(currentJob.status === 'running' || currentJob.status === 'pending') && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Progress</span>
                <span>{Math.round(currentJob.progress * 100)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${currentJob.progress * 100}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Error Message */}
          {currentJob.error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <h3 className="text-red-800 font-semibold mb-2">Error</h3>
              <p className="text-red-700 text-sm font-mono">{currentJob.error}</p>
            </div>
          )}

          {/* Training Configuration */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Training Configuration</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm text-gray-500">Epochs</p>
                <p className="text-lg font-semibold text-gray-900">{currentJob.config.epochs}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Batch Size</p>
                <p className="text-lg font-semibold text-gray-900">{currentJob.config.batch_size}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">LoRA Rank</p>
                <p className="text-lg font-semibold text-gray-900">{currentJob.config.lora_rank}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">LoRA Layers</p>
                <p className="text-lg font-semibold text-gray-900">{currentJob.config.lora_layers}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Learning Rate</p>
                <p className="text-lg font-semibold text-gray-900">{currentJob.config.learning_rate}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Dataset</p>
                <p className="text-sm font-mono text-gray-900 truncate">
                  {currentJob.config.dataset_path.split('/').pop()}
                </p>
              </div>
            </div>
          </div>

          {/* Result (if completed) */}
          {currentJob.result && currentJob.status === 'completed' && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Result</h3>
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Output Path:</p>
                <p className="text-sm font-mono text-gray-900 bg-white p-2 rounded">
                  {currentJob.result.output_path}
                </p>
              </div>
            </div>
          )}

          {/* Training Logs */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-900">Training Logs</h3>
              {(currentJob.status === 'running' || currentJob.status === 'pending') && (
                <span className="text-sm text-gray-500 italic">Auto-refreshing...</span>
              )}
            </div>

            {loading && logs.length === 0 ? (
              <div className="text-center py-8 text-gray-500">Loading logs...</div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
                {error}
              </div>
            ) : logs.length === 0 ? (
              <div className="text-center py-8 text-gray-500">No logs yet</div>
            ) : (
              <div className="bg-gray-900 text-gray-100 rounded-lg p-4 font-mono text-sm max-h-96 overflow-y-auto">
                {logs.map((log, idx) => (
                  <div key={idx} className="mb-1">
                    {log}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Timestamps */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Timeline</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Created:</span>
                <span className="text-gray-900">{new Date(currentJob.created_at).toLocaleString()}</span>
              </div>
              {currentJob.started_at && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Started:</span>
                  <span className="text-gray-900">{new Date(currentJob.started_at).toLocaleString()}</span>
                </div>
              )}
              {currentJob.completed_at && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Completed:</span>
                  <span className="text-gray-900">{new Date(currentJob.completed_at).toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-gray-50 border-t border-gray-200 px-6 py-4">
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
