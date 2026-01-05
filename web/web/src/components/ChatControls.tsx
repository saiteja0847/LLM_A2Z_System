interface ChatControlsProps {
  temperature: number
  maxTokens: number
  onTemperatureChange: (temp: number) => void
  onMaxTokensChange: (tokens: number) => void
}

export function ChatControls({
  temperature,
  maxTokens,
  onTemperatureChange,
  onMaxTokensChange,
}: ChatControlsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
      {/* Temperature Control */}
      <div>
        <label htmlFor="temperature" className="block text-sm font-medium text-gray-700 mb-2">
          Temperature: {temperature.toFixed(2)}
        </label>
        <input
          type="range"
          id="temperature"
          min="0"
          max="2"
          step="0.1"
          value={temperature}
          onChange={(e) => onTemperatureChange(parseFloat(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>Focused (0.0)</span>
          <span>Balanced (1.0)</span>
          <span>Creative (2.0)</span>
        </div>
      </div>

      {/* Max Tokens Control */}
      <div>
        <label htmlFor="max-tokens" className="block text-sm font-medium text-gray-700 mb-2">
          Max Tokens: {maxTokens}
        </label>
        <input
          type="range"
          id="max-tokens"
          min="64"
          max="2048"
          step="64"
          value={maxTokens}
          onChange={(e) => onMaxTokensChange(parseInt(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>Short (64)</span>
          <span>Medium (1024)</span>
          <span>Long (2048)</span>
        </div>
      </div>
    </div>
  )
}
