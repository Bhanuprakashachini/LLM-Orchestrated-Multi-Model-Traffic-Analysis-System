'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  PlayIcon,
  EyeIcon,
  DocumentArrowDownIcon,
  ChartBarIcon,
  ClockIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  FunnelIcon
} from '@heroicons/react/24/outline'

interface VideoAnalysis {
  id: string
  file_path: string
  file_type: string
  status: string
  vehicle_count: number
  vehicle_counts: Record<string, number>
  congestion_level: string
  congestion_index: number
  video_metadata: {
    duration: number
    fps: number
    total_frames: number
    resolution: [number, number]
    file_size: number
    format: string
  }
  traffic_metrics: any
  frames_analyzed: number
  vehicles_tracked: number
  processing_time: number
  annotated_file_path?: string
  thumbnail_path?: string
  created_at: string
  updated_at: string
}

interface VideoHistoryProps {
  onViewMetrics?: (analysisId: string) => void
}

const VideoHistory: React.FC<VideoHistoryProps> = ({ onViewMetrics }) => {
  const [analyses, setAnalyses] = useState<VideoAnalysis[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  useEffect(() => {
    fetchAnalyses()
  }, [page, sortBy, sortOrder])

  const fetchAnalyses = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '10',
        sort_by: sortBy,
        sort_order: sortOrder,
        file_type: 'video'
      })

      const response = await fetch(`/api/v1/analysis/history/?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch video analyses')
      }

      const data = await response.json()
      setAnalyses(data.results || [])
      setTotalPages(data.total_pages || 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const downloadReport = async (analysisId: string, format: 'json' | 'csv') => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `/api/v1/analysis/video/${analysisId}/download/?format=${format}`,
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
      a.download = `video_analysis_${analysisId}.${format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      console.error('Download failed:', err)
    }
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

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'processing':
        return 'bg-yellow-100 text-yellow-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getCongestionColor = (level: string): string => {
    switch (level) {
      case 'low':
        return 'bg-green-100 text-green-800'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800'
      case 'high':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const filteredAnalyses = analyses.filter(analysis => {
    const matchesSearch = analysis.file_path.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'all' || analysis.status === statusFilter
    return matchesSearch && matchesStatus
  })

  if (loading && analyses.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          🎥 Video Analysis History
        </h1>
        <p className="text-gray-600">
          View and manage your video traffic analysis results
        </p>
      </div>

      {/* Filters and Search */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search videos..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Status Filter */}
          <div className="relative">
            <FunnelIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>
          </div>

          {/* Sort By */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="created_at">Date Created</option>
            <option value="vehicle_count">Vehicle Count</option>
            <option value="processing_time">Processing Time</option>
            <option value="congestion_index">Congestion Level</option>
          </select>

          {/* Sort Order */}
          <select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}
            className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>
      </div>

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

      {/* Analysis Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        <AnimatePresence>
          {filteredAnalyses.map((analysis, index) => (
            <motion.div
              key={analysis.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-shadow"
            >
              {/* Thumbnail */}
              <div className="relative h-48 bg-gray-200">
                {analysis.thumbnail_path ? (
                  <img
                    src={`/media/${analysis.thumbnail_path}`}
                    alt="Video thumbnail"
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none'
                    }}
                  />
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <PlayIcon className="w-16 h-16 text-gray-400" />
                  </div>
                )}
                
                {/* Status Badge */}
                <div className="absolute top-2 right-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(analysis.status)}`}>
                    {analysis.status.toUpperCase()}
                  </span>
                </div>
              </div>

              {/* Content */}
              <div className="p-4 space-y-3">
                {/* File Info */}
                <div>
                  <h3 className="font-semibold text-gray-900 truncate">
                    {analysis.file_path.split('/').pop()}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {formatDate(analysis.created_at)}
                  </p>
                </div>

                {/* Video Metadata */}
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-600">Duration:</span>
                    <span className="ml-1 font-medium">
                      {formatDuration(analysis.video_metadata.duration)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Size:</span>
                    <span className="ml-1 font-medium">
                      {formatFileSize(analysis.video_metadata.file_size)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Resolution:</span>
                    <span className="ml-1 font-medium">
                      {analysis.video_metadata.resolution.join('×')}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">FPS:</span>
                    <span className="ml-1 font-medium">
                      {analysis.video_metadata.fps.toFixed(1)}
                    </span>
                  </div>
                </div>

                {/* Analysis Results */}
                {analysis.status === 'completed' && (
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Vehicles:</span>
                      <span className="font-semibold text-blue-600">
                        {analysis.vehicle_count}
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Congestion:</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCongestionColor(analysis.congestion_level)}`}>
                        {analysis.congestion_level.toUpperCase()}
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Tracked:</span>
                      <span className="font-medium">
                        {analysis.vehicles_tracked || 0}
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Processing:</span>
                      <span className="font-medium">
                        {analysis.processing_time?.toFixed(1) || 0}s
                      </span>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex flex-wrap gap-2 pt-2">
                  {analysis.status === 'completed' && (
                    <>
                      <button
                        onClick={() => onViewMetrics?.(analysis.id)}
                        className="flex items-center space-x-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors text-sm"
                      >
                        <ChartBarIcon className="w-4 h-4" />
                        <span>Metrics</span>
                      </button>

                      {analysis.annotated_file_path && (
                        <a
                          href={`/media/${analysis.annotated_file_path}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center space-x-1 px-3 py-1 bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors text-sm"
                        >
                          <PlayIcon className="w-4 h-4" />
                          <span>Video</span>
                        </a>
                      )}

                      <button
                        onClick={() => downloadReport(analysis.id, 'json')}
                        className="flex items-center space-x-1 px-3 py-1 bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200 transition-colors text-sm"
                      >
                        <DocumentArrowDownIcon className="w-4 h-4" />
                        <span>JSON</span>
                      </button>

                      <button
                        onClick={() => downloadReport(analysis.id, 'csv')}
                        className="flex items-center space-x-1 px-3 py-1 bg-orange-100 text-orange-700 rounded-md hover:bg-orange-200 transition-colors text-sm"
                      >
                        <DocumentArrowDownIcon className="w-4 h-4" />
                        <span>CSV</span>
                      </button>
                    </>
                  )}

                  {analysis.status === 'processing' && (
                    <div className="flex items-center space-x-2 text-sm text-yellow-600">
                      <ClockIcon className="w-4 h-4 animate-spin" />
                      <span>Processing...</span>
                    </div>
                  )}

                  {analysis.status === 'failed' && (
                    <div className="text-sm text-red-600">
                      Analysis failed
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Empty State */}
      {filteredAnalyses.length === 0 && !loading && (
        <div className="text-center py-12">
          <PlayIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No video analyses found
          </h3>
          <p className="text-gray-600">
            {searchTerm || statusFilter !== 'all' 
              ? 'Try adjusting your search or filters'
              : 'Upload your first video to get started'
            }
          </p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center space-x-2">
          <button
            onClick={() => setPage(page - 1)}
            disabled={page === 1}
            className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Previous
          </button>
          
          <span className="px-4 py-2 text-gray-600">
            Page {page} of {totalPages}
          </span>
          
          <button
            onClick={() => setPage(page + 1)}
            disabled={page === totalPages}
            className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}

export default VideoHistory