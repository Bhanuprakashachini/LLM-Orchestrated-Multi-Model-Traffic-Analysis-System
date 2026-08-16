'use client'

import { useState, useEffect } from 'react'

interface Violation {
  type: string
  timestamp: string
  vehicle_type: string
  speed?: number
  speed_limit?: number
  excess_speed?: number
  confidence: number
  details: any
}

interface ViolationPopupProps {
  violation: Violation | null
  onClose: () => void
}

export default function ViolationPopup({ violation, onClose }: ViolationPopupProps) {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    if (violation) {
      setIsVisible(true)
      
      // Auto-hide after 5 seconds
      const timer = setTimeout(() => {
        setIsVisible(false)
        setTimeout(onClose, 300) // Wait for animation to complete
      }, 5000)

      return () => clearTimeout(timer)
    }
  }, [violation, onClose])

  if (!violation) return null

  const getViolationIcon = (type: string) => {
    switch (type) {
      case 'OVERSPEEDING':
        return '🚗💨'
      case 'NO_HELMET':
        return '🏍️⚠️'
      case 'RED_LIGHT_VIOLATION':
        return '🚦❌'
      default:
        return '⚠️'
    }
  }

  const getViolationTitle = (type: string) => {
    switch (type) {
      case 'OVERSPEEDING':
        return 'SPEED VIOLATION DETECTED!'
      case 'NO_HELMET':
        return 'HELMET VIOLATION DETECTED!'
      case 'RED_LIGHT_VIOLATION':
        return 'RED LIGHT VIOLATION!'
      default:
        return 'TRAFFIC VIOLATION!'
    }
  }

  const getViolationColor = (type: string) => {
    switch (type) {
      case 'OVERSPEEDING':
        return 'from-red-500 to-red-600'
      case 'NO_HELMET':
        return 'from-orange-500 to-orange-600'
      case 'RED_LIGHT_VIOLATION':
        return 'from-purple-500 to-purple-600'
      default:
        return 'from-gray-500 to-gray-600'
    }
  }

  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp)
      return date.toLocaleTimeString('en-US', { 
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    } catch {
      return timestamp
    }
  }

  return (
    <div className={`fixed top-4 right-4 z-50 transition-all duration-300 transform ${
      isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'
    }`}>
      <div className={`bg-gradient-to-r ${getViolationColor(violation.type)} text-white rounded-lg shadow-2xl border-2 border-white max-w-sm`}>
        {/* Header */}
        <div className="px-4 py-3 border-b border-white/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-2xl">{getViolationIcon(violation.type)}</span>
              <span className="font-bold text-sm">VIOLATION ALERT</span>
            </div>
            <button
              onClick={() => {
                setIsVisible(false)
                setTimeout(onClose, 300)
              }}
              className="text-white/80 hover:text-white text-xl leading-none"
            >
              ×
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="px-4 py-3">
          <div className="font-bold text-lg mb-2">
            {getViolationTitle(violation.type)}
          </div>
          
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>Vehicle:</span>
              <span className="font-semibold">{violation.vehicle_type.toUpperCase()}</span>
            </div>
            
            <div className="flex justify-between">
              <span>Time:</span>
              <span className="font-semibold">{formatTime(violation.timestamp)}</span>
            </div>
            
            {violation.type === 'OVERSPEEDING' && violation.speed && (
              <>
                <div className="flex justify-between">
                  <span>Speed:</span>
                  <span className="font-bold text-yellow-200">{violation.speed.toFixed(1)} km/h</span>
                </div>
                <div className="flex justify-between">
                  <span>Limit:</span>
                  <span className="font-semibold">{violation.speed_limit} km/h</span>
                </div>
                <div className="flex justify-between">
                  <span>Excess:</span>
                  <span className="font-bold text-yellow-200">+{violation.excess_speed?.toFixed(1)} km/h</span>
                </div>
              </>
            )}
            
            {violation.type === 'NO_HELMET' && (
              <div className="text-center py-2">
                <span className="font-semibold">Motorcycle rider without helmet detected</span>
              </div>
            )}
            
            <div className="flex justify-between">
              <span>Confidence:</span>
              <span className="font-semibold">{(violation.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-4 py-2 bg-black/20 rounded-b-lg">
          <div className="text-xs text-center text-white/80">
            🚨 Traffic Violation Detection System
          </div>
        </div>
      </div>
    </div>
  )
}