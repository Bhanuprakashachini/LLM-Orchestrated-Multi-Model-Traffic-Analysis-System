// Enhanced Video Player Component with Better Error Handling and Retry Logic

import { useState, useRef, useEffect } from 'react'

interface VideoPlayerProps {
  path: string
  type: string
  onLoad?: (type: string, path: string) => void
  onError?: (type: string, path: string) => void
}

const VideoPlayer = ({ path, type, onLoad, onError }: VideoPlayerProps) => {
  const [retryCount, setRetryCount] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)
  
  const handleLoad = () => {
    setIsLoading(false)
    setHasError(false)
    onLoad?.(type, path)
  }
  
  const handleError = () => {
    console.error(`❌ Video load failed (attempt ${retryCount + 1}): ${path}`)
    
    if (retryCount < 3) {
      // Retry loading with exponential backoff
      setTimeout(() => {
        setRetryCount(prev => prev + 1)
        if (videoRef.current) {
          videoRef.current.load()
        }
      }, 1000 * (retryCount + 1))
    } else {
      setIsLoading(false)
      setHasError(true)
      onError?.(type, path)
    }
  }
  
  const handleRetry = () => {
    setRetryCount(0)
    setIsLoading(true)
    setHasError(false)
    if (videoRef.current) {
      videoRef.current.load()
    }
  }
  
  // Try multiple URL formats for better compatibility
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const mediaUrls = [
    `${baseUrl}/media/${path}`,
    `${baseUrl}/${path}`,
    `http://localhost:8000/media/${path}`
  ]
  
  useEffect(() => {
    // Reset state when path changes
    setRetryCount(0)
    setIsLoading(true)
    setHasError(false)
  }, [path])
  
  return (
    <div className="relative">
      {isLoading && !hasError && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg z-10">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p className="text-sm text-gray-600">Loading video...</p>
            {retryCount > 0 && <p className="text-xs text-gray-500">Retry {retryCount}/3</p>}
          </div>
        </div>
      )}
      
      {hasError && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-50 rounded-lg z-10">
          <div className="text-center p-4">
            <div className="text-red-500 text-4xl mb-2">⚠️</div>
            <p className="text-red-600 font-medium mb-2">Failed to load video</p>
            <p className="text-sm text-red-500 mb-3">{path}</p>
            <button 
              onClick={handleRetry}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Retry Loading
            </button>
          </div>
        </div>
      )}
      
      <video
        ref={videoRef}
        key={`${path}-${retryCount}`}
        controls
        className="w-full h-auto max-h-96 rounded-lg shadow-lg"
        onLoadedData={handleLoad}
        onError={handleError}
        onCanPlay={handleLoad}
        preload="metadata"
        crossOrigin="anonymous"
        style={{ display: hasError ? 'none' : 'block' }}
      >
        {mediaUrls.map((url, index) => (
          <source key={index} src={url} type="video/mp4" />
        ))}
        <source src={mediaUrls[0].replace('.mp4', '.webm')} type="video/webm" />
        <source src={mediaUrls[0].replace('.mp4', '.avi')} type="video/avi" />
        Your browser does not support the video tag.
      </video>
    </div>
  )
}

export default VideoPlayer