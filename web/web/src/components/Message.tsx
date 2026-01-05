import ReactMarkdown from 'react-markdown'
import type { ChatMessage } from '../types/api'

interface MessageProps {
  message: ChatMessage
}

export function Message({ message }: MessageProps) {
  const isUser = message.role === 'user'
  const isSystem = message.role === 'system'

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div
        className={`max-w-[70%] rounded-lg px-4 py-3 ${
          isUser
            ? 'bg-blue-600 text-white'
            : isSystem
            ? 'bg-yellow-100 text-yellow-900 border border-yellow-300'
            : 'bg-gray-200 text-gray-900'
        }`}
      >
        {/* Role label */}
        <div className="text-xs font-semibold mb-1 opacity-75">
          {message.role.charAt(0).toUpperCase() + message.role.slice(1)}
        </div>

        {/* Message content with Markdown rendering */}
        <div className="prose prose-sm max-w-none">
          <ReactMarkdown
            components={{
              // Style headings
              h1: ({ node, ...props }) => <h1 className="text-xl font-bold mt-2 mb-1" {...props} />,
              h2: ({ node, ...props }) => <h2 className="text-lg font-bold mt-2 mb-1" {...props} />,
              h3: ({ node, ...props }) => <h3 className="text-base font-bold mt-1 mb-1" {...props} />,
              // Style code blocks
              code: ({ node, inline, ...props }) =>
                inline ? (
                  <code className="bg-gray-100 px-1 py-0.5 rounded text-sm" {...props} />
                ) : (
                  <code className="block bg-gray-100 px-2 py-1 rounded text-sm overflow-x-auto" {...props} />
                ),
              // Style lists
              ul: ({ node, ...props }) => <ul className="list-disc list-inside my-1" {...props} />,
              ol: ({ node, ...props }) => <ol className="list-decimal list-inside my-1" {...props} />,
              // Style paragraphs
              p: ({ node, ...props }) => <p className="my-1" {...props} />,
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  )
}
