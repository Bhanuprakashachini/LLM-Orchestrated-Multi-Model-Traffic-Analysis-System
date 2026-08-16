'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

export default function UploadPage() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [showProcessingModal, setShowProcessingModal] = useState(false)
  const [processingStep, setProcessingStep] = useState(0)
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false)
  const [roiPoints, setRoiPoints] = useState<Array<{x: number, y: number}>>([])
  const [showRoiHelper, setShowRoiHelper] = useState(false)

  useEffect(() => {
    if (user === null) {
      router.push('/login')
    }
  }, [user, router])

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  const handleFileSelect = (file: File) => {
    // Expanded list of supported formats for better compatibility
    const validTypes = [
      // Images
      'image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/bmp', 'image/tiff',
      // Videos - common formats
      'video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm', 'video/m4v',
      'video/wmv', 'video/flv', 'video/3gp', 'video/ogv',
      // Additional MIME types that browsers might use
      'video/quicktime', 'video/x-msvideo', 'video/x-ms-wmv'
    ]
    
    // Also check file extensions as fallback (some browsers don't set MIME types correctly)
    const fileName = file.name.toLowerCase()
    const validExtensions = [
      '.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff',
      '.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v', '.wmv', '.flv', '.3gp', '.ogv'
    ]
    
    const hasValidType = validTypes.includes(file.type)
    const hasValidExtension = validExtensions.some(ext => fileName.endsWith(ext))
    
    if (!hasValidType && !hasValidExtension) {
      toast.error('Please select a valid image or video file. Supported formats: JPG, PNG, WebP, MP4, AVI, MOV, MKV, WebM, and more.')
      return
    }

    // Increased file size limit for high-quality videos
    const maxSize = 100 * 1024 * 1024 // 100MB limit
    if (file.size > maxSize) {
      toast.error(`File size must be less than ${maxSize / (1024 * 1024)}MB. Current file: ${(file.size / (1024 * 1024)).toFixed(1)}MB`)
      return
    }

    // Log file info for debugging
    console.log(`📁 File selected: ${file.name}`)
    console.log(`📊 File info: ${(file.size / (1024 * 1024)).toFixed(1)}MB, type: ${file.type}`)

    setSelectedFile(file)
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

  const uploadAndAnalyze = async () => {
    if (!selectedFile) {
      toast.error('Please select a file first')
      return
    }

    setIsUploading(true)
    setShowProcessingModal(true)
    setProcessingStep(0)
    
    // Processing steps for user engagement - All 4 advanced models
    const steps = [
      'Uploading file to server...',
      'Initializing 4 Advanced YOLO models...',
      'Running YOLOv8 Advanced analysis...',
      'Running YOLOv11 Advanced analysis...',
      'Running YOLOv12 Advanced analysis...',
      'Running Advanced Ensemble analysis...',
      'Comparing 4 advanced model results...',
      'Generating advanced insights and recommendations...',
      'Preparing comprehensive analysis results...',
      'Advanced analysis complete!'
    ]
    
    let stepInterval: NodeJS.Timeout | null = null
    let currentStep = 0
    
    try {
      // Import API service
      const { apiService } = await import('@/services/api')
      
      // Start the API call using the API service
      const apiPromise = apiService.comprehensiveModelComparison(selectedFile, {
        roi_polygon: roiPoints.length >= 3 ? roiPoints : undefined
      })

      // Progress simulation that syncs with actual API timing
      stepInterval = setInterval(() => {
        currentStep++
        // Only progress to step 7 (80%) until API completes
        const maxStepBeforeCompletion = 7 // Stop at "Generating insights and recommendations..."
        if (currentStep < maxStepBeforeCompletion) {
          setProcessingStep(currentStep)
        }
      }, 5000) // Adjusted to 5 seconds per step to better match real 4-model analysis time (~35s total)

      // Wait for API response
      const result = await apiPromise

      // Clear the interval once API responds
      if (stepInterval) {
        clearInterval(stepInterval)
      }

      if (result.data) {
        // Store only essential data to avoid quota issues
        const essentialData = {
          analysis_id: result.data.analysis_id,
          vehicle_detection_summary: result.data.vehicle_detection_summary,
          comparison_table: result.data.comparison_table, // Show all models for comparison
          images: {
            original: result.data.images?.original,
            best_model_annotated: result.data.images?.best_model_annotated
          },
          llm_insights: result.data.llm_insights ? {
            traffic_analysis: result.data.llm_insights.traffic_analysis?.substring(0, 300), // Truncate to 300 chars
            model_used: result.data.llm_insights.model_used
          } : null,
          analysis_info: {
            timestamp: result.data.analysis_info?.timestamp || new Date().toISOString(),
            filename: selectedFile.name // Store original filename
          }
        }
        
        try {
          // Clear any existing analysis data first to free up space
          localStorage.removeItem('currentAnalysis')
          localStorage.removeItem('comprehensiveAnalysis')
          localStorage.removeItem('analysisSavedToDB')  // Clear saved flag for new analysis
          localStorage.removeItem('analysisPageReady')
          
          // Check data size before storing
          const dataString = JSON.stringify(essentialData)
          const dataSizeKB = dataString.length / 1024
          
          console.log(`📊 Analysis data size: ${dataSizeKB.toFixed(1)} KB`)
          
          if (dataSizeKB > 3000) { // 3MB limit
            console.warn('⚠️ Data too large, storing ultra-minimal version')
            const ultraMinimalData = {
              vehicle_count: essentialData.vehicle_detection_summary?.total_vehicles || 0,
              best_model: essentialData.comparison_table?.[0]?.model_name || 'Unknown',
              images: essentialData.images,
              filename: essentialData.analysis_info?.filename
            }
            localStorage.setItem('currentAnalysis', JSON.stringify(ultraMinimalData))
          } else {
            localStorage.setItem('currentAnalysis', dataString)
          }
          
          console.log('✅ Analysis data stored successfully')
        } catch (e) {
          console.warn('⚠️ LocalStorage quota exceeded, storing minimal data:', e)
          try {
            // Store absolute minimum - just what's needed for display
            const emergencyData = {
              vehicle_count: result.data.vehicle_detection_summary?.total_vehicles || 0,
              images: {
                original: result.data.images?.original,
                best_model_annotated: result.data.images?.best_model_annotated
              }
            }
            localStorage.setItem('currentAnalysis', JSON.stringify(emergencyData))
            console.log('✅ Emergency minimal data stored')
          } catch (e2) {
            console.error('❌ Cannot store any data, continuing without localStorage:', e2)
            // Continue without storing - analysis will still work from API response
          }
        }
        
        // Show "Preparing results..." step
        setProcessingStep(steps.length - 2) // Second to last step
        
        // Clear any existing analysis page ready signal
        localStorage.removeItem('analysisPageReady')
        
        // Navigate to analysis page first
        router.push('/analysis')
        
        // Wait for analysis page to signal it's ready
        const waitForAnalysisPageReady = () => {
          const checkReady = () => {
            const isReady = localStorage.getItem('analysisPageReady')
            if (isReady === 'true') {
              console.log('✅ Analysis page is ready, completing progress bar')
              // Show final step and complete progress
              setProcessingStep(steps.length - 1) // Final step: "Analysis complete!"
              
              // Wait a moment to show 100% completion, then close modal
              setTimeout(() => {
                setShowProcessingModal(false)
                toast.success('All 4 advanced models analyzed successfully!')
              }, 1500) // Give time to see 100% completion
            } else {
              // Check again in 100ms
              setTimeout(checkReady, 100)
            }
          }
          checkReady()
        }
        
        // Start waiting for analysis page ready signal
        setTimeout(waitForAnalysisPageReady, 500) // Small delay before starting to check
      } else {
        setShowProcessingModal(false)
        toast.error(result.error || 'Analysis failed')
      }
    } catch (error) {
      if (stepInterval) {
        clearInterval(stepInterval)
      }
      setShowProcessingModal(false)
      toast.error('Failed to analyze file. Please try again.')
      console.error('Analysis error:', error)
    } finally {
      setIsUploading(false)
    }
  }

  const processingSteps = [
    'Uploading file to server...',
    'Initializing 4 Advanced YOLO models...',
    'Running YOLOv8 Advanced analysis...',
    'Running YOLOv11 Advanced analysis...',
    'Running YOLOv12 Advanced analysis...',
    'Running Advanced Ensemble analysis...',
    'Comparing 4 advanced model results...',
    'Generating advanced insights and recommendations...',
    'Preparing comprehensive analysis results...',
    'Advanced analysis complete!'
  ]

  const projectFeatures = [
    {
      icon: '🚗',
      title: 'Multi-Vehicle Detection',
      description: 'Detects cars, large vehicles, and 2-wheelers with high accuracy'
    },
    {
      icon: '🧠',
      title: '4 Advanced YOLO Models',
      description: 'YOLOv8, YOLOv11, YOLOv12, and Ensemble - all configured for maximum accuracy'
    },
    {
      icon: '📊',
      title: 'Traffic Analysis',
      description: 'Density estimation, congestion detection, and flow analysis'
    },
    {
      icon: '⚡',
      title: 'Real-time Processing',
      description: 'Fast analysis with performance metrics and FPS monitoring'
    },
    {
      icon: '📈',
      title: 'Model Comparison',
      description: 'Detailed comparison between all 4 models with recommendations'
    },
    {
      icon: '🍃',
      title: 'MongoDB Storage',
      description: 'Persistent data storage with user-specific analytics'
    }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Processing Modal */}
      {showProcessingModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-t-2xl">
              <div className="text-center">
                <div className="text-4xl mb-3">🚗</div>
                <h2 className="text-2xl font-bold mb-2">AI Traffic Analysis in Progress</h2>
                <p className="text-blue-100">Processing your file with advanced YOLO models...</p>
              </div>
            </div>

            {/* Progress Section */}
            <div className="p-6 border-b bg-gray-50">
              <div className="flex items-center mb-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-4"></div>
                <div className="flex-1">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-bold text-gray-900">
                      {processingSteps[processingStep]}
                    </span>
                    <span className="text-sm text-gray-900 font-semibold">
                      {Math.round(((processingStep + 1) / processingSteps.length) * 100)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-300 rounded-full h-3 border">
                    <div 
                      className="bg-gradient-to-r from-blue-600 to-purple-600 h-3 rounded-full transition-all duration-1000"
                      style={{ 
                        width: `${((processingStep + 1) / processingSteps.length) * 100}%`
                      }}
                    ></div>
                  </div>
                </div>
              </div>
              
              <div className="text-center text-sm text-gray-900 font-medium">
                <p>
                  {processingStep < processingSteps.length - 2 
                    ? '⏱️ Estimated time: 60-90 seconds | 🔄 Processing with 4 advanced YOLO models for maximum accuracy...'
                    : processingStep === processingSteps.length - 2
                    ? '🔄 Preparing comprehensive analysis results for display...'
                    : '✅ Advanced analysis complete! Opening results page...'
                  }
                </p>
              </div>
            </div>

            {/* Project Features */}
            <div className="p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4 text-center">
                🎯 What Makes This System Powerful
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                {projectFeatures.map((feature, index) => (
                  <div 
                    key={index}
                    className="flex items-start p-4 bg-white rounded-lg border border-gray-300 shadow-sm hover:shadow-md transition-all"
                  >
                    <div className="text-2xl mr-3 flex-shrink-0">{feature.icon}</div>
                    <div>
                      <h4 className="font-bold text-gray-900 mb-1">{feature.title}</h4>
                      <p className="text-sm text-gray-700 font-medium">{feature.description}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Technical Highlights */}
              <div className="bg-white rounded-lg p-4 border-2 border-blue-300 shadow-sm">
                <h4 className="font-bold text-gray-900 mb-3 text-center">🔬 Advanced AI Technology</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                  <div>
                    <div className="text-3xl font-bold text-blue-700">4</div>
                    <div className="text-sm font-semibold text-gray-800">YOLO Models</div>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-green-700">3</div>
                    <div className="text-sm font-semibold text-gray-800">Vehicle Types</div>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-orange-700">95%+</div>
                    <div className="text-sm font-semibold text-gray-800">Accuracy</div>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-purple-700">Real-time</div>
                    <div className="text-sm font-semibold text-gray-800">Processing</div>
                  </div>
                </div>
              </div>

              {/* What You'll Get */}
              <div className="mt-6 bg-white rounded-lg p-4 border-2 border-green-300 shadow-sm">
                <h4 className="font-bold text-green-900 mb-3 text-center">📋 Your Analysis Report Will Include</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                  <div className="flex items-center">
                    <span className="text-green-700 mr-2 font-bold">✓</span>
                    <span className="text-gray-900 font-medium">Vehicle count and classification</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-green-700 mr-2 font-bold">✓</span>
                    <span className="text-gray-900 font-medium">Traffic density analysis</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-green-700 mr-2 font-bold">✓</span>
                    <span className="text-gray-900 font-medium">Model performance comparison</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-green-700 mr-2 font-bold">✓</span>
                    <span className="text-gray-900 font-medium">Accuracy metrics and performance</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-green-700 mr-2 font-bold">✓</span>
                    <span className="text-gray-900 font-medium">Processing time and FPS metrics</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-green-700 mr-2 font-bold">✓</span>
                    <span className="text-gray-900 font-medium">Downloadable CSV/JSON reports</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-green-700 mr-2 font-bold">✓</span>
                    <span className="text-gray-900 font-medium">AI-generated insights</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-green-700 mr-2 font-bold">✓</span>
                    <span className="text-gray-900 font-medium">Visual analysis with annotations</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="bg-gray-100 px-6 py-4 rounded-b-2xl text-center border-t">
              <p className="text-sm text-gray-900 font-medium">
                🔒 Your data is secure and will be saved to MongoDB when you logout
              </p>
            </div>
          </div>
        </div>
      )}
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-6 py-4 flex justify-between items-center">
          <button
            onClick={() => router.push('/dashboard')}
            className="text-gray-600 hover:text-gray-900 flex items-center"
          >
            ← Dashboard
          </button>
          <h1 className="text-xl font-semibold text-gray-900">Traffic Analysis</h1>
          <button
            onClick={logout}
            className="text-red-600 hover:text-red-700"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <div className="text-6xl mb-6">🚗</div>
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Complete Traffic Analysis
          </h2>
          <p className="text-gray-600 text-lg max-w-2xl mx-auto">
            Upload an image or video for comprehensive AI-powered analysis with vehicle detection, model 
            comparison, and all advanced features
          </p>
        </div>

        {/* What You'll Get */}
        <div className="bg-white rounded-xl shadow-sm border p-6 mb-8">
          <h3 className="text-lg font-semibold text-gray-800 mb-6 text-center flex items-center justify-center">
            <span className="mr-2">🎯</span>
            What You'll Get
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg border border-blue-100">
              <div className="text-3xl mb-3">🚗</div>
              <h4 className="font-semibold text-blue-900 mb-2">Vehicle Detection</h4>
              <p className="text-sm text-blue-700">Count & Classification</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg border border-green-100">
              <div className="text-3xl mb-3">📊</div>
              <h4 className="font-semibold text-green-900 mb-2">Model Comparison</h4>
              <p className="text-sm text-green-700">4 YOLO Models</p>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg border border-orange-100">
              <div className="text-3xl mb-3">📈</div>
              <h4 className="font-semibold text-orange-900 mb-2">Complete Report</h4>
              <p className="text-sm text-orange-700">All Features</p>
            </div>
          </div>
        </div>

        {/* Upload Area */}
        <div className="bg-white rounded-xl shadow-sm border p-8">
          <div
            className={`border-2 border-dashed rounded-xl p-12 text-center transition-all ${
              dragActive
                ? 'border-blue-500 bg-blue-50'
                : selectedFile
                ? 'border-green-500 bg-green-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            {selectedFile ? (
              <div>
                <div className="text-5xl mb-4">📁</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {selectedFile.name}
                </h3>
                <p className="text-gray-500 mb-4">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </p>
                <button
                  onClick={() => setSelectedFile(null)}
                  className="text-red-600 hover:text-red-700 underline"
                >
                  Remove file
                </button>
              </div>
            ) : (
              <div>
                <div className="text-5xl mb-4">📁</div>
                <h3 className="text-xl font-semibold text-gray-700 mb-2">
                  Drop your file here or click to browse
                </h3>
                <p className="text-gray-500 mb-6">
                  Supports: Images (JPEG, PNG, WebP, BMP, TIFF) and Videos (MP4, AVI, MOV, MKV, WebM, WMV, FLV) up to 100MB
                </p>
                <input
                  type="file"
                  accept="image/*,video/*"
                  onChange={(e) => e.target.files && handleFileSelect(e.target.files[0])}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg cursor-pointer hover:bg-blue-700 transition-colors"
                >
                  Choose File
                </label>
              </div>
            )}
          </div>

          {/* Advanced Settings */}
          <div className="mt-6">
            <div className="flex justify-center">
              <button
                type="button"
                onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                <span>⚙️</span>
                <span>{showAdvancedSettings ? 'Hide' : 'Show'} Advanced Settings</span>
              </button>
            </div>
            
            {showAdvancedSettings && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
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
                      <p className="mt-2 text-xs"><strong>Note:</strong> If not set, automatic filtering will be applied to remove detections in the top 30% of the image.</p>
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
                          // Set a default road ROI (bottom 70% of typical image)
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
            )}
          </div>

          {/* Start Analysis Button */}
          <div className="mt-8 text-center">
            <button
              onClick={uploadAndAnalyze}
              disabled={!selectedFile || isUploading}
              className={`px-8 py-4 rounded-xl font-semibold text-lg transition-all ${
                !selectedFile || isUploading
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 shadow-lg hover:shadow-xl'
              }`}
            >
              {isUploading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                  Analyzing...
                </div>
              ) : (
                '🚀 Start Complete Analysis'
              )}
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}