'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'

export default function DashboardPage() {
  const { user, logout } = useAuth()
  const router = useRouter()

  const features = [
    {
      id: 'video-analysis',
      title: 'Video Traffic Analysis',
      description: 'Upload videos for comprehensive vehicle tracking and traffic analysis with frame-by-frame detection.',
      icon: '🎥',
      color: 'from-purple-500 to-purple-600'
    },
    {
      id: 'upload',
      title: 'Image / Video Upload Module',
      description: 'Upload traffic images or videos for comprehensive AI-powered analysis using advanced YOLO models.',
      icon: '📤',
      color: 'from-blue-500 to-blue-600'
    },
    {
      id: 'vehicle-detection',
      title: 'Vehicle Detection Module',
      description: 'Detect and classify vehicles (cars, bikes, buses, trucks) with bounding boxes and confidence scores.',
      icon: '🚗',
      color: 'from-green-500 to-green-600'
    },
    {
      id: 'enhanced-analysis',
      title: 'Enhanced Analysis Engine',
      description: 'Advanced multi-model analysis with improved accuracy and comprehensive vehicle tracking capabilities.',
      icon: '🔄',
      color: 'from-emerald-500 to-emerald-600'
    },
    {
      id: 'comprehensive-comparison',
      title: 'Comprehensive Model Comparison',
      description: 'Compare multiple YOLO models with detailed performance metrics and accuracy assessment.',
      icon: '📊',
      color: 'from-teal-500 to-teal-600'
    },
    {
      id: 'traffic-density',
      title: 'Traffic Density Analysis',
      description: 'Calculate traffic density levels, congestion detection, and flow analysis with AI-powered insights.',
      icon: '📈',
      color: 'from-orange-500 to-orange-600'
    },
    {
      id: 'ai-insights',
      title: 'AI-Powered Scene Analysis',
      description: 'Advanced scene understanding with weather detection, lighting analysis, and intelligent recommendations.',
      icon: '🧠',
      color: 'from-indigo-500 to-indigo-600'
    },
    {
      id: 'visualization',
      title: 'Visualization Dashboard',
      description: 'View detection results with annotated images, bounding boxes, and interactive traffic analysis charts.',
      icon: '📈',
      color: 'from-pink-500 to-pink-600'
    },
    {
      id: 'performance',
      title: 'Performance Metrics Panel',
      description: 'Monitor accuracy, precision, recall, F1-score, and processing speed (FPS) for detection models.',
      icon: '⚙️',
      color: 'from-gray-500 to-gray-600'
    },
    {
      id: 'history',
      title: 'History & Reports Module',
      description: 'Access past analysis results and download detailed reports in CSV or JSON format.',
      icon: '📋',
      color: 'from-slate-500 to-slate-600'
    },
    {
      id: 'user-analytics',
      title: 'User Analytics Dashboard',
      description: 'Personal analytics with trends, statistics, and comprehensive analysis history tracking.',
      icon: '📊',
      color: 'from-blue-500 to-blue-600'
    },
    {
      id: 'advanced-features',
      title: 'Advanced Traffic Features',
      description: 'AI scene analysis, weather detection, and enhanced traffic monitoring capabilities.',
      icon: '🚦',
      color: 'from-green-500 to-green-600'
    }
  ]

  // Features are for display/reading only - no click functionality needed

  const handleUploadClick = () => {
    router.push('/upload')
  }

  return (
    <div className="min-h-screen" style={{
      background: 'linear-gradient(135deg, #f3e8ff 0%, #ffffff 50%, #f3e8ff 100%)'
    }}>
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-blue-200">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-blue-700">TrafficAI Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              {/* User Info */}
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
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
                  <p className="text-gray-500">{user?.email || 'No email provided'}</p>
                </div>
              </div>
              {/* Logout Button */}
              <button
                onClick={logout}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Welcome Section */}
          <div className="text-white rounded-2xl p-8" style={{
            background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)'
          }}>
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-3xl font-bold mb-2">
                  Welcome back, {user?.first_name || user?.username || 'User'}!
                </h2>
                <p className="text-blue-100 text-lg">LLM Orchestrated Multi Model Traffic Analysis System</p>
                <p className="text-blue-200 text-sm mt-2">Advanced AI-powered traffic monitoring and analysis platform</p>
              </div>
              <div className="hidden md:block">
                <div className="w-24 h-24 text-blue-300 text-6xl">🚦</div>
              </div>
            </div>
          </div>

          {/* Project Overview */}
          <div className="bg-white rounded-xl shadow-sm border border-blue-200 p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">🚀 What This Application Does - Key Features</h3>
            <div className="text-gray-700 space-y-4">
              <div className="bg-gradient-to-r from-blue-50 to-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
                <h4 className="font-semibold text-blue-800 mb-2">🎯 Core Purpose</h4>
                <p><strong>Advanced AI-Powered Traffic Analysis System</strong> that uses cutting-edge deep learning models to analyze traffic images and videos in real-time, providing comprehensive insights for traffic management and urban planning.</p>
              </div>
              
              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-green-50 p-4 rounded-lg border-l-4 border-green-500">
                  <h4 className="font-semibold text-green-800 mb-2">🤖 AI Technology</h4>
                  <ul className="text-sm space-y-1">
                    <li>• <strong>Advanced YOLO Models</strong> - YOLOv8, YOLOv11, YOLOv12 variants</li>
                    <li>• <strong>Enhanced Detection</strong> - Optimized confidence thresholds</li>
                    <li>• <strong>Multi-Model Analysis</strong> - Comprehensive comparison capabilities</li>
                    <li>• <strong>AI Scene Understanding</strong> - Weather and lighting detection</li>
                    <li>• <strong>LLM Integration</strong> - Intelligent insights and recommendations</li>
                  </ul>
                </div>
                
                <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
                  <h4 className="font-semibold text-blue-800 mb-2">🚗 Vehicle Detection</h4>
                  <ul className="text-sm space-y-1">
                    <li>• <strong>Multi-Vehicle Types</strong> - Cars, buses, trucks, motorcycles, bicycles</li>
                    <li>• <strong>Accurate Counting</strong> - Precise vehicle enumeration</li>
                    <li>• <strong>Confidence Scoring</strong> - Reliability assessment for each detection</li>
                    <li>• <strong>Bounding Boxes</strong> - Visual detection markers and annotations</li>
                    <li>• <strong>Enhanced Tracking</strong> - Advanced vehicle tracking capabilities</li>
                  </ul>
                </div>
                
                <div className="bg-orange-50 p-4 rounded-lg border-l-4 border-orange-500">
                  <h4 className="font-semibold text-orange-800 mb-2">📊 Traffic Analysis</h4>
                  <ul className="text-sm space-y-1">
                    <li>• <strong>Density Estimation</strong> - Low, Medium, High, Congested levels</li>
                    <li>• <strong>Flow Analysis</strong> - Traffic movement and pattern detection</li>
                    <li>• <strong>Congestion Detection</strong> - Real-time bottleneck identification</li>
                    <li>• <strong>Performance Metrics</strong> - Accuracy, precision, recall, F1-score</li>
                    <li>• <strong>Scene Analysis</strong> - Weather and environmental conditions</li>
                  </ul>
                </div>
                
                <div className="bg-purple-50 p-4 rounded-lg border-l-4 border-purple-500">
                  <h4 className="font-semibold text-purple-800 mb-2">📈 Smart Features</h4>
                  <ul className="text-sm space-y-1">
                    <li>• <strong>User Analytics</strong> - Personal analysis history and trends</li>
                    <li>• <strong>Report Generation</strong> - CSV/JSON export capabilities</li>
                    <li>• <strong>Visual Dashboard</strong> - Interactive charts and visualizations</li>
                    <li>• <strong>Secure Access</strong> - User authentication and data privacy</li>
                    <li>• <strong>Video Analysis</strong> - Comprehensive video processing support</li>
                  </ul>
                </div>
              </div>
              
              <div className="bg-gradient-to-r from-indigo-50 to-blue-50 p-4 rounded-lg border-l-4 border-indigo-500">
                <h4 className="font-semibold text-indigo-800 mb-2">� Maain Benefits & Applications</h4>
                <div className="grid md:grid-cols-3 gap-4 mt-3">
                  <div>
                    <h5 className="font-medium text-indigo-700">🏙️ Urban Planning</h5>
                    <p className="text-sm">Traffic flow optimization, infrastructure planning, smart city development</p>
                  </div>
                  <div>
                    <h5 className="font-medium text-indigo-700">🚦 Traffic Management</h5>
                    <p className="text-sm">Real-time monitoring, congestion alerts, signal optimization</p>
                  </div>
                  <div>
                    <h5 className="font-medium text-indigo-700">📊 Data Analytics</h5>
                    <p className="text-sm">Historical analysis, trend identification, performance reporting</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-yellow-50 p-4 rounded-lg border-l-4 border-yellow-500">
                <h4 className="font-semibold text-yellow-800 mb-2">⚡ Why This System is Powerful</h4>
                <p className="text-sm">Unlike traditional traffic monitoring systems, this AI-powered solution provides <strong>instant analysis</strong>, <strong>multi-model accuracy</strong>, and <strong>intelligent insights</strong> that help make data-driven decisions for traffic management, urban planning, and infrastructure development. Each user gets personalized analytics based on their own uploaded data and analysis history. The system now focuses on core vehicle detection and AI-powered scene analysis with enhanced accuracy and performance.</p>
              </div>
            </div>
          </div>

          {/* Features Grid */}
          <div className="bg-white rounded-xl shadow-sm border border-blue-200 p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-6">System Features & Modules</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {features.map((feature) => (
                <div
                  key={feature.id}
                  className="bg-gradient-to-br from-gray-50 to-white border border-gray-200 rounded-xl p-6 hover:shadow-md transition-all duration-300"
                >
                  <div className="flex items-start space-x-4">
                    <div className={`p-3 rounded-lg bg-gradient-to-r ${feature.color} text-white text-xl flex-shrink-0`}>
                      {feature.icon}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-gray-900">{feature.title}</h4>
                        <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">Feature</span>
                      </div>
                      <p className="text-sm text-gray-600 leading-relaxed">{feature.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Upload Feature */}
          <div className="bg-white rounded-xl shadow-sm border border-blue-200 p-8">
            <div className="text-center">
              <div className="text-6xl mb-4">📤</div>
              <h3 className="text-2xl font-semibold text-gray-900 mb-4">Upload & Analyze Traffic Data</h3>
              <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
                Upload your traffic images or videos to get comprehensive AI-powered analysis including vehicle detection, 
                traffic density estimation, and detailed reporting using advanced YOLO models with enhanced accuracy and intelligent scene understanding.
              </p>
              <button 
                onClick={handleUploadClick}
                className="text-white py-4 px-8 rounded-xl font-medium text-lg transition-all duration-200 hover:shadow-lg transform hover:scale-105"
                style={{
                  background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)'
                }}
              >
                Start Analysis - Upload File
              </button>
            </div>
          </div>

          {/* Traffic Violation Detection Feature */}
          <div className="bg-white rounded-xl shadow-sm border border-red-200 p-8">
            <div className="text-center">
              <div className="text-6xl mb-4">🚦</div>
              <h3 className="text-2xl font-semibold text-gray-900 mb-4">Traffic Violation Detection</h3>
              <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
                Real-time traffic violation detection system with speed monitoring, helmet detection, and comprehensive violation tracking. 
                Features guaranteed speed display for all vehicles using advanced YOLO models (YOLOv8s, YOLOv11s, YOLOv12s).
              </p>
              
              {/* Feature Highlights */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-red-50 rounded-lg p-3 border border-red-200">
                  <div className="text-2xl mb-1">⚡</div>
                  <div className="text-sm font-semibold text-red-900">Guaranteed Speed</div>
                  <div className="text-xs text-red-700">ALL vehicles show speeds</div>
                </div>
                <div className="bg-orange-50 rounded-lg p-3 border border-orange-200">
                  <div className="text-2xl mb-1">🏍️</div>
                  <div className="text-sm font-semibold text-orange-900">Helmet Detection</div>
                  <div className="text-xs text-orange-700">6 detection methods</div>
                </div>
                <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                  <div className="text-2xl mb-1">🤖</div>
                  <div className="text-sm font-semibold text-blue-900">3 YOLO Models</div>
                  <div className="text-xs text-blue-700">v8s, v11s, v12s</div>
                </div>
                <div className="bg-green-50 rounded-lg p-3 border border-green-200">
                  <div className="text-2xl mb-1">📊</div>
                  <div className="text-sm font-semibold text-green-900">Real-Time Stats</div>
                  <div className="text-xs text-green-700">Live violation tracking</div>
                </div>
              </div>

              <button 
                onClick={() => router.push('/traffic-violations')}
                className="text-white py-4 px-8 rounded-xl font-medium text-lg transition-all duration-200 hover:shadow-lg transform hover:scale-105"
                style={{
                  background: 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)'
                }}
              >
                🚗 Start Traffic Detection
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}