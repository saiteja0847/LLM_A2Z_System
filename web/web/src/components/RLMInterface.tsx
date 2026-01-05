import { useState } from 'react'
import { rlmApi } from '../lib/api'
import { ModelSelector } from './ModelSelector'

type RLMMode = 'simple' | 'full'
type Environment = 'local' | 'docker' | 'modal'

interface RLMResult {
  response: string
  model: string
  prompt_size: number
  iterations: number
  sub_calls: number
  execution_time: number
  usage_summary: Record<string, unknown>
}

export function RLMInterface() {
  const [selectedModel, setSelectedModel] = useState<string | null>(null)
  const [mode, setMode] = useState<RLMMode>('simple')
  const [prompt, setPrompt] = useState('')
  const [rootPrompt, setRootPrompt] = useState('')
  const [maxIterations, setMaxIterations] = useState(30)
  const [environment, setEnvironment] = useState<Environment>('local')
  const [verbose, setVerbose] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<RLMResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleProcess = async () => {
    if (!selectedModel || !prompt.trim() || loading) return

    setLoading(true)
    setResult(null)
    setError(null)

    try {
      let response

      if (mode === 'simple') {
        // Simple RLM - fast, direct MLX access
        response = await rlmApi.simpleComplete(
          selectedModel,
          prompt.trim(),
          rootPrompt.trim() || undefined
        )
      } else {
        // Full RLM - with code execution
        response = await rlmApi.fullComplete(
          selectedModel,
          prompt.trim(),
          rootPrompt.trim() || undefined,
          {
            maxIterations,
            environment,
            verbose,
          }
        )
      }

      setResult(response.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process RLM request')
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setResult(null)
    setError(null)
    setPrompt('')
    setRootPrompt('')
  }

  const handleLoadSample = () => {
    setPrompt(`Chapter 1: Introduction to AI
Artificial Intelligence is transforming how we process information.
Traditional language models have context limitations.

Chapter 2: The Solution
RLM (Recursive Language Models) enable near-infinite context handling
by intelligently chunking and processing large documents.

Chapter 3: Benefits
This approach allows processing of documents of any size, making it
possible to analyze entire books, research papers, and log files.

Chapter 4: Technical Details
The recursive approach involves breaking down large inputs into
manageable chunks, processing each chunk independently, and then
aggregating the results into a coherent final answer.

Chapter 5: Use Cases
RLM is particularly useful for:
- Analyzing large log files
- Processing entire books
- Reviewing research papers
- Extracting information from extensive documentation
- Multi-step reasoning tasks`)

    setRootPrompt('Summarize the key benefits of RLM in 2-3 sentences')
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">RLM Processing</h2>
          <ModelSelector
            selectedModel={selectedModel}
            onModelChange={setSelectedModel}
          />
        </div>

        {/* Mode Selector */}
        <div className="flex items-center space-x-4">
          <span className="text-sm font-medium text-gray-700">Mode:</span>
          <div className="flex rounded-lg shadow-sm" role="group">
            <button
              type="button"
              onClick={() => setMode('simple')}
              className={`px-4 py-2 text-sm font-medium rounded-l-lg border ${
                mode === 'simple'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              Simple RLM
            </button>
            <button
              type="button"
              onClick={() => setMode('full')}
              className={`px-4 py-2 text-sm font-medium rounded-r-lg border-t border-b border-r ${
                mode === 'full'
                  ? 'bg-purple-600 text-white border-purple-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              Full RLM
            </button>
          </div>
        </div>

        {/* Mode Description */}
        <div className={`p-3 rounded-lg text-sm ${
          mode === 'simple'
            ? 'bg-blue-50 text-blue-800 border border-blue-200'
            : 'bg-purple-50 text-purple-800 border border-purple-200'
        }`}>
          {mode === 'simple' ? (
            <div>
              <p className="font-medium mb-1">⚡ Simple RLM - Fast Processing</p>
              <p className="text-xs">Direct MLX access, no server needed. Best for quick document processing and summarization.</p>
            </div>
          ) : (
            <div>
              <p className="font-medium mb-1">🧠 Full RLM - Advanced with Code Execution</p>
              <p className="text-xs">Uses official RLM library with Python code execution. Best for complex analysis and multi-step reasoning.</p>
            </div>
          )}
        </div>

        {/* Full RLM Options */}
        {mode === 'full' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Iterations
              </label>
              <input
                type="number"
                value={maxIterations}
                onChange={(e) => setMaxIterations(Number(e.target.value))}
                min={1}
                max={100}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Environment
              </label>
              <select
                value={environment}
                onChange={(e) => setEnvironment(e.target.value as Environment)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="local">Local</option>
                <option value="docker">Docker</option>
                <option value="modal">Modal</option>
              </select>
            </div>
            <div className="flex items-end">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={verbose}
                  onChange={(e) => setVerbose(e.target.checked)}
                  className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                />
                <span className="text-sm font-medium text-gray-700">Verbose</span>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6 bg-gray-50">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Prompt Input */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-3">
              <label className="text-lg font-semibold text-gray-900">
                Context / Document
              </label>
              <button
                onClick={handleLoadSample}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                Load Sample
              </button>
            </div>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Paste your large document or context here..."
              disabled={loading}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none disabled:bg-gray-100 disabled:cursor-not-allowed"
              rows={10}
            />
            <div className="mt-2 text-xs text-gray-500">
              Characters: {prompt.length.toLocaleString()}
            </div>
          </div>

          {/* Root Prompt Input */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <label className="text-lg font-semibold text-gray-900 mb-3 block">
              Task / Question
            </label>
            <textarea
              value={rootPrompt}
              onChange={(e) => setRootPrompt(e.target.value)}
              placeholder="What would you like to know about the context? (Optional)"
              disabled={loading}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none disabled:bg-gray-100 disabled:cursor-not-allowed"
              rows={3}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between">
            <button
              onClick={handleClear}
              disabled={!result && !error}
              className="px-4 py-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              Clear
            </button>
            <button
              onClick={handleProcess}
              disabled={!selectedModel || !prompt.trim() || loading}
              className={`px-6 py-3 text-white font-medium rounded-lg transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed ${
                mode === 'simple'
                  ? 'bg-blue-600 hover:bg-blue-700'
                  : 'bg-purple-600 hover:bg-purple-700'
              }`}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg
                    className="animate-spin h-5 w-5"
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
                  <span>Processing...</span>
                </span>
              ) : (
                `Process with ${mode === 'simple' ? 'Simple RLM' : 'Full RLM'}`
              )}
            </button>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex">
                <svg
                  className="w-6 h-6 text-red-600 mr-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-red-900 mb-1">Error</h3>
                  <p className="text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Result */}
          {result && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Result</h3>

              {/* Statistics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Execution Time</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {result.execution_time.toFixed(2)}s
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Prompt Size</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {result.prompt_size.toLocaleString()} chars
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Iterations</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {result.iterations}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Sub-calls</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {result.sub_calls}
                  </div>
                </div>
              </div>

              {/* Response */}
              <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Response:</h4>
                <p className="text-gray-900 whitespace-pre-wrap">{result.response}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
