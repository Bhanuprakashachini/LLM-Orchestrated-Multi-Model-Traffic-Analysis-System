'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter
} from 'recharts'
import { 
  ChartBarIcon,
  ClockIcon,
  TruckIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline'

interface VideoMetricsProps {
  analysisId: string
}

interface MetricsData {
  analysis_id: string
  video_metadata: any
  traffic_metrics: any
  time_series: Array<{
    timestamp: number
    vehicle_count: number
    congestion_index: number
    density_level: string
  }>
  vehicle_distribution: Record<string, number>
  speed_data: Array<{
    track_id: number
    vehicle_class: string
    avg_speed: number
    max_speed: number
  }>
  congestion_levels: Record<string, number>
  total_frames_analyzed: number
  total_vehicles_tracked: number
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']

const VideoMetrics: React.FC<VideoMetricsProps> = ({ analysisId }) => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    fetchMetrics()
  }, [analysisId])

  const fetchMetrics = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`/api/v1/analysis/video/${analysisId}/metrics/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch metrics')
      }

      const data = await response.json()
      setMetrics(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const formatSpeed = (speed: number): string => {
    return `${speed.toFixed(1)} km/h`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="text-center text-gray-500">
        No metrics data available
      </div>
    )
  }

  const tabs = [
    { id: 'overview', name: 'Overview', icon: ChartBarIcon },
    { id: 'timeline', name: 'Timeline', icon: ClockIcon },
    { id: 'vehicles', name: 'Vehicles', icon: TruckIcon },
    { id: 'performance', name: 'Performance', icon: ArrowTrendingUpIcon }
  ]

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          📊 Video Analysis Metrics
        </h1>
        <p className="text-gray-600">
          Comprehensive traffic analysis results and visualizations
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${
              activeTab === tab.id
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <tab.icon className="w-5 h-5" />
            <span>{tab.name}</span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Key Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
                <h3 className="text-blue-100 text-sm font-medium">Average Vehicles</h3>
                <p className="text-3xl font-bold">
                  {metrics.traffic_metrics.avg_vehicle_count?.toFixed(1) || 'N/A'}
                </p>
              </div>
              
              <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 text-white">
                <h3 className="text-green-100 text-sm font-medium">Peak Vehicles</h3>
                <p className="text-3xl font-bold">
                  {metrics.traffic_metrics.max_vehicle_count || 'N/A'}
                </p>
              </div>
              
              <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-6 text-white">
                <h3 className="text-purple-100 text-sm font-medium">Average Speed</h3>
                <p className="text-3xl font-bold">
                  {metrics.traffic_metrics.avg_speed ? 
                    formatSpeed(metrics.traffic_metrics.avg_speed) : 'N/A'}
                </p>
              </div>
              
              <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg p-6 text-white">
                <h3 className="text-orange-100 text-sm font-medium">Congestion Level</h3>
                <p className="text-3xl font-bold">
                  {metrics.traffic_metrics.congestion_index?.toFixed(2) || 'N/A'}
                  <span className="text-sm text-orange-100 ml-1">index</span>
                </p>
              </div>
            </div>

            {/* Vehicle Distribution */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Vehicle Type Distribution
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={Object.entries(metrics.vehicle_distribution).map(([type, count]) => ({
                        name: type.charAt(0).toUpperCase() + type.slice(1),
                        value: count
                      }))}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${percent ? (percent * 100).toFixed(0) : 0}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {Object.entries(metrics.vehicle_distribution).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Congestion Level Distribution
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={Object.entries(metrics.congestion_levels).map(([level, count]) => ({
                    level: level.charAt(0).toUpperCase() + level.slice(1),
                    count
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="level" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#3B82F6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'timeline' && (
          <div className="space-y-6">
            {/* Vehicle Count Over Time */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Vehicle Count Over Time
              </h3>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={metrics.time_series}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(value) => formatTime(value)}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(value) => `Time: ${formatTime(value)}`}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="vehicle_count" 
                    stroke="#3B82F6" 
                    strokeWidth={2}
                    name="Vehicle Count"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Congestion Index Over Time */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Congestion Index Over Time
              </h3>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={metrics.time_series}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(value) => formatTime(value)}
                  />
                  <YAxis domain={[0, 1]} />
                  <Tooltip 
                    labelFormatter={(value) => `Time: ${formatTime(value)}`}
                    formatter={(value) => [`${(Number(value) * 100).toFixed(1)}%`, 'Congestion Index']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="congestion_index" 
                    stroke="#EF4444" 
                    strokeWidth={2}
                    name="Congestion Index"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {activeTab === 'vehicles' && (
          <div className="space-y-6">
            {/* Speed Distribution */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Vehicle Speed Distribution
              </h3>
              <ResponsiveContainer width="100%" height={400}>
                <ScatterChart data={metrics.speed_data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="avg_speed" 
                    name="Average Speed"
                    unit=" km/h"
                  />
                  <YAxis 
                    dataKey="max_speed" 
                    name="Max Speed"
                    unit=" km/h"
                  />
                  <Tooltip 
                    cursor={{ strokeDasharray: '3 3' }}
                    formatter={(value, name) => [
                      `${value} km/h`, 
                      name === 'avg_speed' ? 'Average Speed' : 'Max Speed'
                    ]}
                  />
                  <Scatter 
                    dataKey="avg_speed" 
                    fill="#3B82F6"
                    name="Average Speed"
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>

            {/* Vehicle Tracking Summary */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Vehicle Tracking Summary
              </h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Track ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Vehicle Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Avg Speed
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Max Speed
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {metrics.speed_data.slice(0, 10).map((vehicle, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {vehicle.track_id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span className="capitalize">{vehicle.vehicle_class}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatSpeed(vehicle.avg_speed)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatSpeed(vehicle.max_speed)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'performance' && (
          <div className="space-y-6">
            {/* Performance Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Processing Performance
                </h3>
                <div className="space-y-4">
                  <div>
                    <span className="text-gray-600">Processing FPS:</span>
                    <span className="ml-2 font-medium">
                      {metrics.traffic_metrics.avg_processing_fps?.toFixed(2) || 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Total Processing Time:</span>
                    <span className="ml-2 font-medium">
                      {metrics.traffic_metrics.total_processing_time?.toFixed(1) || 'N/A'}s
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Detection Accuracy:</span>
                    <span className="ml-2 font-medium">
                      {metrics.traffic_metrics.detection_accuracy ? 
                        `${(metrics.traffic_metrics.detection_accuracy * 100).toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Video Statistics
                </h3>
                <div className="space-y-4">
                  <div>
                    <span className="text-gray-600">Frames Analyzed:</span>
                    <span className="ml-2 font-medium">
                      {metrics.total_frames_analyzed.toLocaleString()}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Vehicles Tracked:</span>
                    <span className="ml-2 font-medium">
                      {metrics.total_vehicles_tracked}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Video Duration:</span>
                    <span className="ml-2 font-medium">
                      {formatTime(metrics.video_metadata.duration)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Traffic Flow Metrics
                </h3>
                <div className="space-y-4">
                  <div>
                    <span className="text-gray-600">Vehicles/Minute:</span>
                    <span className="ml-2 font-medium">
                      {metrics.traffic_metrics.vehicles_per_minute?.toFixed(1) || 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Congestion Duration:</span>
                    <span className="ml-2 font-medium">
                      {metrics.traffic_metrics.congestion_duration ? 
                        formatTime(metrics.traffic_metrics.congestion_duration) : 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Congestion %:</span>
                    <span className="ml-2 font-medium">
                      {metrics.traffic_metrics.congestion_percentage?.toFixed(1) || 'N/A'}%
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* System Performance Chart */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Processing Performance Over Time
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={metrics.time_series.map((item, index) => ({
                  ...item,
                  frame_number: index + 1
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="frame_number" />
                  <YAxis />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="vehicle_count" 
                    stroke="#3B82F6" 
                    strokeWidth={2}
                    name="Vehicles Detected"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  )
}

export default VideoMetrics