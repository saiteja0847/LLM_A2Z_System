import { useEffect, useState } from 'react'
import { systemApi } from '../lib/api'
import type { HealthResponse } from '../types/api'

export function SystemStatus() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await systemApi.health()
        setHealth(response.data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to connect to API')
        setHealth(null)
      } finally {
        setLoading(false)
      }
    }

    checkHealth()
    // Check health every 30 seconds
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-center">
          <div className="w-3 h-3 bg-yellow-400 rounded-full animate-pulse mr-3"></div>
          <div>
            <h3 className="font-semibold text-yellow-900">Checking API status...</h3>
          </div>
        </div>
      </div>
    )
  }

  if (error || !health) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <div className="w-3 h-3 bg-red-500 rounded-full mr-3"></div>
          <div className="flex-1">
            <h3 className="font-semibold text-red-900">API Connection Failed</h3>
            <p className="text-sm text-red-700 mt-1">
              {error || 'Cannot connect to backend'}
            </p>
            <p className="text-sm text-red-600 mt-2">
              Make sure the backend is running: <code className="bg-red-100 px-2 py-1 rounded">uvicorn src.ai_lab.api.app:app --reload</code>
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
      <div className="flex items-center">
        <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
        <div className="flex-1">
          <h3 className="font-semibold text-green-900">API Connected</h3>
          <div className="text-sm text-green-700 mt-1">
            <div>Status: {health.status}</div>
            <div>Version: {health.version}</div>
            <div>
              MLX Backend:{' '}
              {health.mlx_available ? (
                <span className="text-green-600 font-medium">Available</span>
              ) : (
                <span className="text-red-600 font-medium">Not Available</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
