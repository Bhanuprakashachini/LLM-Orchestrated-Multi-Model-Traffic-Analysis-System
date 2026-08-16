'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  CloudArrowUpIcon,
  ChartBarIcon,
  ClockIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline'
import VideoUpload from '@/components/VideoUpload'
import VideoMetrics from '@/components/VideoMetrics'
import VideoHistory from '@/components/VideoHistory'

type TabType = 'upload' | 'metrics' | 'history'

const VideoAnalysisPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('upload')
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string | null>(null)

  const tabs = [
    {
      id: 'upload' as TabType,
      name: 'Upload Video',
      icon: CloudArrowUpIcon,
      description: 'Upload and analyze traffic videos'
    },
    {
      id: 'metrics' as TabType,
      name: 'View Metrics',
      icon: ChartBarIcon,
      description: 'Detailed analysis metrics and visualizations'
    },
    {
      id: 'history' as TabType,
      name: 'Analysis History',
      icon: DocumentTextIcon,
      description: 'View past video analysis results'
    }
  ]

  const handleAnalysisComplete = (results: any) => {
    setSelectedAnalysisId(results.analysis_id)
    setActiveTab('metrics')
  }

  const handleViewMetrics = (analysisId: string) => {
    setSelectedAnalysisId(analysisId)
    setActiveTab('metrics')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                🎥 Video Traffic Analysis
              </h1>
              <p className="text-gray-600 mt-1">
                Comprehensive vehicle detection, tracking, and traffic metrics for video files
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>System Online</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="bg-white rounded-lg shadow-sm p-2 mb-6">
          <div className="flex space-x-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-3 px-6 py-3 rounded-md transition-all duration-200 ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <tab.icon className="w-5 h-5" />
                <div className="text-left">
                  <div className="font-medium">{tab.name}</div>
                  <div className={`text-xs ${
                    activeTab === tab.id ? 'text-blue-100' : 'text-gray-500'
                  }`}>
                    {tab.description}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            {activeTab === 'upload' && (
              <div className="bg-white rounded-lg shadow-sm">
                <VideoUpload onAnalysisComplete={handleAnalysisComplete} />
              </div>
            )}

            {activeTab === 'metrics' && (
              <div className="bg-white rounded-lg shadow-sm">
                {selectedAnalysisId ? (
                  <VideoMetrics analysisId={selectedAnalysisId} />
                ) : (
                  <div className="p-12 text-center">
                    <ChartBarIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      No Analysis Selected
                    </h3>
                    <p className="text-gray-600 mb-6">
                      Upload a video or select an analysis from history to view metrics
                    </p>
                    <div className="flex justify-center space-x-4">
                      <button
                        onClick={() => setActiveTab('upload')}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        Upload Video
                      </button>
                      <button
                        onClick={() => setActiveTab('history')}
                        className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                      >
                        View History
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'history' && (
              <div className="bg-white rounded-lg shadow-sm">
                <VideoHistory onViewMetrics={handleViewMetrics} />
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Features Overview */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Advanced Video Analysis Features
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Our comprehensive video analysis system provides detailed insights into traffic patterns, 
            vehicle behavior, and congestion metrics.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            {
              icon: '🚗',
              title: 'Vehicle Detection',
              description: 'Real-time detection and classification of vehicles using advanced YOLO models'
            },
            {
              icon: '📊',
              title: 'Traffic Density',
              description: 'Comprehensive analysis of traffic density and congestion levels over time'
            },
            {
              icon: '🎯',
              title: 'Object Tracking',
              description: 'Track individual vehicles across frames to prevent duplicate counting'
            },
            {
              icon: '🔄',
              title: 'Model Comparison',
              description: 'Compare YOLOv8 and YOLOv12 performance to select the best model'
            },
            {
              icon: '📈',
              title: 'Metrics & Reports',
              description: 'Detailed analytics with exportable reports in JSON and CSV formats'
            },
            {
              icon: '🎥',
              title: 'Video Visualization',
              description: 'Generate annotated videos with bounding boxes and detection results'
            },
            {
              icon: '📱',
              title: 'History & Storage',
              description: 'Store and manage all your video analysis results with MongoDB'
            }
          ].map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white rounded-lg shadow-sm p-6 text-center hover:shadow-md transition-shadow"
            >
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-600 text-sm">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Technical Specifications */}
      <div className="bg-gray-50 py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Technical Specifications
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Supported Formats
              </h3>
              <ul className="space-y-2 text-gray-600">
                <li>• MP4 (recommended)</li>
                <li>• AVI</li>
                <li>• MOV</li>
                <li>• MKV</li>
                <li>• WMV</li>
                <li>• FLV</li>
              </ul>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Processing Capabilities
              </h3>
              <ul className="space-y-2 text-gray-600">
                <li>• Max file size: 100MB</li>
                <li>• Frame sampling: 1-10 frames</li>
                <li>• Confidence threshold: 0.1-1.0</li>
                <li>• Multi-model comparison</li>
                <li>• Real-time processing</li>
                <li>• GPU acceleration</li>
              </ul>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Output Features
              </h3>
              <ul className="space-y-2 text-gray-600">
                <li>• Annotated video output</li>
                <li>• JSON/CSV reports</li>
                <li>• Interactive visualizations</li>
                <li>• Historical data storage</li>
                <li>• Performance metrics</li>
                <li>• LLM-generated insights</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default VideoAnalysisPage