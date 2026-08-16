'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

interface Analysis {
  id: string
  user_id: string
  analysis_type: string
  model_version: string
  processing_time: number
  success: boolean
  created_at: string
  vehicle_detection: {
    total_vehicles: number
    detection_summary?: Record<string, number>
    best_model?: string
  }
  images?: {
    original?: string
    annotated?: string
    best_model_annotated?: string
  }
  comparison_results?: Array<{
    model_name: string
    grade: string
    total_vehicles: number
    estimated_accuracy: string
    processing_time: string
  }>
  status: string
  error_message?: string
}

interface AnalysisHistory {
  analyses: Analysis[]
  pagination: {
    current_page: number
    total_count: number
    has_more: boolean
    per_page: number
    total_pages: number
  }
}

export default function HistoryPage() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisHistory | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedAnalysis, setSelectedAnalysis] = useState<Analysis | null>(null)
  const [showModal, setShowModal] = useState(false)

  useEffect(() => {
    if (!user) {
      router.push('/login')
      return
    }

    fetchAnalysisHistory(currentPage)
  }, [user, router, currentPage])

  const fetchAnalysisHistory = async (page: number) => {
    try {
      setIsLoading(true)
      const token = localStorage.getItem('access_token')
      if (!token) {
        toast.error('Authentication required')
        router.push('/login')
        return
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/analysis/user/history/?page=${page}&limit=12&type=comprehensive_comparison`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        
        // Filter to show only Multi-Model analyses (comprehensive_comparison type)
        const filteredData = {
          ...data,
          analyses: data.analyses.filter((analysis: Analysis) => 
            analysis.analysis_type === 'comprehensive_comparison' || 
            analysis.model_version === 'Multi-Model Comparison' ||
            analysis.model_version?.includes('Multi-Model')
          )
        }
        
        setAnalysisHistory(filteredData)
        console.log('📋 Multi-Model analysis history loaded:', filteredData)
      } else {
        toast.error('Failed to load analysis history')
      }
    } catch (error) {
      console.error('Error fetching analysis history:', error)
      toast.error('Error loading analysis history')
    } finally {
      setIsLoading(false)
    }
  }

  const handleViewAnalysis = (analysis: Analysis) => {
    setSelectedAnalysis(analysis)
    setShowModal(true)
  }

  const handleDownloadAnalysisReport = async (analysis: Analysis) => {
    try {
      // Generate HTML report for specific analysis
      const htmlContent = generateAnalysisHTMLReport(analysis)
      const blob = new Blob([htmlContent], { type: 'text/html' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.style.display = 'none'
      a.href = url
      a.download = `analysis_report_${analysis.id}_${new Date(analysis.created_at).toISOString().split('T')[0]}.html`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success('Analysis report downloaded')
    } catch (error) {
      console.error('Error downloading analysis report:', error)
      toast.error('Error downloading report')
    }
  }

  const generateAnalysisHTMLReport = (analysis: Analysis) => {
    const timestamp = new Date(analysis.created_at).toLocaleString()
    const bestModel = analysis.comparison_results?.[0]
    
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Traffic Analysis Report - ${analysis.id}</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            line-height: 1.6; 
            background-color: #f8f9fa;
        }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 30px; 
            text-align: center;
        }
        .header h1 { margin: 0; font-size: 2.5em; font-weight: 300; }
        .content { padding: 30px; }
        .section { 
            margin-bottom: 40px; 
            padding: 25px; 
            border: 1px solid #e9ecef; 
            border-radius: 12px; 
            background: #fff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .section h2 { 
            color: #495057; 
            border-bottom: 3px solid #007bff; 
            padding-bottom: 10px; 
            margin-top: 0;
        }
        .images-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }
        .image-container {
            text-align: center;
            padding: 15px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            background: #f8f9fa;
        }
        .image-container h4 {
            margin: 0 0 15px 0;
            color: #495057;
        }
        .image-container img {
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .image-placeholder {
            width: 100%;
            height: 200px;
            background: #e9ecef;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #6c757d;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #dee2e6;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
            margin-bottom: 5px;
        }
        .highlight { 
            background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%); 
            padding: 20px; 
            border-radius: 8px; 
            margin: 15px 0; 
            border-left: 4px solid #28a745;
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
            margin: 15px 0; 
            background: white;
            border-radius: 8px;
            overflow: hidden;
        }
        th, td { 
            border: 1px solid #dee2e6; 
            padding: 12px 15px; 
            text-align: left; 
        }
        th { 
            background: #f8f9fa; 
            font-weight: 600;
        }
        .best-model { background: #d4edda !important; }
        @media (max-width: 768px) {
            .images-section { grid-template-columns: 1fr; }
            .stats-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚗 Traffic Analysis Report</h1>
            <p><strong>Analysis ID:</strong> ${analysis.id}</p>
            <p><strong>Generated:</strong> ${timestamp}</p>
            <p><strong>Status:</strong> ${analysis.success ? '✅ Success' : '❌ Failed'}</p>
        </div>

        <div class="content">
            <!-- Summary Section -->
            <div class="section">
                <h2>📊 Analysis Summary</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">${analysis.vehicle_detection?.total_vehicles || 0}</div>
                        <div class="stat-label">Total Vehicles</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${analysis.model_version}</div>
                        <div class="stat-label">Model Used</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${analysis.processing_time.toFixed(2)}s</div>
                        <div class="stat-label">Processing Time</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${analysis.analysis_type}</div>
                        <div class="stat-label">Analysis Type</div>
                    </div>
                </div>
            </div>

            <!-- Images Section -->
            <div class="section">
                <h2>📷 Analysis Images</h2>
                <div class="images-section">
                    <div class="image-container">
                        <h4>🖼️ Original Image</h4>
                        ${analysis.images?.original ? `
                            <img src="${process.env.NEXT_PUBLIC_MEDIA_URL || 'http://localhost:8000/media'}/${analysis.images.original}" 
                                 alt="Original uploaded image" 
                                 onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
                            <div class="image-placeholder" style="display: none;">
                                📷 Original Image<br><small>Failed to load</small>
                            </div>
                        ` : `
                            <div class="image-placeholder">
                                📷 Original Image<br><small>Not available</small>
                            </div>
                        `}
                    </div>
                    
                    <div class="image-container">
                        <h4>🎯 Annotated Image</h4>
                        ${analysis.images?.best_model_annotated || analysis.images?.annotated ? `
                            <img src="${process.env.NEXT_PUBLIC_MEDIA_URL || 'http://localhost:8000/media'}/${analysis.images.best_model_annotated || analysis.images.annotated}" 
                                 alt="AI annotated image" 
                                 onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
                            <div class="image-placeholder" style="display: none;">
                                🎯 Annotated Image<br><small>Failed to load</small>
                            </div>
                        ` : `
                            <div class="image-placeholder">
                                🎯 Annotated Image<br><small>Not available</small>
                            </div>
                        `}
                    </div>
                </div>
            </div>

            <!-- Vehicle Detection Results -->
            <div class="section">
                <h2>🚗 Vehicle Detection Results</h2>
                <div class="highlight">
                    <p><strong>Total Vehicles Detected:</strong> ${analysis.vehicle_detection?.total_vehicles || 0}</p>
                    <p><strong>Best Model:</strong> ${analysis.vehicle_detection?.best_model || analysis.model_version}</p>
                    <p><strong>Analysis Status:</strong> ${analysis.success ? 'Successful' : 'Failed'}</p>
                    ${analysis.error_message ? `<p><strong>Error:</strong> ${analysis.error_message}</p>` : ''}
                </div>
                
                ${analysis.vehicle_detection?.detection_summary ? `
                <table>
                    <tr><th>Vehicle Type</th><th>Count</th></tr>
                    ${Object.entries(analysis.vehicle_detection.detection_summary).map(([type, count]) => `
                        <tr><td>${type}</td><td>${count}</td></tr>
                    `).join('')}
                </table>
                ` : ''}
            </div>

            ${analysis.comparison_results ? `
            <!-- Model Comparison Results -->
            <div class="section">
                <h2>⚖️ Model Performance Comparison</h2>
                <table>
                    <tr>
                        <th>Rank</th><th>Model</th><th>Grade</th><th>Vehicles</th>
                        <th>Accuracy</th><th>Time</th>
                    </tr>
                    ${analysis.comparison_results.map((model, index) => `
                    <tr class="${index === 0 ? 'best-model' : ''}">
                        <td>${index + 1}</td>
                        <td>${model.model_name}</td>
                        <td>${model.grade}</td>
                        <td>${model.total_vehicles}</td>
                        <td>${model.estimated_accuracy}</td>
                        <td>${model.processing_time}</td>
                    </tr>
                    `).join('')}
                </table>
            </div>
            ` : ''}

            <!-- Technical Details -->
            <div class="section">
                <h2>📋 Technical Details</h2>
                <table>
                    <tr><th>Parameter</th><th>Value</th></tr>
                    <tr><td>Analysis ID</td><td>${analysis.id}</td></tr>
                    <tr><td>User ID</td><td>${analysis.user_id}</td></tr>
                    <tr><td>Analysis Type</td><td>${analysis.analysis_type}</td></tr>
                    <tr><td>Model Version</td><td>${analysis.model_version}</td></tr>
                    <tr><td>Processing Time</td><td>${analysis.processing_time.toFixed(2)} seconds</td></tr>
                    <tr><td>Status</td><td>${analysis.success ? 'Success' : 'Failed'}</td></tr>
                    <tr><td>Created At</td><td>${timestamp}</td></tr>
                </table>
            </div>
        </div>
    </div>
</body>
</html>`
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading multi-model analysis history...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Multi-Model Analysis History</h1>
            <p className="text-gray-600">View and manage your previous multi-model traffic analyses</p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => {
                // Check if there's current analysis data to restore
                const currentAnalysis = localStorage.getItem('currentAnalysis')
                if (currentAnalysis) {
                  // User has analysis data to return to
                  sessionStorage.setItem('returnToAnalysis', 'true')
                  toast.success('Returning to your analysis results...')
                  router.push('/analysis')
                } else {
                  // No current analysis, check if user wants to start new analysis
                  toast('No current analysis session found. Would you like to start a new analysis?', {
                    icon: 'ℹ️',
                    duration: 4000
                  })
                  
                  // Give user option to start new analysis
                  setTimeout(() => {
                    const startNew = confirm('No analysis data found to return to. Would you like to start a new analysis?')
                    if (startNew) {
                      router.push('/upload')
                    }
                  }, 1000)
                }
              }}
              className="text-blue-600 hover:text-blue-800 px-4 py-2 rounded-lg border border-blue-200 hover:bg-blue-50 font-medium"
            >
              ← Back to Analysis
            </button>
            <button
              onClick={() => router.push('/reports')}
              className="text-green-600 hover:text-green-800 px-4 py-2 rounded-lg border border-green-200 hover:bg-green-50"
            >
              📄 Reports
            </button>
            <button
              onClick={() => router.push('/dashboard')}
              className="text-gray-600 hover:text-gray-800 px-4 py-2 rounded-lg border"
            >
              Dashboard
            </button>
            <button
              onClick={() => router.push('/upload')}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              New Analysis
            </button>
            <button
              onClick={logout}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Filter Info */}
        <div className="mb-6 p-4 bg-blue-50 border-l-4 border-blue-400 rounded-lg">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <span className="text-blue-400 text-xl">🔍</span>
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-700">
                <strong>Multi-Model Analysis History:</strong> Showing only comprehensive comparison analyses that used all 4 YOLO models 
                (YOLOv8, YOLOv11, YOLOv12, and Ensemble) for maximum accuracy and detailed performance comparison.
              </p>
              <p className="text-xs text-blue-600 mt-1">
                💡 These analyses provide the most detailed results with model rankings, accuracy comparisons, and performance metrics.
              </p>
            </div>
          </div>
        </div>

        {/* Analysis Grid */}
        {analysisHistory && analysisHistory.analyses.length > 0 ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {analysisHistory.analyses.map((analysis) => (
                <div key={analysis.id} className="bg-white rounded-xl shadow-sm border hover:shadow-md transition-shadow">
                  {/* Analysis Images */}
                  <div className="p-4">
                    <div className="grid grid-cols-2 gap-2 mb-4">
                      {/* Original Image */}
                      <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden">
                        {analysis.images?.original ? (
                          <img
                            src={`${process.env.NEXT_PUBLIC_MEDIA_URL || 'http://localhost:8000/media'}/${analysis.images.original}`}
                            alt="Original"
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.currentTarget.style.display = 'none'
                              const placeholder = e.currentTarget.nextElementSibling as HTMLElement
                              if (placeholder) placeholder.style.display = 'flex'
                            }}
                          />
                        ) : null}
                        <div 
                          className="w-full h-full flex items-center justify-center text-gray-500 text-xs"
                          style={{ display: analysis.images?.original ? 'none' : 'flex' }}
                        >
                          📷 Original
                        </div>
                      </div>

                      {/* Annotated Image */}
                      <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden">
                        {analysis.images?.best_model_annotated || analysis.images?.annotated ? (
                          <img
                            src={`${process.env.NEXT_PUBLIC_MEDIA_URL || 'http://localhost:8000/media'}/${analysis.images.best_model_annotated || analysis.images.annotated}`}
                            alt="Annotated"
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.currentTarget.style.display = 'none'
                              const placeholder = e.currentTarget.nextElementSibling as HTMLElement
                              if (placeholder) placeholder.style.display = 'flex'
                            }}
                          />
                        ) : null}
                        <div 
                          className="w-full h-full flex items-center justify-center text-gray-500 text-xs"
                          style={{ display: (analysis.images?.best_model_annotated || analysis.images?.annotated) ? 'none' : 'flex' }}
                        >
                          🎯 Annotated
                        </div>
                      </div>
                    </div>

                    {/* Analysis Info */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-medium text-gray-800">
                            {analysis.model_version}
                          </span>
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            🔄 Multi-Model
                          </span>
                        </div>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          analysis.success 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {analysis.success ? '✅ Success' : '❌ Failed'}
                        </span>
                      </div>

                      <div className="text-sm text-gray-600">
                        <div>📅 {new Date(analysis.created_at).toLocaleDateString()}</div>
                        <div>🚗 {analysis.vehicle_detection?.total_vehicles || 0} vehicles</div>
                        <div>⏱️ {analysis.processing_time.toFixed(2)}s</div>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex space-x-2 pt-2">
                        <button
                          onClick={() => handleViewAnalysis(analysis)}
                          className="flex-1 bg-blue-600 text-white px-3 py-2 rounded-lg text-sm hover:bg-blue-700"
                        >
                          View Details
                        </button>
                        <button
                          onClick={() => handleDownloadAnalysisReport(analysis)}
                          className="flex-1 bg-green-600 text-white px-3 py-2 rounded-lg text-sm hover:bg-green-700"
                        >
                          Download
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {analysisHistory.pagination.total_pages > 1 && (
              <div className="flex justify-center items-center space-x-4">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                  className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  Previous
                </button>
                
                <span className="text-sm text-gray-600">
                  Page {analysisHistory.pagination.current_page} of {analysisHistory.pagination.total_pages}
                  ({analysisHistory.pagination.total_count} total analyses)
                </span>
                
                <button
                  onClick={() => setCurrentPage(prev => Math.min(analysisHistory.pagination.total_pages, prev + 1))}
                  disabled={currentPage === analysisHistory.pagination.total_pages}
                  className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  Next
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📋</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">No Multi-Model Analysis History</h2>
            <p className="text-gray-600 mb-6">You haven't performed any multi-model analyses yet.</p>
            <button
              onClick={() => router.push('/upload')}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
            >
              Start Your First Analysis
            </button>
          </div>
        )}
      </main>

      {/* Analysis Detail Modal */}
      {showModal && selectedAnalysis && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-y-auto border-2 border-gray-300">
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-blue-600 to-blue-600 text-white p-6 rounded-t-2xl">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold text-white">Analysis Details</h2>
                  <p className="text-blue-100 font-medium">ID: {selectedAnalysis.id}</p>
                </div>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-white hover:text-gray-200 text-3xl font-bold bg-white bg-opacity-20 rounded-full w-10 h-10 flex items-center justify-center hover:bg-opacity-30 transition-all"
                >
                  ×
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="p-6 bg-white">
              {/* Images Section */}
              <div className="mb-6">
                <h3 className="text-xl font-bold mb-4 text-gray-900 border-b-2 border-blue-200 pb-2">📷 Analysis Images</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="border-2 border-gray-300 rounded-lg p-4 bg-gray-50">
                    <h4 className="font-bold mb-3 text-gray-900 text-lg">🖼️ Original Image</h4>
                    <div className="aspect-video bg-gray-200 rounded-lg overflow-hidden border-2 border-gray-300">
                      {selectedAnalysis.images?.original ? (
                        <img
                          src={`${process.env.NEXT_PUBLIC_MEDIA_URL || 'http://localhost:8000/media'}/${selectedAnalysis.images.original}`}
                          alt="Original"
                          className="w-full h-full object-contain"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-gray-700 font-medium">
                          📷 Original Image Not Available
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="border-2 border-gray-300 rounded-lg p-4 bg-gray-50">
                    <h4 className="font-bold mb-3 text-gray-900 text-lg">🎯 Annotated Image</h4>
                    <div className="aspect-video bg-gray-200 rounded-lg overflow-hidden border-2 border-gray-300">
                      {selectedAnalysis.images?.best_model_annotated || selectedAnalysis.images?.annotated ? (
                        <img
                          src={`${process.env.NEXT_PUBLIC_MEDIA_URL || 'http://localhost:8000/media'}/${selectedAnalysis.images.best_model_annotated || selectedAnalysis.images.annotated}`}
                          alt="Annotated"
                          className="w-full h-full object-contain"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-gray-700 font-medium">
                          🎯 Annotated Image Not Available
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Analysis Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-semibold mb-4 text-gray-900">📊 Analysis Summary</h3>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between p-2 bg-gray-50 rounded">
                      <span className="text-gray-800 font-medium">Status:</span>
                      <span className={`font-bold ${selectedAnalysis.success ? 'text-green-700' : 'text-red-700'}`}>
                        {selectedAnalysis.success ? '✅ Success' : '❌ Failed'}
                      </span>
                    </div>
                    <div className="flex justify-between p-2 bg-gray-50 rounded">
                      <span className="text-gray-800 font-medium">Model:</span>
                      <span className="font-bold text-gray-900">{selectedAnalysis.model_version}</span>
                    </div>
                    <div className="flex justify-between p-2 bg-gray-50 rounded">
                      <span className="text-gray-800 font-medium">Type:</span>
                      <span className="font-bold text-gray-900">{selectedAnalysis.analysis_type}</span>
                    </div>
                    <div className="flex justify-between p-2 bg-gray-50 rounded">
                      <span className="text-gray-800 font-medium">Vehicles:</span>
                      <span className="font-bold text-blue-700">{selectedAnalysis.vehicle_detection?.total_vehicles || 0}</span>
                    </div>
                    <div className="flex justify-between p-2 bg-gray-50 rounded">
                      <span className="text-gray-800 font-medium">Processing Time:</span>
                      <span className="font-bold text-blue-700">{selectedAnalysis.processing_time.toFixed(2)}s</span>
                    </div>
                    <div className="flex justify-between p-2 bg-gray-50 rounded">
                      <span className="text-gray-800 font-medium">Date:</span>
                      <span className="font-bold text-gray-900">{new Date(selectedAnalysis.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold mb-4 text-gray-900">🚗 Vehicle Detection</h3>
                  {selectedAnalysis.vehicle_detection?.detection_summary ? (
                    <div className="space-y-2 text-sm">
                      {Object.entries(selectedAnalysis.vehicle_detection.detection_summary).map(([type, count]) => (
                        <div key={type} className="flex justify-between p-2 bg-blue-50 rounded border border-blue-200">
                          <span className="text-gray-800 font-medium">{type}:</span>
                          <span className="font-bold text-blue-800">{count}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-700 text-sm bg-yellow-50 p-3 rounded border border-yellow-200">No detailed breakdown available</p>
                  )}
                </div>
              </div>

              {/* Model Comparison Results - Show ALL models, not just best */}
              {selectedAnalysis.comparison_results && selectedAnalysis.comparison_results.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold mb-4 text-gray-900">⚖️ All Model Results</h3>
                  <div className="bg-gray-50 rounded-lg p-4 border">
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="bg-gray-800 text-white">
                            <th className="p-3 text-left font-bold">Rank</th>
                            <th className="p-3 text-left font-bold">Model</th>
                            <th className="p-3 text-center font-bold">Grade</th>
                            <th className="p-3 text-center font-bold">Vehicles</th>
                            <th className="p-3 text-center font-bold">Accuracy</th>
                            <th className="p-3 text-center font-bold">Time</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedAnalysis.comparison_results.map((model, index) => (
                            <tr key={index} className={index === 0 ? 'bg-green-100 border-2 border-green-400' : 'bg-white'}>
                              <td className="p-3 border border-gray-300">
                                <div className="flex items-center">
                                  {index === 0 && <span className="text-lg mr-2">🏆</span>}
                                  {index === 1 && <span className="text-lg mr-2">🥈</span>}
                                  {index === 2 && <span className="text-lg mr-2">🥉</span>}
                                  <span className="font-bold text-gray-900">{index + 1}</span>
                                </div>
                              </td>
                              <td className="p-3 border border-gray-300">
                                <div className="font-bold text-gray-900">{model.model_name}</div>
                                {index === 0 && <div className="text-xs text-green-700 font-medium">SELECTED BEST</div>}
                              </td>
                              <td className="p-3 border border-gray-300 text-center">
                                <span className={`px-2 py-1 rounded font-bold text-sm ${
                                  model.grade === 'A+' || model.grade === 'A' ? 'bg-green-200 text-green-900' :
                                  model.grade === 'B+' || model.grade === 'B' ? 'bg-blue-200 text-blue-900' :
                                  'bg-yellow-200 text-yellow-900'
                                }`}>
                                  {model.grade}
                                </span>
                              </td>
                              <td className="p-3 border border-gray-300 text-center font-bold text-gray-900">{model.total_vehicles}</td>
                              <td className="p-3 border border-gray-300 text-center font-bold text-gray-900">{model.estimated_accuracy}</td>
                              <td className="p-3 border border-gray-300 text-center font-bold text-gray-900">{model.processing_time}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    
                    <div className="mt-4 p-3 bg-green-100 rounded border border-green-300">
                      <h4 className="font-bold text-green-900 mb-2">🏆 Why {selectedAnalysis.comparison_results[0].model_name} was selected:</h4>
                      <p className="text-green-800 font-medium text-sm">
                        Best overall performance with <strong>{selectedAnalysis.comparison_results[0].grade} grade</strong>, 
                        detecting <strong>{selectedAnalysis.comparison_results[0].total_vehicles} vehicles</strong> with 
                        <strong> {selectedAnalysis.comparison_results[0].estimated_accuracy} accuracy</strong> 
                        in <strong>{selectedAnalysis.comparison_results[0].processing_time}</strong>.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex justify-end space-x-4 mt-8 pt-6 border-t-2 border-gray-200 bg-gray-50 p-4 rounded-lg">
                <button
                  onClick={() => handleDownloadAnalysisReport(selectedAnalysis)}
                  className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 font-bold text-lg shadow-lg hover:shadow-xl transition-all"
                >
                  📄 Download Report
                </button>
                <button
                  onClick={() => setShowModal(false)}
                  className="bg-gray-700 text-white px-6 py-3 rounded-lg hover:bg-gray-800 font-bold text-lg shadow-lg hover:shadow-xl transition-all"
                >
                  ✕ Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}