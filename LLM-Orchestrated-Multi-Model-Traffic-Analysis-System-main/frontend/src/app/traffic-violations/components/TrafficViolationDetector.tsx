'use client'

import { useState, useEffect, useRef } from 'react'
import toast from 'react-hot-toast'
import VideoUploadArea from './VideoUploadArea'
import SpeedSettings from './SpeedSettings'
import LiveVideoStream from './LiveVideoStream'
import ViolationStats from './ViolationStats'
import ViolationHistory from './ViolationHistory'
import ViolationPopup from './ViolationPopup'

interface DetectionSettings {
  speed_limit: number
  model_name: string
  confidence_threshold: number
  video_path: string
}

interface ViolationStats {
  total_violations: number
  speed_violations: number
  helmet_violations: number
  vehicle_counts: {
    cars: number
    bikes: number
    buses: number
    trucks: number
    total: number
  }
}

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

export default function TrafficViolationDetector() {
  const [isDetecting, setIsDetecting] = useState(false)
  const [selectedVideo, setSelectedVideo] = useState<string>('')
  const [availableVideos, setAvailableVideos] = useState<any[]>([])
  const [settings, setSettings] = useState<DetectionSettings>({
    speed_limit: 50,
    model_name: 'yolov8s',
    confidence_threshold: 0.15,  // Updated to match improved backend
    video_path: ''
  })
  const [currentFrame, setCurrentFrame] = useState<string | null>(null)
  const [violationStats, setViolationStats] = useState<ViolationStats>({
    total_violations: 0,
    speed_violations: 0,
    helmet_violations: 0,
    vehicle_counts: {
      cars: 0,
      bikes: 0,
      buses: 0,
      trucks: 0,
      total: 0
    }
  })
  const [recentViolations, setRecentViolations] = useState<Violation[]>([])
  const [availableModels, setAvailableModels] = useState<string[]>(['yolov8s', 'yolo11s', 'yolo12s'])
  const [currentViolationPopup, setCurrentViolationPopup] = useState<Violation | null>(null)

  const framePollingRef = useRef<NodeJS.Timeout | null>(null)
  const violationPollingRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    loadAvailableVideos()
    loadAvailableModels()
    
    return () => {
      stopPolling()
    }
  }, [])

  const loadAvailableVideos = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      const response = await fetch(`${apiUrl}/traffic-violations/videos/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        setAvailableVideos(data.videos || [])
      } else {
        console.error('Failed to load videos')
      }
    } catch (error) {
      console.error('Error loading videos:', error)
    }
  }

  const loadAvailableModels = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      const response = await fetch(`${apiUrl}/traffic-violations/models/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        setAvailableModels(data.available_models || ['yolov8s', 'yolo11s', 'yolo12s'])
      }
    } catch (error) {
      console.error('Error loading models:', error)
    }
  }

  const handleVideoUpload = async (file: File) => {
    try {
      const formData = new FormData()
      formData.append('video', file)

      const token = localStorage.getItem('access_token')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      const response = await fetch(`${apiUrl}/traffic-violations/upload/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        toast.success(data.message)
        
        // Set the uploaded video as selected
        setSelectedVideo(data.file_path)
        setSettings(prev => ({ ...prev, video_path: data.file_path }))
        
        // Reload video list
        loadAvailableVideos()
      } else {
        const error = await response.json()
        toast.error(error.message || 'Upload failed')
      }
    } catch (error) {
      toast.error('Upload failed')
      console.error('Upload error:', error)
    }
  }

  const handleVideoSelect = (videoPath: string) => {
    setSelectedVideo(videoPath)
    setSettings(prev => ({ ...prev, video_path: videoPath }))
  }

  const handleSettingsChange = (newSettings: Partial<DetectionSettings>) => {
    setSettings(prev => ({ ...prev, ...newSettings }))
  }

  const startDetection = async () => {
    if (!selectedVideo) {
      toast.error('Please select a video first')
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      
      // Update settings first
      await fetch(`${apiUrl}/traffic-violations/settings/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
      })

      // Start detection
      const response = await fetch(`${apiUrl}/traffic-violations/start/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          video_path: selectedVideo
        })
      })

      if (response.ok) {
        const data = await response.json()
        console.log('🚀 Detection started successfully:', data)
        setIsDetecting(true)
        toast.success(data.message)
        startPolling()
      } else {
        const error = await response.json()
        console.error('❌ Detection start failed:', error)
        toast.error(error.message || 'Failed to start detection')
      }
    } catch (error) {
      toast.error('Failed to start detection')
      console.error('Start detection error:', error)
    }
  }

  const stopDetection = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      const response = await fetch(`${apiUrl}/traffic-violations/stop/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        setIsDetecting(false)
        toast.success('Detection stopped')
        stopPolling()
      }
    } catch (error) {
      console.error('Stop detection error:', error)
    }
  }

  const startPolling = () => {
    console.log('🔄 Starting frame and violation polling...')
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
    
    // Poll for frames
    framePollingRef.current = setInterval(async () => {
      try {
        const token = localStorage.getItem('access_token')
        const response = await fetch(`${apiUrl}/traffic-violations/frame/`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.ok) {
          const data = await response.json()
          console.log('📡 Frame data received:', {
            hasImage: !!data.image,
            imageLength: data.image ? data.image.length : 0,
            stats: data.stats
          })
          if (data.image) {
            setCurrentFrame(data.image)
          }
          if (data.stats) {
            setViolationStats(prev => ({ ...prev, ...data.stats }))
          }
        } else {
          console.warn('❌ Frame request failed:', response.status)
        }
      } catch (error) {
        console.error('Frame polling error:', error)
      }
    }, 100) // 10 FPS polling

    // Poll for violations
    violationPollingRef.current = setInterval(async () => {
      try {
        const token = localStorage.getItem('access_token')
        const response = await fetch(`${apiUrl}/traffic-violations/violations/`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.ok) {
          const data = await response.json()
          if (data.violations && data.violations.length > 0) {
            // Check for new violations to show popup
            const currentViolationCount = recentViolations.length
            const newViolations = data.violations
            
            // Show popup for the most recent new violation
            if (newViolations.length > 0) {
              const latestViolation = newViolations[newViolations.length - 1]
              
              // Only show popup if this is a truly new violation (not already in our list)
              const isNewViolation = !recentViolations.some(existing => 
                existing.timestamp === latestViolation.timestamp &&
                existing.type === latestViolation.type &&
                existing.vehicle_type === latestViolation.vehicle_type
              )
              
              if (isNewViolation) {
                setCurrentViolationPopup(latestViolation)
                
                // Play violation sound (optional)
                try {
                  const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT')
                  audio.volume = 0.3
                  audio.play().catch(() => {}) // Ignore audio errors
                } catch (e) {
                  // Ignore audio errors
                }
              }
            }
            
            setRecentViolations(prev => [...prev, ...data.violations].slice(-20)) // Keep last 20
          }
          if (data.stats) {
            setViolationStats(prev => ({ ...prev, ...data.stats }))
          }
        }
      } catch (error) {
        console.error('Violation polling error:', error)
      }
    }, 500) // 2 FPS for violations
  }

  const stopPolling = () => {
    if (framePollingRef.current) {
      clearInterval(framePollingRef.current)
      framePollingRef.current = null
    }
    if (violationPollingRef.current) {
      clearInterval(violationPollingRef.current)
      violationPollingRef.current = null
    }
  }

  const resetSession = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      await fetch(`${apiUrl}/traffic-violations/session/reset/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      // Reset local state
      setViolationStats({
        total_violations: 0,
        speed_violations: 0,
        helmet_violations: 0,
        vehicle_counts: {
          cars: 0,
          bikes: 0,
          buses: 0,
          trucks: 0,
          total: 0
        }
      })
      setRecentViolations([])
      setCurrentFrame(null)
      
      toast.success('Session reset')
    } catch (error) {
      toast.error('Failed to reset session')
      console.error('Reset error:', error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Video Upload and Selection */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <VideoUploadArea
          onVideoUpload={handleVideoUpload}
          availableVideos={availableVideos}
          selectedVideo={selectedVideo}
          onVideoSelect={handleVideoSelect}
        />
        
        <SpeedSettings
          settings={settings}
          availableModels={availableModels}
          onSettingsChange={handleSettingsChange}
        />
      </div>

      {/* Control Buttons */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {!isDetecting ? (
              <button
                onClick={startDetection}
                disabled={!selectedVideo}
                className={`px-6 py-3 rounded-lg font-semibold flex items-center space-x-2 ${
                  selectedVideo
                    ? 'bg-red-600 text-white hover:bg-red-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                <span>🚀</span>
                <span>Start Detection</span>
              </button>
            ) : (
              <button
                onClick={stopDetection}
                className="px-6 py-3 bg-gray-600 text-white rounded-lg font-semibold hover:bg-gray-700 flex items-center space-x-2"
              >
                <span>⏹️</span>
                <span>Stop Detection</span>
              </button>
            )}
            
            <button
              onClick={resetSession}
              className="px-4 py-3 bg-orange-600 text-white rounded-lg font-semibold hover:bg-orange-700 flex items-center space-x-2"
            >
              <span>🔄</span>
              <span>Reset</span>
            </button>
          </div>

          <div className="flex items-center space-x-4">
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              isDetecting 
                ? 'bg-green-100 text-green-800' 
                : 'bg-gray-100 text-gray-800'
            }`}>
              {isDetecting ? '🟢 DETECTING' : '⚫ STOPPED'}
            </div>
          </div>
        </div>
      </div>

      {/* Live Video Stream and Statistics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <LiveVideoStream
            currentFrame={currentFrame}
            isDetecting={isDetecting}
            settings={settings}
          />
        </div>
        
        <div className="space-y-6">
          <ViolationStats stats={violationStats} />
          <ViolationHistory violations={recentViolations} />
        </div>
      </div>

      {/* Violation Popup - Top Right Corner */}
      <ViolationPopup
        violation={currentViolationPopup}
        onClose={() => setCurrentViolationPopup(null)}
      />
    </div>
  )
}