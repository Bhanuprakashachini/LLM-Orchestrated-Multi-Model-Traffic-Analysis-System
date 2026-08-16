'use client'

import React, { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import toast from 'react-hot-toast'

interface AdvancedFeaturesProps {
  analysisData?: any
  onFeatureToggle?: (feature: string, enabled: boolean) => void
}

interface FeatureStatus {
  available: boolean
  description: string
  capabilities: string[]
}

interface FeaturesStatus {
  ai_processing_engine: FeatureStatus
  system_requirements: {
    gpu_acceleration: string
    memory_requirement: string
    processing_time: string
    supported_formats: string[]
  }
}

export default function AdvancedFeatures({ analysisData, onFeatureToggle }: AdvancedFeaturesProps) {
  const { user } = useAuth()
  const [featuresStatus, setFeaturesStatus] = useState<FeaturesStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [enabledFeatures, setEnabledFeatures] = useState({
    ai_processing: true
  })

  useEffect(() => {
    fetchFeaturesStatus()
  }, [])

  const fetchFeaturesStatus = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) return

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/analysis/advanced/features-status/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const data = await response.json()
        setFeaturesStatus(data.features_status)
      }
    } catch (error) {
      console.error('Error fetching features status:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFeatureToggle = (feature: string, enabled: boolean) => {
    setEnabledFeatures(prev => ({
      ...prev,
      [feature]: enabled
    }))
    onFeatureToggle?.(feature, enabled)
  }

  const renderAIProcessingEngine = () => {
    if (!analysisData?.scene_analysis) return null

    const sceneData = analysisData.scene_analysis
    const aiInsights = analysisData.ai_insights || {}

    return (
      <div className="bg-white rounded-lg shadow-lg p-6 border-l-4 border-purple-500">
        <div className="flex items-center mb-4">
          <div className="p-3 rounded-lg bg-gradient-to-r from-purple-500 to-purple-600 text-white text-xl mr-4">
            🧠
          </div>
          <div>
            <h3 className="text-xl font-semibold text-purple-800">AI Processing Engine</h3>
            <p className="text-gray-600">Advanced deep learning analysis</p>
          </div>
        </div>

        {/* Scene Analysis */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
            <h4 className="font-semibold text-purple-800 mb-2">🏞️ Scene Classification</h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-700">Scene Type:</span>
                <span className="text-sm font-medium text-purple-700 capitalize">
                  {sceneData.scene_type || 'Unknown'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-700">Complexity:</span>
                <span className="text-sm font-medium text-purple-700 capitalize">
                  {sceneData.scene_complexity || 'Medium'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-700">Visibility:</span>
                <span className="text-sm font-medium text-purple-700">
                  {((sceneData.visibility_score || 0) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <h4 className="font-semibold text-blue-800 mb-2">🌤️ Weather Detection</h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-700">Condition:</span>
                <span className="text-sm font-medium text-blue-700 capitalize">
                  {sceneData.weather_condition || 'Clear'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-700">Time of Day:</span>
                <span className="text-sm font-medium text-blue-700 capitalize">
                  {sceneData.time_of_day || 'Unknown'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-700">Lighting:</span>
                <span className="text-sm font-medium text-blue-700 capitalize">
                  {sceneData.lighting_quality || 'Good'}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-green-50 p-4 rounded-lg border border-green-200">
            <h4 className="font-semibold text-green-800 mb-2">🎯 AI Confidence</h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-700">Overall Score:</span>
                <span className="text-sm font-medium text-green-700">
                  {((aiInsights.confidence_score || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-700">Risk Level:</span>
                <span className={`text-sm font-medium capitalize ${
                  aiInsights.risk_assessment === 'high' ? 'text-red-700' :
                  aiInsights.risk_assessment === 'medium' ? 'text-yellow-700' : 'text-green-700'
                }`}>
                  {aiInsights.risk_assessment || 'Low'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* AI Insights */}
        {aiInsights.key_findings && aiInsights.key_findings.length > 0 && (
          <div className="mb-4">
            <h4 className="font-semibold text-gray-800 mb-3">🔍 Key Findings</h4>
            <div className="bg-gray-50 p-4 rounded-lg">
              <ul className="space-y-2">
                {aiInsights.key_findings.map((finding: string, index: number) => (
                  <li key={index} className="flex items-start">
                    <span className="text-purple-600 mr-2">•</span>
                    <span className="text-sm text-gray-700">{finding}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Recommendations */}
        {aiInsights.recommendations && aiInsights.recommendations.length > 0 && (
          <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-4 rounded-lg border border-purple-200">
            <h4 className="font-semibold text-purple-800 mb-3">💡 AI Recommendations</h4>
            <ul className="space-y-2">
              {aiInsights.recommendations.map((recommendation: string, index: number) => (
                <li key={index} className="flex items-start">
                  <span className="text-purple-600 mr-2">→</span>
                  <span className="text-sm text-purple-700">{recommendation}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    )
  }

  const renderRemovedFeatureNotice = () => {
    return (
      <div className="bg-yellow-50 rounded-lg shadow-lg p-6 border-l-4 border-yellow-500">
        <div className="flex items-center mb-4">
          <div className="p-3 rounded-lg bg-yellow-500 text-white text-xl mr-4">
            ⚠️
          </div>
          <div>
            <h3 className="text-xl font-semibold text-yellow-800">Lane Analysis Feature</h3>
            <p className="text-gray-600">This feature has been removed from the system</p>
          </div>
        </div>
        <div className="bg-yellow-100 p-4 rounded-lg border border-yellow-200">
          <p className="text-sm text-yellow-800">
            Lane analysis functionality has been removed per user request. 
            The system now focuses on vehicle detection and AI-powered scene analysis.
          </p>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Feature Status Overview */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">🚀 Advanced Traffic Analysis Features</h2>
        
        {featuresStatus && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
              <div className="flex items-center mb-2">
                <span className="text-2xl mr-2">🧠</span>
                <h3 className="font-semibold text-purple-800">AI Processing Engine</h3>
              </div>
              <p className="text-sm text-purple-700 mb-2">{featuresStatus.ai_processing_engine.description}</p>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={enabledFeatures.ai_processing}
                  onChange={(e) => handleFeatureToggle('ai_processing', e.target.checked)}
                  className="mr-2"
                />
                <span className="text-sm text-purple-600">Enable AI Analysis</span>
              </div>
            </div>

            <div className="bg-gradient-to-br from-gray-50 to-gray-100 p-4 rounded-lg border border-gray-200">
              <div className="flex items-center mb-2">
                <span className="text-2xl mr-2">🛣️</span>
                <h3 className="font-semibold text-gray-600">Lane Analysis</h3>
              </div>
              <p className="text-sm text-gray-600 mb-2">Feature removed per user request</p>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={false}
                  disabled={true}
                  className="mr-2 opacity-50"
                />
                <span className="text-sm text-gray-500">No longer available</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Feature Results */}
      {analysisData && (
        <div className="space-y-6">
          {enabledFeatures.ai_processing && renderAIProcessingEngine()}
          {renderRemovedFeatureNotice()}
        </div>
      )}
    </div>
  )
}