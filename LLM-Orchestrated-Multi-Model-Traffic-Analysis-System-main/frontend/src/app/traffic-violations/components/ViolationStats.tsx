'use client'

interface ViolationStatsData {
  total_violations: number
  speed_violations: number
  helmet_violations: number
  vehicle_counts: {
    cars: number
    bikes: number
    buses: number
    trucks: number
    total: number
  }
}

interface ViolationStatsProps {
  stats: ViolationStatsData
}

export default function ViolationStats({ stats }: ViolationStatsProps) {
  const violationRate = stats.vehicle_counts.total > 0 
    ? ((stats.total_violations / stats.vehicle_counts.total) * 100).toFixed(1)
    : '0.0'

  return (
    <div className="bg-white rounded-xl shadow-sm border p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <span className="mr-2">📊</span>
        Live Statistics
      </h3>

      {/* Main Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-red-50 rounded-lg p-4 border border-red-200 text-center">
          <div className="text-2xl font-bold text-red-700">{stats.total_violations}</div>
          <div className="text-sm text-red-600 font-medium">Total Violations</div>
        </div>
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200 text-center">
          <div className="text-2xl font-bold text-blue-700">{stats.vehicle_counts.total}</div>
          <div className="text-sm text-blue-600 font-medium">Total Vehicles</div>
        </div>
      </div>

      {/* Violation Breakdown */}
      <div className="mb-6">
        <h4 className="font-semibold text-gray-900 mb-3">🚨 Violation Types</h4>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-200">
            <div className="flex items-center space-x-2">
              <span className="text-red-600">🚗💨</span>
              <span className="font-medium text-red-900">Speed Violations</span>
            </div>
            <div className="text-xl font-bold text-red-700">{stats.speed_violations}</div>
          </div>
          
          <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg border border-orange-200">
            <div className="flex items-center space-x-2">
              <span className="text-orange-600">🏍️⚠️</span>
              <span className="font-medium text-orange-900">Helmet Violations</span>
            </div>
            <div className="text-xl font-bold text-orange-700">{stats.helmet_violations}</div>
          </div>
        </div>
      </div>

      {/* Vehicle Counts */}
      <div className="mb-6">
        <h4 className="font-semibold text-gray-900 mb-3">🚗 Vehicle Counts</h4>
        <div className="space-y-2">
          <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
            <div className="flex items-center space-x-2">
              <span>🚗</span>
              <span className="text-gray-700 font-medium">Cars</span>
            </div>
            <span className="font-bold text-gray-900">{stats.vehicle_counts.cars}</span>
          </div>
          
          <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
            <div className="flex items-center space-x-2">
              <span>🏍️</span>
              <span className="text-gray-700 font-medium">Motorcycles</span>
            </div>
            <span className="font-bold text-gray-900">{stats.vehicle_counts.bikes}</span>
          </div>
          
          <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
            <div className="flex items-center space-x-2">
              <span>🚌</span>
              <span className="text-gray-700 font-medium">Buses</span>
            </div>
            <span className="font-bold text-gray-900">{stats.vehicle_counts.buses}</span>
          </div>
          
          <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
            <div className="flex items-center space-x-2">
              <span>🚛</span>
              <span className="text-gray-700 font-medium">Trucks</span>
            </div>
            <span className="font-bold text-gray-900">{stats.vehicle_counts.trucks}</span>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="bg-gray-50 rounded-lg p-4 border">
        <h4 className="font-semibold text-gray-900 mb-3">📈 Performance</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Violation Rate:</span>
            <span className="font-bold text-gray-900">{violationRate}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Detection Status:</span>
            <span className="font-bold text-green-700">✅ Active</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Processing Mode:</span>
            <span className="font-bold text-blue-700">Real-time</span>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-4 pt-4 border-t">
        <div className="text-xs text-gray-500 text-center">
          📊 Statistics update in real-time during detection
        </div>
      </div>
    </div>
  )
}