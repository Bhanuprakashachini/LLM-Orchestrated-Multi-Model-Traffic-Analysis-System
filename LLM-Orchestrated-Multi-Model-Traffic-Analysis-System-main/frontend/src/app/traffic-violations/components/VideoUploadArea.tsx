'use client'

import { useState } from 'react'
import toast from 'react-hot-toast'

interface VideoUploadAreaProps {
  onVideoUpload: (file: File) => void
  availableVideos: any[]
  selectedVideo: string
  onVideoSelect: (videoPath: string) => void
}

export default function VideoUploadArea({
  onVideoUpload,
  availableVideos,
  selectedVideo,
  onVideoSelect
}: VideoUploadAreaProps) {
  const [dragActive, setDragActive] = useState(false)
  const [isUploading, setIsUploading] = useState(false)

  const handleFileSelect = (file: File) => {
    // Validate file type
    const validTypes = [
      'video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm', 
      'video/m4v', 'video/wmv', 'video/flv', 'video/3gp'
    ]
    
    const fileName = file.name.toLowerCase()
    const validExtensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v', '.wmv', '.flv', '.3gp']
    
    const hasValidType = validTypes.includes(file.type)
    const hasValidExtension = validExtensions.some(ext => fileName.endsWith(ext))
    
    if (!hasValidType && !hasValidExtension) {
      toast.error('Please select a valid video file. Supported formats: MP4, AVI, MOV, MKV, WebM, WMV, FLV')
      return
    }

    // Check file size (500MB limit)
    const maxSize = 500 * 1024 * 1024 // 500MB
    if (file.size > maxSize) {
      toast.error(`File size must be less than 500MB. Current file: ${(file.size / (1024 * 1024)).toFixed(1)}MB`)
      return
    }

    setIsUploading(true)
    onVideoUpload(file)
    
    // Reset uploading state after a delay
    setTimeout(() => setIsUploading(false), 3000)
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragActive(false)
    
    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      handleFileSelect(files[0])
    }
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragActive(true)
  }

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragActive(false)
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <span className="mr-2">📁</span>
        Video Upload & Selection
      </h3>

      {/* Drag & Drop Upload Area */}
      <div
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-all mb-6 ${
          dragActive
            ? 'border-red-500 bg-red-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <div className="text-4xl mb-3">🎬</div>
        <h4 className="text-lg font-semibold text-gray-700 mb-2">
          Drop video here or click to browse
        </h4>
        <p className="text-gray-500 mb-4 text-sm">
          Supports: MP4, AVI, MOV, MKV, WebM, WMV, FLV (up to 500MB)
        </p>
        
        <input
          type="file"
          accept="video/*,.mp4,.avi,.mov,.mkv,.webm,.m4v,.wmv,.flv"
          onChange={(e) => e.target.files && handleFileSelect(e.target.files[0])}
          className="hidden"
          id="video-upload"
          disabled={isUploading}
        />
        <label
          htmlFor="video-upload"
          className={`inline-block px-6 py-3 rounded-lg cursor-pointer transition-colors ${
            isUploading
              ? 'bg-gray-400 text-white cursor-not-allowed'
              : 'bg-red-600 text-white hover:bg-red-700'
          }`}
        >
          {isUploading ? (
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span>Uploading...</span>
            </div>
          ) : (
            '📁 Choose Video File'
          )}
        </label>
      </div>

      {/* Available Videos List */}
      <div>
        <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
          <span className="mr-2">📚</span>
          Available Videos ({availableVideos.length})
        </h4>
        
        {availableVideos.length > 0 ? (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {availableVideos.map((video, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedVideo === video.path
                    ? 'border-red-500 bg-red-50'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
                onClick={() => onVideoSelect(video.path)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">🎥</span>
                      <span className="font-medium text-gray-900 truncate">
                        {video.name}
                      </span>
                      {selectedVideo === video.path && (
                        <span className="text-red-600 text-sm">✓ Selected</span>
                      )}
                    </div>
                    <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
                      <span>📊 {video.size}</span>
                      <span>📍 {video.location || 'Uploaded'}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <div className="text-3xl mb-2">📭</div>
            <p>No videos available</p>
            <p className="text-sm">Upload a video to get started</p>
          </div>
        )}
      </div>

      {/* Selected Video Info */}
      {selectedVideo && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <span className="text-green-600">✅</span>
            <span className="font-medium text-green-900">Ready for Detection</span>
          </div>
          <p className="text-sm text-green-700 mt-1">
            Video selected: {selectedVideo.split('/').pop()}
          </p>
        </div>
      )}
    </div>
  )
}