import { useState, useEffect } from 'react'
import { modelsApi, trainingApi } from '../lib/api'
import type { Model } from '../types/api'

interface TrainingFormProps {
  onSuccess?: () => void
}

export function TrainingForm({ onSuccess }: TrainingFormProps) {
  // Models
  const [models, setModels] = useState<Model[]>([])
  const [loadingModels, setLoadingModels] = useState(true)

  // Form state
  const [baseModel, setBaseModel] = useState('')
  const [outputName, setOutputName] = useState('')
  const [dataset, setDataset] = useState<File | null>(null)
  const [epochs, setEpochs] = useState(3)
  const [batchSize, setBatchSize] = useState(2)
  const [loraRank, setLoraRank] = useState(8)
  const [loraLayers, setLoraLayers] = useState(16)
  const [learningRate, setLearningRate] = useState(0.0001)

  // Optimization parameters
  const [gradientCheckpoint, setGradientCheckpoint] = useState(true)
  const [maxSeqLength, setMaxSeqLength] = useState(2048)
  const [valBatches, setValBatches] = useState(25)
  const [stepsPerEval, setStepsPerEval] = useState(100)

  // UI state
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  // Fetch available models
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await modelsApi.list()
        const allModels = response.data || []
        // Filter to only base models for training
        const baseModels = allModels
          .map((model: Model) => ({ ...model, id: model.name }))
          .filter((model: Model) => model.type === 'base')
        setModels(baseModels)
      } catch (err) {
        console.error('Failed to fetch models:', err)
      } finally {
        setLoadingModels(false)
      }
    }

    fetchModels()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(false)

    // Validation
    if (!baseModel) {
      setError('Please select a base model')
      return
    }
    if (!outputName.trim()) {
      setError('Please enter an output name')
      return
    }
    if (!dataset) {
      setError('Please upload a training dataset')
      return
    }

    setSubmitting(true)

    try {
      await trainingApi.train(baseModel, outputName, dataset, {
        epochs,
        batchSize,
        loraRank,
        loraLayers,
        learningRate,
        gradientCheckpoint,
        maxSeqLength,
        valBatches,
        stepsPerEval,
      })

      setSuccess(true)
      // Reset form
      setOutputName('')
      setDataset(null)
      setEpochs(3)
      setBatchSize(2)
      setLoraRank(8)
      setLoraLayers(16)
      setLearningRate(0.0001)
      setGradientCheckpoint(true)
      setMaxSeqLength(2048)
      setValBatches(25)
      setStepsPerEval(100)

      // Call success callback
      if (onSuccess) {
        onSuccess()
      }

      // Clear file input
      const fileInput = document.getElementById('dataset-upload') as HTMLInputElement
      if (fileInput) {
        fileInput.value = ''
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start training job')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-semibold text-gray-900 mb-4">Start New Training</h3>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Base Model Selection */}
        <div>
          <label htmlFor="base-model" className="block text-sm font-medium text-gray-700 mb-2">
            Base Model *
          </label>
          {loadingModels ? (
            <div className="text-sm text-gray-500">Loading models...</div>
          ) : (
            <select
              id="base-model"
              value={baseModel}
              onChange={(e) => setBaseModel(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
              <option value="">Select a model</option>
              {models.map((model) => (
                <option key={model.id} value={model.name}>
                  {model.name} ({model.backend})
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Output Name */}
        <div>
          <label htmlFor="output-name" className="block text-sm font-medium text-gray-700 mb-2">
            Output Model Name *
          </label>
          <input
            type="text"
            id="output-name"
            value={outputName}
            onChange={(e) => setOutputName(e.target.value)}
            placeholder="e.g., my-finetuned-model"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            The name for your fine-tuned model adapter
          </p>
        </div>

        {/* Dataset Upload */}
        <div>
          <label htmlFor="dataset-upload" className="block text-sm font-medium text-gray-700 mb-2">
            Training Dataset (JSONL) *
          </label>
          <input
            type="file"
            id="dataset-upload"
            accept=".jsonl,.json"
            onChange={(e) => setDataset(e.target.files?.[0] || null)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          />
          {dataset && (
            <p className="text-sm text-green-600 mt-2">
              Selected: {dataset.name} ({(dataset.size / 1024).toFixed(2)} KB)
            </p>
          )}
          <p className="text-xs text-gray-500 mt-1">
            Upload a JSONL file with training examples ({"{"}"text": "..."{"}"} format)
          </p>
        </div>

        {/* Training Parameters */}
        <div className="space-y-4">
          <h4 className="text-sm font-semibold text-gray-900">Training Parameters</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div>
              <label htmlFor="epochs" className="block text-sm font-medium text-gray-700 mb-2">
                Epochs: {epochs}
              </label>
              <input
                type="range"
                id="epochs"
                min="1"
                max="20"
                value={epochs}
                onChange={(e) => setEpochs(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>1</span>
                <span>20</span>
              </div>
            </div>

          <div>
            <label htmlFor="batch-size" className="block text-sm font-medium text-gray-700 mb-2">
              Batch Size: {batchSize}
            </label>
            <input
              type="range"
              id="batch-size"
              min="1"
              max="16"
              value={batchSize}
              onChange={(e) => setBatchSize(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>1</span>
              <span>16</span>
            </div>
          </div>

          <div>
            <label htmlFor="lora-rank" className="block text-sm font-medium text-gray-700 mb-2">
              LoRA Rank: {loraRank}
            </label>
            <input
              type="range"
              id="lora-rank"
              min="1"
              max="64"
              value={loraRank}
              onChange={(e) => setLoraRank(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>1</span>
              <span>64</span>
            </div>
          </div>

          <div>
            <label htmlFor="lora-layers" className="block text-sm font-medium text-gray-700 mb-2">
              LoRA Layers: {loraLayers}
            </label>
            <input
              type="range"
              id="lora-layers"
              min="1"
              max="32"
              value={loraLayers}
              onChange={(e) => setLoraLayers(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>1</span>
              <span>32</span>
            </div>
          </div>

          <div className="md:col-span-2">
            <label htmlFor="learning-rate" className="block text-sm font-medium text-gray-700 mb-2">
              Learning Rate: {learningRate.toExponential(2)}
            </label>
            <input
              type="range"
              id="learning-rate"
              min="-6"
              max="-3"
              step="0.1"
              value={Math.log10(learningRate)}
              onChange={(e) => setLearningRate(Math.pow(10, parseFloat(e.target.value)))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>1e-6</span>
              <span>1e-3</span>
            </div>
          </div>
        </div>
        </div>

        {/* Optimization Parameters */}
        <div className="space-y-4">
          <h4 className="text-sm font-semibold text-gray-900">MLX Optimizations</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="md:col-span-2">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={gradientCheckpoint}
                  onChange={(e) => setGradientCheckpoint(e.target.checked)}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                />
                <div>
                  <span className="text-sm font-medium text-gray-900">Enable Gradient Checkpointing</span>
                  <p className="text-xs text-gray-600">Reduces memory usage for training on M4 (16GB RAM)</p>
                </div>
              </label>
            </div>

            <div>
              <label htmlFor="max-seq-length" className="block text-sm font-medium text-gray-700 mb-2">
                Max Sequence Length: {maxSeqLength}
              </label>
              <input
                type="range"
                id="max-seq-length"
                min="512"
                max="8192"
                step="512"
                value={maxSeqLength}
                onChange={(e) => setMaxSeqLength(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>512</span>
                <span>8192</span>
              </div>
            </div>

            <div>
              <label htmlFor="val-batches" className="block text-sm font-medium text-gray-700 mb-2">
                Validation Batches: {valBatches}
              </label>
              <input
                type="range"
                id="val-batches"
                min="5"
                max="100"
                step="5"
                value={valBatches}
                onChange={(e) => setValBatches(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>5</span>
                <span>100</span>
              </div>
            </div>

            <div className="md:col-span-2">
              <label htmlFor="steps-per-eval" className="block text-sm font-medium text-gray-700 mb-2">
                Steps Per Evaluation: {stepsPerEval}
              </label>
              <input
                type="range"
                id="steps-per-eval"
                min="10"
                max="500"
                step="10"
                value={stepsPerEval}
                onChange={(e) => setStepsPerEval(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>10</span>
                <span>500</span>
              </div>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Success Message */}
        {success && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-800">Training job started successfully!</p>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={submitting || loadingModels}
          className="w-full px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {submitting ? (
            <span className="flex items-center justify-center">
              <svg
                className="animate-spin h-5 w-5 mr-2"
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
              Starting Training...
            </span>
          ) : (
            'Start Training'
          )}
        </button>
      </form>
    </div>
  )
}
