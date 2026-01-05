import { useState } from 'react'
import { SystemStatus } from './components/SystemStatus'

function App() {
  const [currentPage, setCurrentPage] = useState('home')

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 text-white">
        <div className="p-6">
          <h1 className="text-2xl font-bold mb-8">AI Lab</h1>
          <nav className="space-y-2">
            <button
              onClick={() => setCurrentPage('home')}
              className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                currentPage === 'home'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800'
              }`}
            >
              Home
            </button>
            <button
              onClick={() => setCurrentPage('models')}
              className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                currentPage === 'models'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800'
              }`}
            >
              Models
            </button>
            <button
              onClick={() => setCurrentPage('chat')}
              className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                currentPage === 'chat'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800'
              }`}
            >
              Chat
            </button>
            <button
              onClick={() => setCurrentPage('training')}
              className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                currentPage === 'training'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800'
              }`}
            >
              Training
            </button>
          </nav>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          {currentPage === 'home' && <HomePage />}
          {currentPage === 'models' && <ModelsPage />}
          {currentPage === 'chat' && <ChatPage />}
          {currentPage === 'training' && <TrainingPage />}
        </div>
      </main>
    </div>
  )
}

function HomePage() {
  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-900 mb-4">Welcome to AI Lab</h2>
      <p className="text-gray-700 mb-6">
        Your local LLM platform for model management, training, and inference.
      </p>

      {/* System Status */}
      <div className="mb-8">
        <SystemStatus />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card title="Models" description="Manage and download local models" />
        <Card title="Chat" description="Interactive chat with your models" />
        <Card title="Training" description="Fine-tune models with LoRA" />
      </div>
    </div>
  )
}

function ModelsPage() {
  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-900 mb-4">Models</h2>
      <p className="text-gray-700">Model management coming soon...</p>
    </div>
  )
}

function ChatPage() {
  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-900 mb-4">Chat</h2>
      <p className="text-gray-700">Chat interface coming soon...</p>
    </div>
  )
}

function TrainingPage() {
  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-900 mb-4">Training</h2>
      <p className="text-gray-700">Training interface coming soon...</p>
    </div>
  )
}

function Card({ title, description }: { title: string; description: string }) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <h3 className="text-xl font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}

export default App
