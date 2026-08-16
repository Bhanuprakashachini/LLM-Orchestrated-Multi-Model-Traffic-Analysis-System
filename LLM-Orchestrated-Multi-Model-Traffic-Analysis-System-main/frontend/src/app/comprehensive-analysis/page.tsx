'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'
import ComprehensiveModelComparison from '@/components/analysis/ComprehensiveModelComparison'

interface ComprehensiveAnalysisData {
  analysis_info: {
    filename: string
    file_size: number
    analysis_timestamp: string
    total_models_compared: number
    analysis_time: string
  }
  comparison_table: any[]
  performance_table: {
    headers: string[]
    rows: string[][]
  }
  detailed_metrics: {
    accuracy_metrics: { headers: string[]; rows: string[][] }
    performance_metrics: { headers: string[]; rows: string[][] }
    detection_metrics: { headers: string[]; rows: string[][] }
  }
  recommendations: {
    best_overall?: { model: string; reason: string }
    best_accuracy?: { model: string; reason: string }
    best_speed?: { model: string; reason: string }
  }
  use_case_recommendations: Record<string, any>
  model_selection_guide: any
}

export default function ComprehensiveAnalysisPage() {
  const { user } = useAuth()
  const router = useRouter()
  const [analysisData, setAnalysisData] = useState<ComprehensiveAnalysisData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [selectedModel, setSelectedModel] = useState<string | null>(null)
  const [modelJustification, setModelJustification] = useState<any>(null)

  useEffect(() => {
    if (!user) {
      router.push('/login')
      return
    }

    // Load comprehensive analysis data from localStorage
    const storedData = localStorage.getItem('comprehensiveAnalysis')
    if (storedData) {
      try {
        const data = JSON.parse(storedData)
        setAnalysisData(data)
        console.log('Loaded comprehensive analysis data:', data)
      } catch (error) {
        console.error('Failed to parse stored analysis data:', error)
        toast.error('Failed to load analysis data')
        router.push('/upload')
      }
    } else {
      toast.error('No analysis data found. Please upload a file first.')
      router.push('/upload')
    }
    
    setIsLoading(false)
  }, [user, router])

  const handleModelSelect = async (modelName: string) => {
    if (!analysisData) return

    setSelectedModel(modelName)
    
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        toast.error('Authentication required')
        return
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/analysis/comprehensive/justification/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model_name: modelName,
          comparison_results: analysisData
        })
      })

      if (response.ok) {
        const justification = await response.json()
        setModelJustification(justification)
        toast.success(`Model justification loaded for ${modelName}`)
      } else {
        toast.error('Failed to load model justification')
      }
    } catch (error) {
      console.error('Error loading model justification:', error)
      toast.error('Failed to load model justification')
    }
  }

  const handleExportCSV = async () => {
    if (!analysisData) return

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        toast.error('Authentication required')
        return
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/analysis/comprehensive/export-csv/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          comparison_results: analysisData
        })
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.style.display = 'none'
        a.href = url
        a.download = `model_comparison_${Date.now()}.csv`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        toast.success('CSV exported successfully!')
      } else {
        toast.error('Failed to export CSV')
      }
    } catch (error) {
      console.error('Error exporting CSV:', error)
      toast.error('Failed to export CSV')
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading comprehensive analysis...</p>
        </div>
      </div>
    )
  }

  if (!analysisData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">No analysis data available</p>
          <button
            onClick={() => router.push('/upload')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Upload New File
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-purple-200">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <button
                onClick={() => router.push('/upload')}
                className="mr-4 p-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <h1 className="text-2xl font-bold text-purple-700">
                Comprehensive Model Analysis
              </h1>
            </div>

            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/dashboard')}
                className="px-4 py-2 text-sm font-medium text-purple-600 hover:text-purple-700 transition-colors"
              >
                Dashboard
              </button>
              <button
                onClick={() => router.push('/history')}
                className="px-4 py-2 text-sm font-medium text-purple-600 hover:text-purple-700 transition-colors"
              >
                History
              </button>

              {/* User Info */}
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">
                    {user?.first_name?.charAt(0) || user?.username?.charAt(0) || 'U'}
                  </span>
                </div>
                <div className="text-sm">
                  <p className="font-medium text-gray-900">
                    {user?.first_name && user?.last_name 
                      ? `${user.first_name} ${user.last_name}` 
                      : user?.username || 'User'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <div className="max-w-7xl mx-auto">
          {/* Comprehensive Model Comparison Component */}
          <ComprehensiveModelComparison
            comparisonData={analysisData}
            onModelSelect={handleModelSelect}
            onExportCSV={handleExportCSV}
          />

          {/* Model Justification Section */}
          {selectedModel && modelJustification && (
            <div className="mt-8 bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                🎯 Model Selection Justification: {selectedModel}
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Performance Metrics</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Accuracy Score:</span>
                      <span className="font-medium">{modelJustification.selection_rationale?.accuracy_score}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">F1-Score:</span>
                      <span className="font-medium">{modelJustification.selection_rationale?.performance_score}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Processing Speed:</span>
                      <span className="font-medium">{modelJustification.selection_rationale?.speed_score}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Overall Grade:</span>
                      <span className="font-medium">{modelJustification.selection_rationale?.overall_grade}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Key Strengths</h3>
                  <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                    {modelJustification.strengths?.map((strength: string, idx: number) => (
                      <li key={idx}>{strength}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h3 className="font-medium text-blue-900 mb-2">Project Justification</h3>
                <p className="text-sm text-blue-800">{modelJustification.project_justification}</p>
              </div>

              <div className="mt-4">
                <h3 className="font-medium text-gray-900 mb-2">Recommended Use Cases</h3>
                <div className="flex flex-wrap gap-2">
                  {modelJustification.best_use_cases?.map((useCase: string, idx: number) => (
                    <span key={idx} className="px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full">
                      {useCase}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="mt-8 flex justify-center space-x-4">
            <button
              onClick={() => router.push('/upload')}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Analyze Another File
            </button>
            <button
              onClick={() => router.push('/dashboard')}
              className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}