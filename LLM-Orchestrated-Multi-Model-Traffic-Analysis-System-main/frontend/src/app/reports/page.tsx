'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

interface AnalysisReport {
  id: number
  created_at: string
  model_version: string
  processing_time: number
  fps: number
  file_size: number
  vehicle_detection: any
  traffic_density: any
  analysis_type: string
}

export default function ReportsPage() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [analyses, setAnalyses] = useState<AnalysisReport[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedAnalyses, setSelectedAnalyses] = useState<number[]>([])
  const [reportFormat, setReportFormat] = useState<'csv' | 'json'>('csv')
  const [isGenerating, setIsGenerating] = useState(false)

  useEffect(() => {
    if (!user) {
      router.push('/login')
      return
    }

    const fetchAnalyses = async () => {
      setIsLoading(true)
      try {
        const token = localStorage.getItem('access_token')
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/analysis/history/`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.ok) {
          const data = await response.json()
          setAnalyses(data.results || [])
        } else {
          console.error('Failed to fetch analyses for reports')
          toast.error('Failed to load analysis data')
          setAnalyses([])
        }
      } catch (error) {
        console.error('Error fetching analyses:', error)
        toast.error('Error loading analysis data')
        setAnalyses([])
      } finally {
        setIsLoading(false)
      }
    }

    fetchAnalyses()
  }, [user, router])

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const handleSelectAll = () => {
    if (selectedAnalyses.length === analyses.length) {
      setSelectedAnalyses([])
    } else {
      setSelectedAnalyses(analyses.map(a => a.id))
    }
  }

  const handleSelectAnalysis = (id: number) => {
    setSelectedAnalyses(prev => 
      prev.includes(id) 
        ? prev.filter(analysisId => analysisId !== id)
        : [...prev, id]
    )
  }

  const downloadSingleReport = async (analysisId: number) => {
    try {
      setIsGenerating(true)
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/analysis/download/${analysisId}/?format=${reportFormat}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        }
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.style.display = 'none'
        a.href = url
        a.download = `analysis_${analysisId}.${reportFormat}`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        toast.success('Report downloaded successfully')
      } else {
        toast.error('Failed to download report')
      }
    } catch (error) {
      console.error('Error downloading report:', error)
      toast.error('Error downloading report')
    } finally {
      setIsGenerating(false)
    }
  }

  const generateBulkReport = async () => {
    if (selectedAnalyses.length === 0) {
      toast.error('Please select at least one analysis')
      return
    }

    try {
      setIsGenerating(true)
      
      // For bulk reports, we'll generate a combined report
      const selectedData = analyses.filter(a => selectedAnalyses.includes(a.id))
      
      if (reportFormat === 'csv') {
        generateCSVReport(selectedData)
      } else {
        generateJSONReport(selectedData)
      }
      
      toast.success(`Bulk ${reportFormat.toUpperCase()} report generated successfully`)
    } catch (error) {
      console.error('Error generating bulk report:', error)
      toast.error('Error generating bulk report')
    } finally {
      setIsGenerating(false)
    }
  }

  const generateCSVReport = (data: AnalysisReport[]) => {
    const headers = [
      'Analysis ID',
      'Date',
      'Model Version',
      'Processing Time (s)',
      'FPS',
      'File Size',
      'Total Vehicles',
      'Traffic Density',
      'Congestion Index',
      'Analysis Type'
    ]

    const rows = data.map(analysis => [
      analysis.id,
      formatDate(analysis.created_at),
      analysis.model_version,
      analysis.processing_time,
      analysis.fps,
      formatFileSize(analysis.file_size),
      analysis.vehicle_detection?.total_vehicles || 0,
      analysis.traffic_density?.density_level || 'Unknown',
      analysis.traffic_density?.congestion_index || 0,
      analysis.analysis_type
    ])

    const csvContent = [headers, ...rows]
      .map(row => row.map(field => `"${field}"`).join(','))
      .join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `bulk_analysis_report_${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }

  const generateJSONReport = (data: AnalysisReport[]) => {
    const report = {
      generated_at: new Date().toISOString(),
      total_analyses: data.length,
      analyses: data,
      summary: {
        total_vehicles: data.reduce((sum, a) => sum + (a.vehicle_detection?.total_vehicles || 0), 0),
        average_processing_time: data.reduce((sum, a) => sum + a.processing_time, 0) / data.length,
        average_fps: data.reduce((sum, a) => sum + a.fps, 0) / data.length,
        model_distribution: data.reduce((acc, a) => {
          acc[a.model_version] = (acc[a.model_version] || 0) + 1
          return acc
        }, {} as Record<string, number>)
      }
    }

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `bulk_analysis_report_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }

  if (!user) {
    return null
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-green-200">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/dashboard')}
                className="flex items-center text-green-600 hover:text-green-700 transition-colors"
              >
                <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Dashboard
              </button>
              <h1 className="text-2xl font-bold text-green-700">
                Analysis Reports
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/upload')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                New Analysis
              </button>
              <button
                onClick={logout}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Report Controls */}
          <div className="bg-white rounded-lg shadow-sm border border-green-200 p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Report Generation</h2>
            
            <div className="flex flex-wrap items-center gap-4 mb-4">
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">Format:</label>
                <select
                  value={reportFormat}
                  onChange={(e) => setReportFormat(e.target.value as 'csv' | 'json')}
                  className="border border-gray-300 rounded-md px-3 py-1 text-sm"
                >
                  <option value="csv">CSV</option>
                  <option value="json">JSON</option>
                </select>
              </div>
              
              <button
                onClick={handleSelectAll}
                className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                {selectedAnalyses.length === analyses.length ? 'Deselect All' : 'Select All'}
              </button>
              
              <button
                onClick={generateBulkReport}
                disabled={selectedAnalyses.length === 0 || isGenerating}
                className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {isGenerating ? 'Generating...' : `Generate Report (${selectedAnalyses.length} selected)`}
              </button>
            </div>
            
            <p className="text-sm text-gray-600">
              Select analyses to include in your bulk report, or download individual reports using the download buttons in the table.
            </p>
          </div>

          {/* Analysis Table */}
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
              <p className="ml-4 text-gray-600">Loading analysis data...</p>
            </div>
          ) : analyses.length === 0 ? (
            <div className="bg-white rounded-lg shadow-lg p-12 text-center">
              <div className="text-gray-400 mb-4">
                <svg className="mx-auto h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-medium text-gray-900 mb-2">No Analysis Data</h3>
              <p className="text-gray-500 mb-6">You haven't performed any traffic analysis yet.</p>
              <button
                onClick={() => router.push('/upload')}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                Start Your First Analysis
              </button>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border border-green-200 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <input
                          type="checkbox"
                          checked={selectedAnalyses.length === analyses.length && analyses.length > 0}
                          onChange={handleSelectAll}
                          className="rounded border-gray-300"
                        />
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Analysis
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Model
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Vehicles
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Performance
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {analyses.map((analysis) => (
                      <tr key={analysis.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="checkbox"
                            checked={selectedAnalyses.includes(analysis.id)}
                            onChange={() => handleSelectAnalysis(analysis.id)}
                            className="rounded border-gray-300"
                          />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">#{analysis.id}</div>
                            <div className="text-sm text-gray-500">{formatDate(analysis.created_at)}</div>
                            <div className="text-xs text-gray-400">{formatFileSize(analysis.file_size)}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                            {analysis.model_version}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {analysis.vehicle_detection?.total_vehicles || 0} vehicles
                            </div>
                            <div className="text-sm text-gray-500">
                              {analysis.vehicle_detection?.total_vehicles || 0} vehicles detected
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm text-gray-900">{analysis.processing_time.toFixed(2)}s</div>
                            <div className="text-sm text-gray-500">{analysis.fps.toFixed(1)} FPS</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => downloadSingleReport(analysis.id)}
                            disabled={isGenerating}
                            className="text-green-600 hover:text-green-900 disabled:text-gray-400 disabled:cursor-not-allowed mr-4"
                          >
                            Download
                          </button>
                          <button
                            onClick={() => router.push(`/analysis?id=${analysis.id}`)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            View
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}