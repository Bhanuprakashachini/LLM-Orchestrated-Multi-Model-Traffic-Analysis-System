'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import TrafficViolationDetector from './components/TrafficViolationDetector'

export default function TrafficViolationsPage() {
  const { user, logout } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (user === null) {
      router.push('/login')
    }
  }, [user, router])

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <button
            onClick={() => router.push('/dashboard')}
            className="text-gray-600 hover:text-gray-900 flex items-center"
          >
            ← Dashboard
          </button>
          <div className="flex items-center space-x-3">
            <div className="text-2xl">🚦</div>
            <h1 className="text-xl font-semibold text-gray-900">Traffic Violation Detection</h1>
          </div>
          <button
            onClick={logout}
            className="text-red-600 hover:text-red-700"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8">
          <div className="text-center mb-6">
            <div className="text-4xl mb-3">🚗🏍️🚌🚛</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Real-Time Traffic Violation Detection
            </h2>
            <p className="text-gray-600 max-w-3xl mx-auto">
              Advanced AI-powered system for detecting speed violations, helmet violations, and traffic infractions. 
              Upload a video and watch real-time analysis with guaranteed speed display for all vehicles.
            </p>
          </div>

          {/* Feature Highlights */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-lg p-4 border border-green-200 text-center">
              <div className="text-2xl mb-2">⚡</div>
              <h3 className="font-semibold text-green-900">Guaranteed Speed</h3>
              <p className="text-sm text-green-700">ALL vehicles show speeds</p>
            </div>
            <div className="bg-white rounded-lg p-4 border border-blue-200 text-center">
              <div className="text-2xl mb-2">🤖</div>
              <h3 className="font-semibold text-blue-900">3 YOLO Models</h3>
              <p className="text-sm text-blue-700">YOLOv8s, v11s, v12s</p>
            </div>
            <div className="bg-white rounded-lg p-4 border border-orange-200 text-center">
              <div className="text-2xl mb-2">🏍️</div>
              <h3 className="font-semibold text-orange-900">Helmet Detection</h3>
              <p className="text-sm text-orange-700">6 detection methods</p>
            </div>
            <div className="bg-white rounded-lg p-4 border border-red-200 text-center">
              <div className="text-2xl mb-2">📊</div>
              <h3 className="font-semibold text-red-900">Real-Time Stats</h3>
              <p className="text-sm text-red-700">Live violation tracking</p>
            </div>
          </div>
        </div>

        {/* Main Detection Interface */}
        <TrafficViolationDetector />
      </main>
    </div>
  )
}