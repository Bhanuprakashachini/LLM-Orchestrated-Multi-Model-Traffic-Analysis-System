'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'

interface Insight {
  id: number
  type: string
  title: string
  insight: string
  confidence: number
  timestamp: string
}

export default function InsightsPage() {
  const { user } = useAuth()
  const [insights, setInsights] = useState<Insight[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Simulate loading LLM insights
    const timer = setTimeout(() => {
      setInsights([
        {
          id: 1,
          type: 'traffic_pattern',
          title: 'Peak Hour Analysis',
          insight: 'Traffic congestion typically peaks between 8-9 AM and 5-6 PM with 40% higher vehicle density.',
          confidence: 92,
          timestamp: new Date().toISOString()
        },
        {
          id: 2,
          type: 'vehicle_distribution',
          title: 'Vehicle Type Distribution',
          insight: 'Cars represent 75% of traffic, Large Vehicles 15%, and 2-Wheelers 10% in urban areas.',
          confidence: 88,
          timestamp: new Date().toISOString()
        }
      ])
      setIsLoading(false)
    }, 2000)

    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="px-6 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            🧠 Intelligent Insights (LLM-based)
          </h1>
          <p className="text-gray-600 mt-1">
            AI-powered traffic analysis with intelligent recommendations and pattern recognition
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <div className="max-w-6xl mx-auto">
          {/* Feature Overview */}
          <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              LLM-Powered Analysis Capabilities
            </h2>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center p-4 bg-indigo-50 rounded-lg">
                <div className="text-3xl mb-2">🤖</div>
                <h3 className="font-semibold text-indigo-800">Pattern Recognition</h3>
                <p className="text-sm text-indigo-600 mt-2">
                  AI identifies complex traffic patterns and behavioral trends
                </p>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-3xl mb-2">💡</div>
                <h3 className="font-semibold text-purple-800">Smart Recommendations</h3>
                <p className="text-sm text-purple-600 mt-2">
                  Intelligent suggestions for traffic optimization and management
                </p>
              </div>
              <div className="text-center p-4 bg-pink-50 rounded-lg">
                <div className="text-3xl mb-2">📈</div>
                <h3 className="font-semibold text-pink-800">Predictive Analytics</h3>
                <p className="text-sm text-pink-600 mt-2">
                  Forecast traffic conditions and congestion patterns
                </p>
              </div>
            </div>
          </div>

          {/* LLM Insights Display */}
          <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Recent AI Insights
            </h2>
            
            {isLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Generating intelligent insights...</p>
              </div>
            ) : (
              <div className="space-y-4">
                {insights.map((insight) => (
                  <div key={insight.id} className="p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg border-l-4 border-indigo-500">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-indigo-800 mb-2">{insight.title}</h3>
                        <p className="text-gray-700 mb-2">{insight.insight}</p>
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span>Confidence: {insight.confidence}%</span>
                          <span>Generated: {new Date(insight.timestamp).toLocaleString()}</span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                          insight.confidence >= 90 ? 'bg-green-100 text-green-800' :
                          insight.confidence >= 80 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {insight.confidence >= 90 ? 'High' : insight.confidence >= 80 ? 'Medium' : 'Low'} Confidence
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* LLM Features */}
          <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              AI Analysis Features
            </h2>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border-l-4 border-blue-500">
                <h3 className="font-semibold text-blue-800 mb-2">Natural Language Processing</h3>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Traffic pattern description</li>
                  <li>• Automated report generation</li>
                  <li>• Insight summarization</li>
                  <li>• Recommendation explanations</li>
                </ul>
              </div>
              <div className="p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border-l-4 border-purple-500">
                <h3 className="font-semibold text-purple-800 mb-2">Machine Learning Analysis</h3>
                <ul className="text-sm text-purple-700 space-y-1">
                  <li>• Anomaly detection</li>
                  <li>• Trend identification</li>
                  <li>• Correlation analysis</li>
                  <li>• Predictive modeling</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Coming Soon Notice */}
          <div className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl p-8 text-center">
            <div className="text-6xl mb-4">🚧</div>
            <h2 className="text-2xl font-bold mb-4">Intelligent Insights Module</h2>
            <p className="text-lg mb-6">
              Advanced LLM-powered traffic analysis and intelligent recommendations are currently in development.
            </p>
            <div className="bg-white/20 rounded-lg p-4 max-w-2xl mx-auto">
              <h3 className="font-semibold mb-2">Planned Features:</h3>
              <ul className="text-left space-y-1">
                <li>• GPT-powered traffic analysis</li>
                <li>• Natural language insights</li>
                <li>• Automated report generation</li>
                <li>• Predictive traffic modeling</li>
                <li>• Smart optimization suggestions</li>
                <li>• Conversational traffic queries</li>
              </ul>
            </div>
            <button 
              className="mt-6 bg-white text-indigo-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
              onClick={() => window.history.back()}
            >
              ← Back to Dashboard
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}