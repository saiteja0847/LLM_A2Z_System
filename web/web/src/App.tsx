import { useState } from 'react'
import { SystemStatus } from './components/SystemStatus'
import { ModelList } from './components/ModelList'
import { DownloadModel } from './components/DownloadModel'
import { ChatInterface } from './components/ChatInterface'
import { TrainingForm } from './components/TrainingForm'
import { TrainingJobList } from './components/TrainingJobList'
import { TrainingJobDetails } from './components/TrainingJobDetails'
import { OptimizationInterface } from './components/OptimizationInterface'
import { RLMInterface } from './components/RLMInterface'
import type { TrainingJob } from './types/api'

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
            <button
              onClick={() => setCurrentPage('optimization')}
              className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                currentPage === 'optimization'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800'
              }`}
            >
              Optimization
            </button>
            <button
              onClick={() => setCurrentPage('rlm')}
              className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                currentPage === 'rlm'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800'
              }`}
            >
              RLM
            </button>
          </nav>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {currentPage === 'chat' ? (
          <ChatPage />
        ) : currentPage === 'rlm' ? (
          <RLMPage />
        ) : (
          <div className="p-8">
            {currentPage === 'home' && <HomePage />}
            {currentPage === 'models' && <ModelsPage />}
            {currentPage === 'training' && <TrainingPage />}
            {currentPage === 'optimization' && <OptimizationPage />}
          </div>
        )}
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
  const [refreshKey, setRefreshKey] = useState(0)

  const handleDownloadSuccess = () => {
    // Trigger a refresh of the model list
    setRefreshKey((prev) => prev + 1)
  }

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-900 mb-6">Model Management</h2>

      {/* Download Section */}
      <div className="mb-8">
        <DownloadModel onSuccess={handleDownloadSuccess} />
      </div>

      {/* Models List */}
      <div key={refreshKey}>
        <ModelList />
      </div>
    </div>
  )
}

function ChatPage() {
  return (
    <div className="h-full flex flex-col">
      <h2 className="text-3xl font-bold text-gray-900 mb-4 px-8 pt-8">Chat Playground</h2>
      <div className="flex-1 min-h-0">
        <ChatInterface />
      </div>
    </div>
  )
}

function TrainingPage() {
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const [selectedJob, setSelectedJob] = useState<TrainingJob | null>(null)

  const handleTrainingSuccess = () => {
    // Trigger refresh of job list
    setRefreshTrigger((prev) => prev + 1)
  }

  const handleJobClick = (job: TrainingJob) => {
    setSelectedJob(job)
  }

  const handleCloseModal = () => {
    setSelectedJob(null)
  }

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-900 mb-6">Training</h2>

      {/* Training Form */}
      <div className="mb-8">
        <TrainingForm onSuccess={handleTrainingSuccess} />
      </div>

      {/* Job List */}
      <div>
        <h3 className="text-2xl font-semibold text-gray-900 mb-4">Training Jobs</h3>
        <TrainingJobList
          onJobClick={handleJobClick}
          refreshTrigger={refreshTrigger}
        />
      </div>

      {/* Job Details Modal */}
      {selectedJob && (
        <TrainingJobDetails
          job={selectedJob}
          onClose={handleCloseModal}
        />
      )}
    </div>
  )
}

function OptimizationPage() {
  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-900 mb-6">Hyperparameter Optimization</h2>
      <OptimizationInterface />
    </div>
  )
}

function RLMPage() {
  return (
    <div className="h-full flex flex-col">
      <h2 className="text-3xl font-bold text-gray-900 mb-4 px-8 pt-8">Recursive Language Model (RLM)</h2>
      <div className="flex-1 min-h-0">
        <RLMInterface />
      </div>
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
