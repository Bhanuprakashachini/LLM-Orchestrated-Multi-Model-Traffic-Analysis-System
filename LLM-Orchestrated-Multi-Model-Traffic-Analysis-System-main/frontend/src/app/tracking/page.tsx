'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'

export default function TrackingPage() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="px-6 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            📊 Object Tracking
          </h1>
          <p className="text-gray-600 mt-1">
            Track vehicles across frames with unique IDs and prevent duplicate counting
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <div className="max-w-6xl mx-auto">
          {/* Feature Overview */}
          <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Object Tracking Capabilities
            </h2>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center p-4 bg-teal-50 rounded-lg">
                <div className="text-3xl mb-2">🎯</div>
                <h3 className="font-semibold text-teal-800">Cross-Frame Tracking</h3>
                <p className="text-sm text-teal-600 mt-2">
                  Follow vehicles as they move across multiple video frames
                </p>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <div className="text-3xl mb-2">🔢</div>
                <h3 className="font-semibold text-orange-800">Duplicate Prevention</h3>
                <p className="text-sm text-orange-600 mt-2">
                  Intelligent algorithms prevent counting the same vehicle multiple times
                </p>
              </div>
              <div className="text-center p-4 bg-indigo-50 rounded-lg">
                <div className="text-3xl mb-2">🏷️</div>
                <h3 className="font-semibold text-indigo-800">Unique Vehicle IDs</h3>
                <p className="text-sm text-indigo-600 mt-2">
                  Each detected vehicle gets a unique identifier for precise tracking
                </p>
              </div>
            </div>
          </div>

          {/* Tracking Algorithms */}
          <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Tracking Algorithms & Methods
            </h2>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="p-4 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg border-l-4 border-blue-500">
                <h3 className="font-semibold text-blue-800 mb-2">DeepSORT Integration</h3>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Kalman filter for motion prediction</li>
                  <li>• Deep appearance descriptor</li>
                  <li>• Hungarian algorithm for assignment</li>
                  <li>• Track lifecycle management</li>
                </ul>
              </div>
              <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border-l-4 border-green-500">
                <h3 className="font-semibold text-green-800 mb-2">YOLO + Tracking</h3>
                <ul className="text-sm text-green-700 space-y-1">
                  <li>• Real-time detection with YOLO</li>
                  <li>• Bounding box association</li>
                  <li>• Confidence-based filtering</li>
                  <li>• Multi-class vehicle tracking</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Coming Soon Notice */}
          <div className="bg-gradient-to-r from-teal-500 to-cyan-600 text-white rounded-xl p-8 text-center">
            <div className="text-6xl mb-4">🚧</div>
            <h2 className="text-2xl font-bold mb-4">Object Tracking Module</h2>
            <p className="text-lg mb-6">
              Advanced multi-object tracking system is currently in development.
            </p>
            <div className="bg-white/20 rounded-lg p-4 max-w-2xl mx-auto">
              <h3 className="font-semibold mb-2">Planned Features:</h3>
              <ul className="text-left space-y-1">
                <li>• DeepSORT tracking algorithm</li>
                <li>• Unique vehicle ID assignment</li>
                <li>• Cross-frame trajectory visualization</li>
                <li>• Duplicate counting prevention</li>
                <li>• Track persistence and recovery</li>
                <li>• Multi-class tracking support</li>
              </ul>
            </div>
            <button 
              className="mt-6 bg-white text-teal-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
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