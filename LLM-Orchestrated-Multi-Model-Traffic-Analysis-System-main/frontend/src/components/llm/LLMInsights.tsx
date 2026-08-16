'use client'

import { useState } from 'react'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import llmService from '@/services/llmService'
import toast from 'react-hot-toast'

interface LLMInsightsProps {
  insights: {
    conditions?: any
    summary?: any
    recommendations?: any
  }
  isLoading?: boolean
}

export default function LLMInsights({ insights, isLoading }: LLMInsightsProps) {
  const [activeTab, setActiveTab] = useState<'conditions' | 'summary' | 'recommendations' | 'chat'>('conditions')
  const [chatQuery, setChatQuery] = useState('')
  const [chatResponse, setChatResponse] = useState('')
  const [isChatLoading, setIsChatLoading] = useState(false)

  const handleChatQuery = async () => {
    if (!chatQuery.trim()) {
      toast.error('Please enter a question')
      return
    }

    setIsChatLoading(true)
    try {
      const response = await llmService.handleNaturalLanguageQuery(chatQuery)
      if (response.data) {
        setChatResponse(response.data.response)
      } else {
        toast.error('Failed to get response')
      }
    } catch (error) {
      console.error('Chat query error:', error)
      toast.error('Failed to process query')
    } finally {
      setIsChatLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner size="lg" />
          <span className="ml-3 text-lg text-gray-600">Generating AI insights...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <svg className="w-5 h-5 mr-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          AI Traffic Insights
        </h3>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6">
          {[
            { id: 'conditions', label: 'Traffic Analysis', icon: '📊' },
            { id: 'summary', label: 'Summary', icon: '📝' },
            { id: 'recommendations', label: 'Recommendations', icon: '💡' },
            { id: 'chat', label: 'Ask AI', icon: '💬' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center ${
                activeTab === tab.id
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {/* Traffic Conditions Analysis */}
        {activeTab === 'conditions' && (
          <div className="space-y-4">
            {insights.conditions?.data ? (
              <div className="prose max-w-none">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                  <div className="flex items-center mb-2">
                    <span className="text-blue-600 font-medium">Confidence Score:</span>
                    <span className="ml-2 text-blue-800 font-bold">
                      {(insights.conditions.data.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
                
                <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                  {insights.conditions.data.analysis}
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <p>No traffic analysis available</p>
              </div>
            )}
          </div>
        )}

        {/* Traffic Summary */}
        {activeTab === 'summary' && (
          <div className="space-y-4">
            {insights.summary?.data ? (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h4 className="font-medium text-green-800 mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Traffic Summary
                </h4>
                <div className="text-green-700 whitespace-pre-wrap leading-relaxed">
                  {insights.summary.data.summary}
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p>No summary available</p>
              </div>
            )}
          </div>
        )}

        {/* Recommendations */}
        {activeTab === 'recommendations' && (
          <div className="space-y-4">
            {insights.recommendations?.data ? (
              <div className="space-y-4">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <span className="text-yellow-600 font-medium">Confidence Score:</span>
                    <span className="ml-2 text-yellow-800 font-bold">
                      {(insights.recommendations.data.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                  <h4 className="font-medium text-orange-800 mb-3 flex items-center">
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                    Traffic Management Recommendations
                  </h4>
                  <div className="text-orange-700 whitespace-pre-wrap leading-relaxed">
                    {insights.recommendations.data.recommendations}
                  </div>
                </div>

                {/* Structured Recommendations */}
                {insights.recommendations.data.structured_recommendations?.length > 0 && (
                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <h5 className="font-medium text-gray-800 mb-3">Action Items:</h5>
                    <ul className="space-y-2">
                      {insights.recommendations.data.structured_recommendations.map((rec: any, index: number) => (
                        <li key={index} className="flex items-start">
                          <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium mr-3 mt-0.5">
                            {index + 1}
                          </span>
                          <span className="text-gray-700">{rec.action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <p>No recommendations available</p>
              </div>
            )}
          </div>
        )}

        {/* AI Chat */}
        {activeTab === 'chat' && (
          <div className="space-y-4">
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <h4 className="font-medium text-purple-800 mb-2">Ask AI about Traffic Analysis</h4>
              <p className="text-purple-600 text-sm">
                Ask questions about the current traffic analysis, vehicle detection, or get specific insights.
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex space-x-3">
                <input
                  type="text"
                  value={chatQuery}
                  onChange={(e) => setChatQuery(e.target.value)}
                  placeholder="Ask a question about the traffic analysis..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  onKeyPress={(e) => e.key === 'Enter' && handleChatQuery()}
                />
                <button
                  onClick={handleChatQuery}
                  disabled={isChatLoading || !chatQuery.trim()}
                  className="bg-purple-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {isChatLoading ? (
                    <>
                      <LoadingSpinner size="sm" className="mr-2" />
                      Asking...
                    </>
                  ) : (
                    'Ask AI'
                  )}
                </button>
              </div>

              {chatResponse && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start">
                    <div className="flex-shrink-0 w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center mr-3">
                      <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900 mb-1">AI Assistant</div>
                      <div className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                        {chatResponse}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Sample Questions */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h5 className="font-medium text-gray-800 mb-3">Sample Questions:</h5>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {[
                  "How many vehicles were detected?",
                  "What's the traffic density level?",
                  "Are there any safety concerns?",
                  "What time of day is this analysis from?",
                  "Which vehicle types are most common?",
                  "Is there any congestion detected?"
                ].map((question, index) => (
                  <button
                    key={index}
                    onClick={() => setChatQuery(question)}
                    className="text-left text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 p-2 rounded border border-blue-200 hover:border-blue-300"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}