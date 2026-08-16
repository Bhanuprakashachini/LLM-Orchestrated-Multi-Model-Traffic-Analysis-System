'use client'

import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { useEffect } from 'react'

export default function HomePage() {
  const router = useRouter()
  const { user, isLoading } = useAuth()

  // Redirect authenticated users to dashboard
  useEffect(() => {
    if (!isLoading && user) {
      router.push('/dashboard')
    }
  }, [user, isLoading, router])

  // Show loading spinner while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  // Don't render home page if user is authenticated (will redirect)
  if (user) {
    return null
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 relative overflow-hidden">
      {/* Background elements */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 right-1/4 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl animate-pulse" />
        <div 
          className="absolute bottom-1/4 left-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl animate-pulse"
          style={{ animationDelay: '1s' }}
        />
      </div>

      {/* Navigation Header */}
      <nav className="relative z-10 bg-white/80 backdrop-blur-md shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="flex items-center space-x-3">
                <div className="relative p-2 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg shadow-lg">
                  <span className="text-white text-lg">🚗</span>
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg blur-lg opacity-50"></div>
                </div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-blue-600 bg-clip-text text-transparent">
                  Traffic Analysis System
                </h1>
              </div>
            </div>
            <div className="flex space-x-4">
              <button
                onClick={() => router.push('/login')}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
              >
                Login
              </button>
              <button
                onClick={() => router.push('/register')}
                className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 rounded-lg transition-all duration-200 shadow-lg shadow-blue-500/25"
              >
                Register
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div className="text-center">
          <div className="mb-8">
            <div className="relative p-4 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl shadow-2xl mx-auto w-20 h-20 flex items-center justify-center mb-6">
              <span className="text-3xl">🚦</span>
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl blur-xl opacity-50"></div>
            </div>
          </div>
          
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Advanced Traffic Analysis
            <span className="block bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              Powered by AI
            </span>
          </h1>
          
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
            LLM Orchestrated Multi-Model Traffic Analysis System using advanced YOLO models 
            (YOLOv8, YOLOv11, YOLOv12) with enhanced accuracy configuration and intelligent insights.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
            <button
              onClick={() => router.push('/register')}
              className="px-8 py-4 text-lg font-semibold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 rounded-xl shadow-2xl shadow-blue-500/25 hover:shadow-blue-500/40 transition-all duration-200 transform hover:scale-105"
            >
              Get Started
            </button>
            <button
              onClick={() => router.push('/login')}
              className="px-8 py-4 text-lg font-semibold text-blue-600 bg-white/90 backdrop-blur-xl hover:bg-white rounded-xl shadow-xl hover:shadow-2xl transition-all duration-200 transform hover:scale-105 border-2 border-blue-200 hover:border-blue-300"
            >
              Sign In
            </button>
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mt-16">
            <div className="bg-white/90 backdrop-blur-xl rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 border border-gray-200/50">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center mb-6 mx-auto shadow-lg">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Video Analysis</h3>
              <p className="text-gray-600 leading-relaxed">
                Real-time traffic video analysis with advanced object detection and tracking capabilities using state-of-the-art AI models.
              </p>
            </div>

            <div className="bg-white/90 backdrop-blur-xl rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 border border-gray-200/50">
              <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl flex items-center justify-center mb-6 mx-auto shadow-lg">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Multi-Model AI</h3>
              <p className="text-gray-600 leading-relaxed">
                Ensemble of advanced YOLO models (v8, v11, v12) with enhanced detection accuracy and intelligent model selection for comprehensive traffic analysis.
              </p>
            </div>

            <div className="bg-white/90 backdrop-blur-xl rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 border border-gray-200/50">
              <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-600 rounded-xl flex items-center justify-center mb-6 mx-auto shadow-lg">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">LLM Insights</h3>
              <p className="text-gray-600 leading-relaxed">
                AI-powered insights and intelligent recommendations based on comprehensive traffic pattern analysis and machine learning.
              </p>
            </div>
          </div>

          {/* Additional Features */}
          <div className="mt-16 bg-white/90 backdrop-blur-xl rounded-2xl p-8 shadow-xl border border-gray-200/50">
            <h3 className="text-2xl font-bold text-gray-900 mb-6">Why Choose Traffic Analysis?</h3>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center mb-4 mx-auto">
                  <span className="text-white text-xl">🎯</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Enhanced Accuracy</h4>
                <p className="text-sm text-gray-600">Optimized detection thresholds for comprehensive analysis</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-600 rounded-lg flex items-center justify-center mb-4 mx-auto">
                  <span className="text-white text-xl">⚡</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Real-time Processing</h4>
                <p className="text-sm text-gray-600">Fast analysis with instant results and feedback</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-600 rounded-lg flex items-center justify-center mb-4 mx-auto">
                  <span className="text-white text-xl">🧠</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Smart Analytics</h4>
                <p className="text-sm text-gray-600">LLM-powered insights and intelligent recommendations</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-red-600 rounded-lg flex items-center justify-center mb-4 mx-auto">
                  <span className="text-white text-xl">📊</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Detailed Reports</h4>
                <p className="text-sm text-gray-600">Comprehensive analysis reports and data export</p>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 bg-white/80 backdrop-blur-md border-t border-gray-200 mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-3 mb-4">
              <div className="relative p-2 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg shadow-lg">
                <span className="text-white text-sm">🚗</span>
              </div>
              <span className="text-lg font-bold bg-gradient-to-r from-gray-900 to-blue-600 bg-clip-text text-transparent">
                Traffic Analysis System
              </span>
            </div>
            <p className="text-sm text-gray-500">
              LLM Orchestrated Multi Model Traffic Analysis • Secure • Reliable • AI-Powered
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}