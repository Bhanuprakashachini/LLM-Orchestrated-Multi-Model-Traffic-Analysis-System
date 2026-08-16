'use client'

import React, { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  CloudArrowUpIcon, 
  PlayIcon, 
  ChartBarIcon,
  ClockIcon,
  EyeIcon,
  DocumentArrowDownIcon,
  CogIcon
} from '@heroicons/react/24/outline'

interface VideoUploadProps {
  onAnalysisComplete?: (results: any) => void
}

interface AnalysisResults {
  analysis_id: string
  status: string
  results: {
    total_vehicles: number  // Legacy field (shows max per frame)
    vehicles_tracked: number  // CORRECT field (shows unique vehicles)
    vehicle_counts: Record<string, number>
    congestion_level: string
    congestion_index: number
    traffic_metrics: any
    video_metadata: any
    frames_analyzed: number
    processing_time: number
    annotated_video_url: string
    thumbnail_url: string
    original_video_url?: string
    model_comparison?: any
  }
}

const VideoUpload: React.FC<VideoUploadProps> = ({ onAnalysisComplete }) => {
  const [file, setFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [results, setResults] = useState<AnalysisResults | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  // Analysis settings - OPTIMIZED for maximum vehicle detection
  const [modelType, setModelType] = useState('auto')
  const [sampleRate, setSampleRate] = useState(1)  // OPTIMIZED: Every frame for maximum detection
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.04)  // OPTIMIZED: Lower threshold for more vehicles
  const [showSettings, setShowSettings] = useState(false)
  const [roiPoints, setRoiPoints] = useState<Array<{x: number, y: number}>>([])
  const [showRoiHelper, setShowRoiHelper] = useState(false)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0]
      if (isValidVideoFile(droppedFile)) {
        setFile(droppedFile)
        setError(null)
      } else {
        setError('Please upload a valid video file (MP4, AVI, MOV, MKV, WMV, FLV)')
      }
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0]
      if (isValidVideoFile(selectedFile)) {
        setFile(selectedFile)
        setError(null)
      } else {
        setError('Please upload a valid video file (MP4, AVI, MOV, MKV, WMV, FLV)')
      }
    }
  }

  const isValidVideoFile = (file: File): boolean => {
    const validTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo', 'video/x-ms-wmv']
    const validExtensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
    
    return validTypes.includes(file.type) || 
           validExtensions.some(ext => file.name.toLowerCase().endsWith(ext))
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const uploadAndAnalyze = async () => {
    if (!file) return

    setUploading(true)
    setAnalyzing(true)
    setProgress(0)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('video', file)
      formData.append('model_type', modelType)
      formData.append('sample_rate', sampleRate.toString())
      formData.append('confidence_threshold', confidenceThreshold.toString())
      // OPTIMIZED: Force disable ROI filtering for maximum detection
      formData.append('enable_roi_filtering', 'false')
      
      // Add ROI polygon if defined
      if (roiPoints.length >= 3) {
        formData.append('roi_polygon', JSON.stringify(roiPoints))
      }

      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) return prev
          return prev + Math.random() * 10
        })
      }, 1000)

      const token = localStorage.getItem('access_token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/analysis/video/upload/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      })

      clearInterval(progressInterval)
      setProgress(100)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Upload failed')
      }

      const analysisResults = await response.json()
      setResults(analysisResults)
      
      if (onAnalysisComplete) {
        onAnalysisComplete(analysisResults)
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setUploading(false)
      setAnalyzing(false)
    }
  }

  const downloadReport = async (format: 'json' | 'csv') => {
    if (!results) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/analysis/video/${results.analysis_id}/download/?format=${format}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (!response.ok) throw new Error('Download failed')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `video_analysis_${results.analysis_id}.${format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError('Failed to download report')
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          🎥 Video Traffic Analysis
        </h1>
        <p className="text-gray-600">
          Upload a video for comprehensive vehicle detection, tracking, and traffic metrics
        </p>
      </div>

      {/* Settings Panel */}
      <motion.div
        initial={false}
        animate={{ height: showSettings ? 'auto' : 0 }}
        className="overflow-hidden"
      >
        <div className="bg-gray-50 rounded-lg p-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Model Type
              </label>
              <select
                value={modelType}
                onChange={(e) => setModelType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="auto">Auto (Best Model)</option>
                <option value="yolov8">YOLOv8</option>
                <option value="yolov12">YOLOv12</option>
                <option value="comparison">Model Comparison</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sample Rate (Every Nth frame)
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={sampleRate}
                onChange={(e) => setSampleRate(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Confidence Threshold
                <span className="text-xs text-gray-500 ml-2">(Lower = more detections, try 0.10-0.15)</span>
              </label>
              <input
                type="number"
                min="0.1"
                max="1.0"
                step="0.05"
                value={confidenceThreshold}
                onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          
          {/* ROI Configuration */}
          <div className="border-t pt-4">
            <div className="flex items-center justify-between mb-3">
              <label className="block text-sm font-medium text-gray-700">
                🎯 Region of Interest (ROI) - Reduces False Detections
              </label>
              <button
                type="button"
                onClick={() => setShowRoiHelper(!showRoiHelper)}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                {showRoiHelper ? 'Hide Help' : 'Show Help'}
              </button>
            </div>
            
            {showRoiHelper && (
              <div className="mb-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <div className="text-sm text-blue-800">
                  <p className="font-medium mb-2">🎯 What is ROI?</p>
                  <p className="mb-2">ROI (Region of Interest) helps eliminate false detections by only analyzing vehicles within the road area.</p>
                  <p className="mb-2"><strong>Benefits:</strong></p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li>Eliminates vehicles detected in background fields/areas</li>
                    <li>Improves accuracy by focusing on actual traffic</li>
                    <li>Reduces processing time and false positives</li>
                  </ul>
                  <p className="mt-2 text-xs"><strong>Note:</strong> If not set, automatic filtering will be applied to remove detections in the top 30% of the frame.</p>
                </div>
              </div>
            )}
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-600 mb-2">
                  ROI Points: {roiPoints.length} {roiPoints.length >= 3 ? '✅' : '(need 3+ points)'}
                </div>
                <div className="flex space-x-2">
                  <button
                    type="button"
                    onClick={() => setRoiPoints([])}
                    className="px-3 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600"
                  >
                    Clear ROI
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      // Set a default road ROI (bottom 70% of typical video)
                      setRoiPoints([
                        {x: 0, y: 0.3}, // Top-left (30% down from top)
                        {x: 1, y: 0.3}, // Top-right
                        {x: 1, y: 1},   // Bottom-right
                        {x: 0, y: 1}    // Bottom-left
                      ])
                    }}
                    className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                  >
                    Use Default Road Area
                  </button>
                </div>
              </div>
              
              <div>
                <div className="text-sm text-gray-600 mb-2">
                  Status: {roiPoints.length >= 3 ? 
                    <span className="text-green-600 font-medium">ROI Active - False detections will be filtered</span> : 
                    <span className="text-orange-600 font-medium">Using automatic height-based filtering</span>
                  }
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Settings Toggle */}
      <div className="flex justify-center">
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
        >
          <CogIcon className="w-4 h-4" />
          <span>{showSettings ? 'Hide' : 'Show'} Advanced Settings</span>
        </button>
      </div>

      {/* Upload Area */}
      {!results && (
        <motion.div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <input
            type="file"
            accept="video/*,.mp4,.avi,.mov,.mkv,.wmv,.flv"
            onChange={handleFileSelect}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            disabled={uploading}
          />
          
          <div className="space-y-4">
            <CloudArrowUpIcon className="w-16 h-16 text-gray-400 mx-auto" />
            
            {file ? (
              <div className="space-y-2">
                <p className="text-lg font-medium text-gray-900">{file.name}</p>
                <p className="text-sm text-gray-500">
                  {formatFileSize(file.size)}
                </p>
                
                <motion.button
                  onClick={uploadAndAnalyze}
                  disabled={uploading}
                  className="inline-flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <PlayIcon className="w-5 h-5" />
                  <span>{uploading ? 'Analyzing...' : 'Start Analysis'}</span>
                </motion.button>
              </div>
            ) : (
              <div>
                <p className="text-lg text-gray-600">
                  Drop your video file here or click to browse
                </p>
                <p className="text-sm text-gray-500">
                  Supports MP4, AVI, MOV, MKV, WMV, FLV (max 100MB)
                </p>
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Progress Bar */}
      <AnimatePresence>
        {uploading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-4"
          >
            <div className="bg-white rounded-lg p-6 shadow-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  {analyzing ? 'Analyzing video...' : 'Uploading...'}
                </span>
                <span className="text-sm text-gray-500">{Math.round(progress)}%</span>
              </div>
              
              <div className="w-full bg-gray-200 rounded-full h-2">
                <motion.div
                  className="bg-blue-600 h-2 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
              
              <div className="mt-4 text-sm text-gray-600">
                <p>• Extracting video metadata</p>
                <p>• Running vehicle detection on frames</p>
                <p>• Tracking vehicles across frames</p>
                <p>• Calculating traffic metrics</p>
                <p>• Generating insights and reports</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error Display */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-red-50 border border-red-200 rounded-lg p-4"
          >
            <p className="text-red-800">{error}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results Display */}
      <AnimatePresence>
        {results && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-4 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-blue-100 text-sm">Total Vehicles</p>
                    <p className="text-2xl font-bold">{results.results.vehicles_tracked || 0}</p>
                    <p className="text-blue-200 text-xs">Unique vehicles tracked</p>
                  </div>
                  <ChartBarIcon className="w-8 h-8 text-blue-200" />
                </div>
              </div>
              
              <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-4 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-green-100 text-sm">Vehicles Tracked</p>
                    <p className="text-2xl font-bold">{results.results.vehicles_tracked || 0}</p>
                  </div>
                  <EyeIcon className="w-8 h-8 text-green-200" />
                </div>
              </div>
              
              <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-4 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-purple-100 text-sm">Frames Analyzed</p>
                    <p className="text-2xl font-bold">{results.results.frames_analyzed || 0}</p>
                  </div>
                  <PlayIcon className="w-8 h-8 text-purple-200" />
                </div>
              </div>
              
              <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg p-4 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-orange-100 text-sm">Processing Time</p>
                    <p className="text-2xl font-bold">{(results.results.processing_time || 0).toFixed(1)}s</p>
                  </div>
                  <ClockIcon className="w-8 h-8 text-orange-200" />
                </div>
              </div>
            </div>

            {/* No Vehicles Detected Message */}
            {results.results.vehicles_tracked === 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-yellow-800">
                      No Vehicles Detected
                    </h3>
                    <div className="mt-2 text-sm text-yellow-700">
                      <p>The analysis completed successfully but no vehicles were detected in the video. This could be due to:</p>
                      <ul className="mt-2 list-disc list-inside space-y-1">
                        <li>The video doesn't contain clear vehicle imagery</li>
                        <li>Vehicles are too small or unclear in the video</li>
                        <li>The confidence threshold is too high (try 0.10-0.15 for better detection)</li>
                        <li>The video quality is too low for accurate detection</li>
                      </ul>
                      <p className="mt-2">
                        <strong>Tip:</strong> Try uploading a video with clear, well-lit traffic scenes for better results.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Traffic Metrics */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Traffic Analysis</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-gray-700 mb-2">Congestion Level</h4>
                  <div className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${
                    results.results.congestion_level === 'low' 
                      ? 'bg-green-100 text-green-800'
                      : results.results.congestion_level === 'medium'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {(results.results.congestion_level || 'low').toUpperCase()}
                  </div>
                  
                  <div className="mt-2">
                    <div className="flex justify-between text-sm text-gray-600 mb-1">
                      <span>Congestion Index</span>
                      <span>{((results.results.congestion_index || 0) * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          (results.results.congestion_index || 0) < 0.3 ? 'bg-green-500' :
                          (results.results.congestion_index || 0) < 0.7 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${((results.results.congestion_index || 0) * 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-700 mb-2">Vehicle Analysis</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Unique Vehicles Tracked:</span>
                      <span className="font-medium text-green-600">{results.results.vehicles_tracked || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Peak Vehicles (single frame):</span>
                      <span className="font-medium text-blue-600">{results.results.total_vehicles || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Frames Analyzed:</span>
                      <span className="font-medium">{results.results.frames_analyzed || 0}</span>
                    </div>
                    {results.results.traffic_metrics?.avg_vehicle_count && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Avg per Frame:</span>
                        <span className="font-medium">{results.results.traffic_metrics.avg_vehicle_count.toFixed(1)}</span>
                      </div>
                    )}
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-700 mb-2">Vehicle Distribution</h4>
                  {results.results.vehicle_counts && Object.keys(results.results.vehicle_counts).length > 0 ? (
                    <div className="space-y-2">
                      {Object.entries(results.results.vehicle_counts).map(([type, count]) => (
                        <div key={type} className="flex justify-between text-sm">
                          <span className="capitalize text-gray-600">{type}</span>
                          <span className="font-medium">{count} detections</span>
                        </div>
                      ))}
                      <div className="pt-2 border-t border-gray-200">
                        <div className="flex justify-between text-sm font-medium">
                          <span className="text-gray-700">Total Detections:</span>
                          <span className="text-purple-600">
                            {Object.values(results.results.vehicle_counts).reduce((sum, count) => sum + count, 0)}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          * Detections include same vehicles across multiple frames
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="text-sm text-gray-500 italic">
                      No vehicles detected to show distribution
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Video Display Section */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <PlayIcon className="w-5 h-5 mr-2" />
                Video Analysis Results
              </h3>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Original Video */}
                <div className="space-y-3">
                  <h4 className="font-medium text-gray-700 flex items-center">
                    <span className="mr-2">📹</span>
                    Original Video
                  </h4>
                  {results.results.original_video_url ? (
                    <div className="bg-gray-100 rounded-lg overflow-hidden">
                      <video
                        controls
                        className="w-full h-auto max-h-64 object-contain"
                        preload="metadata"
                        crossOrigin="anonymous"
                      >
                        <source 
                          src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/media/${results.results.original_video_url}`}
                          type="video/mp4"
                        />
                        <source 
                          src={`http://localhost:8000/media/${results.results.original_video_url}`}
                          type="video/mp4"
                        />
                        <source 
                          src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${results.results.original_video_url}`}
                          type="video/mp4"
                        />
                        Your browser does not support the video tag.
                      </video>
                    </div>
                  ) : (
                    <div className="bg-gray-100 rounded-lg p-8 text-center">
                      <PlayIcon className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                      <p className="text-gray-500">Original video not available</p>
                    </div>
                  )}
                </div>

                {/* Annotated Video */}
                <div className="space-y-3">
                  <h4 className="font-medium text-gray-700 flex items-center">
                    <span className="mr-2">🎯</span>
                    Annotated Video (with detections)
                  </h4>
                  {results.results.annotated_video_url ? (
                    <div className="bg-gray-100 rounded-lg overflow-hidden">
                      <video
                        controls
                        className="w-full h-auto max-h-64 object-contain"
                        preload="metadata"
                        crossOrigin="anonymous"
                      >
                        <source 
                          src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/media/${results.results.annotated_video_url}`}
                          type="video/mp4"
                        />
                        <source 
                          src={`http://localhost:8000/media/${results.results.annotated_video_url}`}
                          type="video/mp4"
                        />
                        <source 
                          src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${results.results.annotated_video_url}`}
                          type="video/mp4"
                        />
                        Your browser does not support the video tag.
                      </video>
                    </div>
                  ) : (
                    <div className="bg-gray-100 rounded-lg p-8 text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                      <p className="text-gray-500">Generating annotated video...</p>
                      <p className="text-xs text-gray-400 mt-1">This may take a few moments</p>
                    </div>
                  )}
                </div>
              </div>
              
              {/* Video Info */}
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Duration:</span>
                    <span className="font-medium">
                      {results.results.video_metadata?.duration ? formatDuration(results.results.video_metadata.duration) : 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Resolution:</span>
                    <span className="font-medium">
                      {results.results.video_metadata?.resolution ? results.results.video_metadata.resolution.join(' × ') : 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">FPS:</span>
                    <span className="font-medium">
                      {results.results.video_metadata?.fps ? results.results.video_metadata.fps.toFixed(1) : 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Format:</span>
                    <span className="font-medium">
                      {results.results.video_metadata?.format ? results.results.video_metadata.format.toUpperCase() : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-4 justify-center">
              <button
                onClick={() => downloadReport('json')}
                className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <DocumentArrowDownIcon className="w-5 h-5" />
                <span>Download JSON Report</span>
              </button>
              
              <button
                onClick={() => downloadReport('csv')}
                className="inline-flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                <DocumentArrowDownIcon className="w-5 h-5" />
                <span>Download CSV Report</span>
              </button>
              
              {results.results.annotated_video_url && (
                <a
                  href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${results.results.annotated_video_url}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  <PlayIcon className="w-5 h-5" />
                  <span>View Annotated Video</span>
                </a>
              )}
              
              <button
                onClick={() => {
                  setResults(null)
                  setFile(null)
                  setProgress(0)
                }}
                className="inline-flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                <CloudArrowUpIcon className="w-5 h-5" />
                <span>Analyze Another Video</span>
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default VideoUpload