import { useState, useEffect, useRef } from 'react'
import { API_BASE_URL } from '../lib/api'

interface OptimizationConfig {
  base_model: string
  dataset_path: string
  num_trials: number
  experiment_epochs: number
  experiment_name: string
  [key: string]: string | number  // Allow additional properties
}

interface OptimizationJob {
  id: string
  type: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  config: OptimizationConfig
  created_at: string
  started_at?: string
  completed_at?: string
  progress: number
  error?: string
  result?: {
    best_parameters: Record<string, string | number>
    parameter_importance: Record<string, number>
  }
}

interface Model {
  name: string
  size_gb?: number
  estimated_memory_gb?: number
  status: string
  type: string
  backend: string
}

export function OptimizationInterface() {
  const [jobs, setJobs] = useState<OptimizationJob[]>([])
  const [selectedJob, setSelectedJob] = useState<OptimizationJob | null>(null)

  // Form state
  const [modelName, setModelName] = useState('')
  const [datasetPath, setDatasetPath] = useState('')
  const [numTrials, setNumTrials] = useState(20)
  const [experimentEpochs, setExperimentEpochs] = useState(1)
  const [experimentName, setExperimentName] = useState('lora_optimization')

  // UI state
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [models, setModels] = useState<Model[]>([])
  const [modelsLoading, setModelsLoading] = useState(true)

  // Store polling intervals for cleanup
  const pollingIntervals = useRef<Set<number>>(new Set())

  const API_BASE = `${API_BASE_URL}/api/optimization`

  // Fetch available models on mount
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/models/`)
        if (response.ok) {
          const modelsData = await response.json()
          // Filter to only show base models (not fine-tuned)
          const baseModels = (modelsData || []).filter((m: Model) => m.type === 'base')
          setModels(baseModels)
          // Auto-select first model if none selected
          if (!modelName && baseModels && baseModels.length > 0) {
            setModelName(baseModels[0].name)
          }
        } else {
          setError('Failed to fetch available models')
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to connect to API'
        setError(`Failed to fetch models: ${errorMessage}`)
      } finally {
        setModelsLoading(false)
      }
    }
    fetchModels()
  }, [modelName])

  // Cleanup all polling intervals on unmount
  useEffect(() => {
    return () => {
      // Clear all active polling intervals
      pollingIntervals.current.forEach(interval => clearInterval(interval))
      pollingIntervals.current.clear()
    }
  }, [])

  const refreshJobs = async () => {
    try {
      const response = await fetch(`${API_BASE}/list`)
      if (response.ok) {
        const data = await response.json()
        setJobs(data)
      } else {
        setError('Failed to fetch optimization jobs')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to connect to API'
      setError(`Failed to fetch jobs: ${errorMessage}`)
    }
  }

  // Fetch jobs on component mount
  useEffect(() => {
    refreshJobs()
  }, [])

  const startOptimization = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          base_model: modelName,
          dataset_path: datasetPath,
          num_trials: numTrials,
          experiment_epochs: experimentEpochs,
          experiment_name: experimentName,
        }),
      })

      if (response.ok) {
        const job = await response.json()
        setSelectedJob(job)
        // Start polling for updates
        pollJobStatus(job.id)
      } else {
        const err = await response.json()
        setError(err.detail || 'Failed to start optimization')
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to connect to API'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const pollJobStatus = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE}/${jobId}`)
        if (response.ok) {
          const job: OptimizationJob = await response.json()
          setSelectedJob(job)

          if (job.status === 'completed' || job.status === 'failed') {
            clearInterval(interval)
            pollingIntervals.current.delete(interval)
            refreshJobs()
          }
        }
      } catch (err) {
        // Silently log polling errors to avoid overwhelming the user
        console.error('Polling error:', err instanceof Error ? err.message : err)
      }
    }, 2000)

    // Store interval for cleanup
    pollingIntervals.current.add(interval)
  }

  const viewJobDetails = async (jobId: string) => {
    try {
      const response = await fetch(`${API_BASE}/${jobId}`)
      if (response.ok) {
        const job: OptimizationJob = await response.json()
        setSelectedJob(job)
      } else {
        setError('Failed to fetch job details')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to connect to API'
      setError(`Failed to fetch job: ${errorMessage}`)
    }
  }

  const getJobStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      running: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const formatParameter = (key: string, value: string | number): string => {
    if (typeof value === 'number') {
      if (key.includes('rate') || key.includes('ratio')) {
        return value.toFixed(6)
      }
      return value.toString()
    }
    return value
  }

  return (
    <div className="space-y-6">
      {/* Start Optimization Form */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Start Hyperparameter Optimization</h3>

        <form onSubmit={startOptimization} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Base Model
              </label>
              {modelsLoading ? (
                <div className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500">
                  Loading models...
                </div>
              ) : (
                <select
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Select a model...</option>
                  {models.map((model) => (
                    <option key={model.name} value={model.name}>
                      {model.name}
                      {model.estimated_memory_gb
                        ? ` (~${model.estimated_memory_gb.toFixed(1)}GB)`
                        : model.size_gb
                        ? ` (${model.size_gb.toFixed(1)}GB)`
                        : ''}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dataset File
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={datasetPath}
                  onChange={(e) => setDatasetPath(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="data.jsonl or /path/to/data.jsonl"
                  required
                />
                <label className="px-4 py-2 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-md cursor-pointer transition-colors">
                  Browse
                  <input
                    type="file"
                    accept=".jsonl,.json"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (file) {
                        // For local files, use just the filename
                        // Files should be placed in project root or uploads directory
                        setDatasetPath(file.name)
                      }
                    }}
                  />
                </label>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Select a .jsonl or .json file from your project directory
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Number of Trials
              </label>
              <input
                type="number"
                min={1}
                max={100}
                value={numTrials}
                onChange={(e) => {
                  const value = parseInt(e.target.value)
                  setNumTrials(isNaN(value) ? 1 : Math.max(1, Math.min(100, value)))
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Epochs per Trial
              </label>
              <input
                type="number"
                min={1}
                max={5}
                value={experimentEpochs}
                onChange={(e) => {
                  const value = parseInt(e.target.value)
                  setExperimentEpochs(isNaN(value) ? 1 : Math.max(1, Math.min(5, value)))
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">Use 1 for faster experiments</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Experiment Name
            </label>
            <input
              type="text"
              value={experimentName}
              onChange={(e) => setExperimentName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="lora_optimization"
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
          >
            {loading ? 'Starting...' : 'Start Optimization'}
          </button>
        </form>
      </div>

      {/* Selected Job Details */}
      {selectedJob && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Job Details</h3>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <span className="text-sm text-gray-600">Job ID:</span>
              <p className="font-mono text-sm">{selectedJob.id}</p>
            </div>
            <div>
              <span className="text-sm text-gray-600">Status:</span>
              <span className={`ml-2 px-2 py-1 rounded text-sm ${getJobStatusColor(selectedJob.status)}`}>
                {selectedJob.status}
              </span>
            </div>
            <div>
              <span className="text-sm text-gray-600">Progress:</span>
              <div className="mt-1">
                <div className="bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${selectedJob.progress * 100}%` }}
                  />
                </div>
                <p className="text-sm text-gray-600 mt-1">{(selectedJob.progress * 100).toFixed(1)}%</p>
              </div>
            </div>
            <div>
              <span className="text-sm text-gray-600">Trials:</span>
              <p className="font-medium">{selectedJob.config.num_trials}</p>
            </div>
          </div>

          {/* Best Parameters */}
          {selectedJob.result && selectedJob.result.best_parameters && (
            <div className="mt-6">
              <h4 className="text-lg font-semibold text-gray-900 mb-3">Best Parameters</h4>
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <dl className="grid grid-cols-2 gap-3">
                  {Object.entries(selectedJob.result.best_parameters).map(([key, value]) => (
                    <div key={key}>
                      <dt className="text-sm font-medium text-gray-700">{key.replace(/_/g, ' ')}</dt>
                      <dd className="mt-1 text-sm text-gray-900 font-mono">
                        {formatParameter(key, value)}
                      </dd>
                    </div>
                  ))}
                </dl>
              </div>

              {/* Parameter Importance */}
              {selectedJob.result.parameter_importance && Object.keys(selectedJob.result.parameter_importance).length > 0 && (
                <div className="mt-4">
                  <h5 className="text-sm font-semibold text-gray-700 mb-2">Parameter Importance</h5>
                  <div className="space-y-2">
                    {Object.entries(selectedJob.result.parameter_importance)
                      .sort(([, a], [, b]) => b - a)
                      .map(([param, importance]) => (
                        <div key={param} className="flex items-center">
                          <span className="w-32 text-sm text-gray-600">{param}</span>
                          <div className="flex-1 bg-gray-200 rounded-full h-2 mx-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${importance * 100}%` }}
                            />
                          </div>
                          <span className="text-sm text-gray-900">{(importance * 100).toFixed(1)}%</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {selectedJob.error && (
            <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
              {selectedJob.error}
            </div>
          )}
        </div>
      )}

      {/* Jobs List */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-bold text-gray-900">Optimization Jobs</h3>
          <button
            onClick={refreshJobs}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
          >
            Refresh
          </button>
        </div>

        {jobs.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No optimization jobs yet</p>
        ) : (
          <div className="space-y-3">
            {jobs.map((job) => (
              <div
                key={job.id}
                onClick={() => viewJobDetails(job.id)}
                className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 cursor-pointer transition-colors"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="font-mono text-sm text-gray-600">{job.id.slice(0, 8)}</span>
                      <span className={`px-2 py-1 rounded text-xs ${getJobStatusColor(job.status)}`}>
                        {job.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">
                      Model: <span className="font-medium">{job.config.base_model}</span>
                    </p>
                    <p className="text-sm text-gray-600">
                      Trials: <span className="font-medium">{job.config.num_trials}</span>
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">{(job.progress * 100).toFixed(0)}%</p>
                    <p className="text-xs text-gray-500">
                      {new Date(job.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
