'use client'

import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

export default function TrafficDensityPage() {
  const { user } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const analysisId = searchParams.get('analysisId')

  const densityData = {
    overall: 'Heavy',
    percentage: 78,
    vehicleCount: 42,
    areaOccupancy: 65,
    congestionLevel: 'High',
    zones: [
      { id: 1, name: 'Zone A (Left)', density: 'Medium', vehicles: 12, occupancy: 45 },
      { id: 2, name: 'Zone B (Center)', density: 'Heavy', vehicles: 18, occupancy: 82 },
      { id: 3, name: 'Zone C (Right)', density: 'Congested', vehicles: 12, occupancy: 95 }
    ],
    timeAnalysis: [
      { time: '10:00', density: 35, vehicles: 15 },
      { time: '10:15', density: 52, vehicles: 23 },
      { time: '10:30', density: 68, vehicles: 31 },
      { time: '10:45', density: 78, vehicles: 42 },
      { time: '11:00', density: 72, vehicles: 38 }
    ]
  }

  const getDensityColor = (density: string) => {
    switch (density) {
      case 'Low': return 'text-green-600 bg-green-100'
      case 'Medium': return 'text-yellow-600 bg-yellow-100'
      case 'Heavy': return 'text-orange-600 bg-orange-100'
      case 'Congested': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-white">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-purple-200">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/upload')}
                className="text-purple-600 hover:text-purple-800 flex items-center"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Results
              </button>
              <h1 className="text-2xl font-bold text-purple-700">Traffic Density Estimation</h1>
            </div>
            <div className="text-sm text-gray-600">
              Analysis ID: {analysisId || 'N/A'}
            </div>
          </div>
        </div>
      </header>

      <main className="p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Overall Density Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-xl shadow-sm border border-purple-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Overall Density</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{densityData.overall}</p>
                  <p className="text-sm text-gray-500 mt-1">{densityData.percentage}% occupied</p>
                </div>
                <div className="p-3 rounded-lg bg-orange-100">
                  <span className="text-orange-600 text-xl">📊</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-purple-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Vehicle Count</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{densityData.vehicleCount}</p>
                  <p className="text-sm text-gray-500 mt-1">Total vehicles</p>
                </div>
                <div className="p-3 rounded-lg bg-blue-100">
                  <span className="text-blue-600 text-xl">🚗</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-purple-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Area Occupancy</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{densityData.areaOccupancy}%</p>
                  <p className="text-sm text-gray-500 mt-1">Road coverage</p>
                </div>
                <div className="p-3 rounded-lg bg-purple-100">
                  <span className="text-purple-600 text-xl">📏</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-purple-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Congestion Level</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{densityData.congestionLevel}</p>
                  <p className="text-sm text-gray-500 mt-1">Traffic status</p>
                </div>
                <div className="p-3 rounded-lg bg-red-100">
                  <span className="text-red-600 text-xl">🚨</span>
                </div>
              </div>
            </div>
          </div>

          {/* Density Visualization */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Heatmap Visualization */}
            <div className="bg-white rounded-xl shadow-sm border border-purple-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Density Heatmap
              </h3>
              <div className="aspect-video bg-gradient-to-br from-green-200 via-yellow-200 via-orange-200 to-red-200 rounded-lg relative overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center text-gray-700">
                    <div className="text-4xl mb-2">🔥</div>
                    <p className="font-medium">Traffic Density Heatmap</p>
                    <p className="text-sm mt-1">Red = High Density, Green = Low Density</p>
                  </div>
                </div>
                {/* Simulated heat zones */}
                <div className="absolute top-4 left-4 w-16 h-16 bg-yellow-400 opacity-60 rounded-full"></div>
                <div className="absolute top-8 right-8 w-20 h-20 bg-red-500 opacity-70 rounded-full"></div>
                <div className="absolute bottom-6 left-1/3 w-24 h-24 bg-orange-400 opacity-65 rounded-full"></div>
              </div>
              
              {/* Legend */}
              <div className="mt-4 flex items-center justify-between text-sm">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-green-400 rounded"></div>
                    <span>Low</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-yellow-400 rounded"></div>
                    <span>Medium</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-orange-400 rounded"></div>
                    <span>Heavy</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-red-500 rounded"></div>
                    <span>Congested</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Zone Analysis */}
            <div className="bg-white rounded-xl shadow-sm border border-purple-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Zone-wise Analysis
              </h3>
              <div className="space-y-4">
                {densityData.zones.map((zone) => (
                  <div key={zone.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-gray-900">{zone.name}</h4>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getDensityColor(zone.density)}`}>
                        {zone.density}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Vehicles:</span>
                        <span className="font-medium ml-2">{zone.vehicles}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Occupancy:</span>
                        <span className="font-medium ml-2">{zone.occupancy}%</span>
                      </div>
                    </div>
                    <div className="mt-3">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            zone.occupancy >= 80 ? 'bg-red-500' :
                            zone.occupancy >= 60 ? 'bg-orange-500' :
                            zone.occupancy >= 40 ? 'bg-yellow-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${zone.occupancy}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Time-based Analysis */}
          <div className="bg-white rounded-xl shadow-sm border border-purple-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Density Trend Analysis
            </h3>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Chart Area */}
              <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                <div className="text-center text-gray-500">
                  <div className="text-4xl mb-2">📈</div>
                  <p>Density Trend Chart</p>
                  <p className="text-sm mt-1">Time vs Traffic Density</p>
                </div>
              </div>
              
              {/* Data Table */}
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Time-based Data</h4>
                <div className="space-y-2">
                  {densityData.timeAnalysis.map((data, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="font-medium text-gray-900">{data.time}</span>
                      <div className="flex items-center space-x-4">
                        <span className="text-sm text-gray-600">{data.vehicles} vehicles</span>
                        <div className="w-20 bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${
                              data.density >= 70 ? 'bg-red-500' :
                              data.density >= 50 ? 'bg-orange-500' :
                              data.density >= 30 ? 'bg-yellow-500' : 'bg-green-500'
                            }`}
                            style={{ width: `${data.density}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium text-gray-900">{data.density}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Density Classification */}
          <div className="bg-white rounded-xl shadow-sm border border-purple-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Density Classification Criteria
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { level: 'Low', range: '0-25%', color: 'bg-green-100 text-green-700', vehicles: '0-10', description: 'Free flow traffic' },
                { level: 'Medium', range: '26-50%', color: 'bg-yellow-100 text-yellow-700', vehicles: '11-25', description: 'Stable traffic flow' },
                { level: 'Heavy', range: '51-75%', color: 'bg-orange-100 text-orange-700', vehicles: '26-40', description: 'Reduced speed' },
                { level: 'Congested', range: '76-100%', color: 'bg-red-100 text-red-700', vehicles: '40+', description: 'Stop-and-go traffic' }
              ].map((category) => (
                <div key={category.level} className="border border-gray-200 rounded-lg p-4">
                  <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium mb-3 ${category.color}`}>
                    {category.level}
                  </div>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-gray-600">Occupancy:</span>
                      <span className="font-medium ml-1">{category.range}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Vehicles:</span>
                      <span className="font-medium ml-1">{category.vehicles}</span>
                    </div>
                    <p className="text-gray-600 text-xs mt-2">{category.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* AI Model Info */}
          <div className="bg-white rounded-xl shadow-sm border border-purple-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              AI Model Performance
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600 mb-1">94.8%</div>
                <div className="text-sm text-gray-600">Density Accuracy</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600 mb-1">0.23s</div>
                <div className="text-sm text-gray-600">Processing Time</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600 mb-1">CNN</div>
                <div className="text-sm text-gray-600">Model Architecture</div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}