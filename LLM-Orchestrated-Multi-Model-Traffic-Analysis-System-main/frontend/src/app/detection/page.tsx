'use client'

import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

export default function VehicleDetectionPage() {
  const { user } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const analysisId = searchParams.get('analysisId')

  const detectedVehicles = [
    { id: 1, type: 'Car', confidence: 95.2, bbox: [120, 180, 280, 320], color: 'Blue' },
    { id: 2, type: 'Truck', confidence: 88.7, bbox: [350, 120, 520, 380], color: 'Red' },
    { id: 3, type: 'Motorcycle', confidence: 92.1, bbox: [580, 200, 620, 260], color: 'Black' },
    { id: 4, type: 'Bus', confidence: 96.8, bbox: [80, 100, 300, 280], color: 'Yellow' },
    { id: 5, type: 'Car', confidence: 89.3, bbox: [400, 250, 560, 390], color: 'White' }
  ]

  const vehicleStats = {
    total: detectedVehicles.length,
    cars: detectedVehicles.filter(v => v.type === 'Car').length,
    trucks: detectedVehicles.filter(v => v.type === 'Truck').length,
    motorcycles: detectedVehicles.filter(v => v.type === 'Motorcycle').length,
    buses: detectedVehicles.filter(v => v.type === 'Bus').length,
    avgConfidence: detectedVehicles.reduce((sum, v) => sum + v.confidence, 0) / detectedVehicles.length
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
              <h1 className="text-2xl font-bold text-purple-700">Vehicle Detection Module</h1>
            </div>
            <div className="text-sm text-gray-600">
              Analysis ID: {analysisId || 'N/A'}
            </div>
          </div>
        </div>
      </header>

      <main className="p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Overview Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-xl shadow-sm border border-purple-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Vehicles</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">{vehicleStats.total}</p>
                </div>
                <div className="p-3 rounded-lg bg-blue-100">
                  <span className="text-blue-600 text-xl">🚗</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-purple-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Confidence</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">{vehicleStats.avgConfidence.toFixed(1)}%</p>
                </div>
                <div className="p-3 rounded-lg bg-green-100">
                  <span className="text-green-600 text-xl">✅</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-purple-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Cars Detected</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">{vehicleStats.cars}</p>
                </div>
                <div className="p-3 rounded-lg bg-purple-100">
                  <span className="text-purple-600 text-xl">🚙</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-purple-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Heavy Vehicles</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">{vehicleStats.trucks + vehicleStats.buses}</p>
                </div>
                <div className="p-3 rounded-lg bg-orange-100">
                  <span className="text-orange-600 text-xl">🚛</span>
                </div>
              </div>
            </div>
          </div>

          {/* Detection Results */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Image with Bounding Boxes */}
            <div className="bg-white rounded-xl shadow-sm border border-purple-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Detection Visualization
              </h3>
              <div className="aspect-video bg-gray-100 rounded-lg relative overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <div className="text-4xl mb-2">🖼️</div>
                    <p>Original image with bounding boxes</p>
                    <p className="text-sm mt-1">YOLOv8 Detection Results</p>
                  </div>
                </div>
                {/* Simulated bounding boxes */}
                {detectedVehicles.map((vehicle) => (
                  <div
                    key={vehicle.id}
                    className="absolute border-2 border-red-500 bg-red-500 bg-opacity-10"
                    style={{
                      left: `${(vehicle.bbox[0] / 640) * 100}%`,
                      top: `${(vehicle.bbox[1] / 480) * 100}%`,
                      width: `${((vehicle.bbox[2] - vehicle.bbox[0]) / 640) * 100}%`,
                      height: `${((vehicle.bbox[3] - vehicle.bbox[1]) / 480) * 100}%`,
                    }}
                  >
                    <div className="absolute -top-6 left-0 bg-red-500 text-white text-xs px-2 py-1 rounded">
                      {vehicle.type} {vehicle.confidence.toFixed(1)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Vehicle Classification */}
            <div className="bg-white rounded-xl shadow-sm border border-purple-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Vehicle Classification
              </h3>
              <div className="space-y-4">
                {[
                  { type: 'Cars', count: vehicleStats.cars, color: 'bg-blue-500', icon: '🚗' },
                  { type: 'Trucks', count: vehicleStats.trucks, color: 'bg-red-500', icon: '🚛' },
                  { type: 'Motorcycles', count: vehicleStats.motorcycles, color: 'bg-green-500', icon: '🏍️' },
                  { type: 'Buses', count: vehicleStats.buses, color: 'bg-yellow-500', icon: '🚌' }
                ].map((category) => (
                  <div key={category.type} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className="text-xl">{category.icon}</span>
                      <span className="font-medium text-gray-900">{category.type}</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div 
                          className={`${category.color} h-2 rounded-full`}
                          style={{ width: `${(category.count / vehicleStats.total) * 100}%` }}
                        ></div>
                      </div>
                      <span className="font-semibold text-gray-900 w-8">{category.count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Detailed Detection Table */}
          <div className="bg-white rounded-xl shadow-sm border border-purple-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Detailed Detection Results
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-medium text-gray-900">ID</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Vehicle Type</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Confidence</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Bounding Box</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Color</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {detectedVehicles.map((vehicle) => (
                    <tr key={vehicle.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 text-gray-900">#{vehicle.id}</td>
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-2">
                          <span className="text-lg">
                            {vehicle.type === 'Car' ? '🚗' : 
                             vehicle.type === 'Truck' ? '🚛' :
                             vehicle.type === 'Motorcycle' ? '🏍️' : '🚌'}
                          </span>
                          <span className="font-medium text-gray-900">{vehicle.type}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          vehicle.confidence >= 95 ? 'bg-green-100 text-green-700' :
                          vehicle.confidence >= 90 ? 'bg-yellow-100 text-yellow-700' :
                          'bg-orange-100 text-orange-700'
                        }`}>
                          {vehicle.confidence.toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600">
                        [{vehicle.bbox.join(', ')}]
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-sm">
                          {vehicle.color}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                          Detected
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Model Performance */}
          <div className="bg-white rounded-xl shadow-sm border border-purple-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              YOLOv8 Model Performance
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600 mb-1">98.2%</div>
                <div className="text-sm text-gray-600">Precision</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600 mb-1">96.7%</div>
                <div className="text-sm text-gray-600">Recall</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600 mb-1">45 FPS</div>
                <div className="text-sm text-gray-600">Processing Speed</div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}