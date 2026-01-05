import { useState, useEffect } from 'react'
import { modelsApi } from '../lib/api'

interface DownloadModelProps {
  onSuccess?: () => void
}

// Helper function to format elapsed time
const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (mins > 0) {
    return `${mins}m ${secs}s`
  }
  return `${secs}s`
}

export function DownloadModel({ onSuccess }: DownloadModelProps) {
  const [repo, setRepo] = useState('')
  const [alias, setAlias] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [downloadStartTime, setDownloadStartTime] = useState<number | null>(null)
  const [elapsedTime, setElapsedTime] = useState(0)

  // Timer for download progress
  useEffect(() => {
    let interval: number | undefined
    if (loading && downloadStartTime) {
      interval = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - downloadStartTime) / 1000))
      }, 1000)
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [loading, downloadStartTime])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!repo || !alias) {
      setError('Both repository and alias are required')
      return
    }

    try {
      setLoading(true)
      setError(null)
      setSuccess(false)
      setDownloadStartTime(Date.now())
      setElapsedTime(0)

      await modelsApi.download(repo, alias)

      setSuccess(true)
      setRepo('')
      setAlias('')
      setDownloadStartTime(null)
      setElapsedTime(0)

      // Call onSuccess callback after a short delay
      setTimeout(() => {
        onSuccess?.()
        setSuccess(false)
      }, 2000)
    } catch (err) {
      // Extract detailed error message
      let errorMessage = 'Failed to download model'
      if (err instanceof Error) {
        // Check if axios added userMessage
        errorMessage = (err as any).userMessage || err.message || errorMessage
      }
      setError(errorMessage)
      setDownloadStartTime(null)
      setElapsedTime(0)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-semibold text-gray-900 mb-4">
        Download Model from HuggingFace
      </h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="repo" className="block text-sm font-medium text-gray-700 mb-2">
            Repository
          </label>
          <input
            type="text"
            id="repo"
            value={repo}
            onChange={(e) => setRepo(e.target.value)}
            placeholder="e.g., mlx-community/Qwen2.5-1.5B-Instruct-4bit"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
          <p className="mt-1 text-xs text-gray-500">
            HuggingFace repository in format: organization/model-name
          </p>
        </div>

        <div>
          <label htmlFor="alias" className="block text-sm font-medium text-gray-700 mb-2">
            Alias (Local Name)
          </label>
          <input
            type="text"
            id="alias"
            value={alias}
            onChange={(e) => setAlias(e.target.value)}
            placeholder="e.g., qwen-1.5b"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
          <p className="mt-1 text-xs text-gray-500">
            Short name to identify this model locally
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {success && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-green-700 text-sm">Model download started successfully!</p>
          </div>
        )}

        <button
          type="submit"
          disabled={loading || !repo || !alias}
          className="w-full px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {loading ? (
            <span className="flex flex-col items-center justify-center">
              <div className="flex items-center mb-2">
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
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
                <span className="font-medium">Downloading Model...</span>
              </div>
              <span className="text-xs text-blue-100">
                Elapsed time: {formatTime(elapsedTime)}
              </span>
            </span>
          ) : (
            'Download Model'
          )}
        </button>
      </form>

      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h4 className="text-sm font-semibold text-blue-900 mb-2">Example Models:</h4>
        <ul className="text-xs text-blue-800 space-y-1">
          <li>• mlx-community/Qwen3-4B-Instruct-2507-4bit (recommended)</li>
          <li>• mlx-community/Qwen2.5-7B-Instruct-4bit</li>
          <li>• mlx-community/Llama-3.1-8B-Instruct-4bit</li>
          <li>• mlx-community/Mistral-7B-Instruct-v0.3-4bit</li>
        </ul>
        <p className="text-xs text-blue-700 mt-2">
          💡 Large models (4GB+) can take 5-10 minutes to download. The download will continue in the background.
        </p>
      </div>
    </div>
  )
}
