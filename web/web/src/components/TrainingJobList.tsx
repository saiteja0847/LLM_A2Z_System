import { useState, useEffect } from 'react'
import { trainingApi } from '../lib/api'
import type { TrainingJob } from '../types/api'
import { TrainingJobCard } from './TrainingJobCard'

interface TrainingJobListProps {
  onJobClick?: (job: TrainingJob) => void
  refreshTrigger?: number
}

export function TrainingJobList({ onJobClick, refreshTrigger }: TrainingJobListProps) {
  const [jobs, setJobs] = useState<TrainingJob[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch jobs
  const fetchJobs = async () => {
    try {
      setError(null)
      const response = await trainingApi.listJobs()
      setJobs(response.data.jobs || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch training jobs')
    } finally {
      setLoading(false)
    }
  }

  // Initial fetch and refresh when trigger changes
  useEffect(() => {
    fetchJobs()
  }, [refreshTrigger])

  // Auto-refresh every 5 seconds if there are running jobs
  useEffect(() => {
    const hasRunningJobs = jobs.some((job) => job.status === 'running' || job.status === 'pending')

    if (!hasRunningJobs) return

    const interval = setInterval(() => {
      fetchJobs()
    }, 5000) // 5 seconds

    return () => clearInterval(interval)
  }, [jobs])

  // Loading state
  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="text-center">
          <svg
            className="animate-spin h-10 w-10 text-blue-600 mx-auto mb-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            ></circle>
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          <p className="text-gray-600">Loading training jobs...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-start">
          <svg
            className="w-6 h-6 text-red-600 mr-3 flex-shrink-0"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
          <div>
            <h3 className="text-red-800 font-medium mb-1">Failed to load training jobs</h3>
            <p className="text-red-700 text-sm">{error}</p>
            <button
              onClick={fetchJobs}
              className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Empty state
  if (jobs.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <svg
          className="w-16 h-16 text-gray-400 mx-auto mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
          />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No training jobs yet</h3>
        <p className="text-gray-600">Start a new training job to fine-tune your models</p>
      </div>
    )
  }

  // Group jobs by status
  const runningJobs = jobs.filter((job) => job.status === 'running')
  const pendingJobs = jobs.filter((job) => job.status === 'pending')
  const completedJobs = jobs.filter((job) => job.status === 'completed')
  const failedJobs = jobs.filter((job) => job.status === 'failed')

  return (
    <div className="space-y-6">
      {/* Running Jobs */}
      {runningJobs.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
            <span className="w-3 h-3 bg-blue-500 rounded-full mr-2 animate-pulse"></span>
            Running ({runningJobs.length})
          </h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {runningJobs.map((job) => (
              <TrainingJobCard
                key={job.id}
                job={job}
                onClick={onJobClick ? () => onJobClick(job) : undefined}
              />
            ))}
          </div>
        </div>
      )}

      {/* Pending Jobs */}
      {pendingJobs.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
            <span className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></span>
            Pending ({pendingJobs.length})
          </h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {pendingJobs.map((job) => (
              <TrainingJobCard
                key={job.id}
                job={job}
                onClick={onJobClick ? () => onJobClick(job) : undefined}
              />
            ))}
          </div>
        </div>
      )}

      {/* Completed Jobs */}
      {completedJobs.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
            <span className="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
            Completed ({completedJobs.length})
          </h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {completedJobs.map((job) => (
              <TrainingJobCard
                key={job.id}
                job={job}
                onClick={onJobClick ? () => onJobClick(job) : undefined}
              />
            ))}
          </div>
        </div>
      )}

      {/* Failed Jobs */}
      {failedJobs.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
            <span className="w-3 h-3 bg-red-500 rounded-full mr-2"></span>
            Failed ({failedJobs.length})
          </h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {failedJobs.map((job) => (
              <TrainingJobCard
                key={job.id}
                job={job}
                onClick={onJobClick ? () => onJobClick(job) : undefined}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
