'use client'

interface TrafficDensity {
  density_level: string
  congestion_index: number
  vehicle_density: number
  area_coverage_percentage: number
  total_vehicles: number
  density_metrics: {
    vehicles_per_area: number
    coverage_percentage: number
    congestion_score: number
  }
}

interface TrafficDensityCardProps {
  density: TrafficDensity
  className?: string
}

export default function TrafficDensityCard({ density, className = '' }: TrafficDensityCardProps) {
  const getDensityColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'empty':
        return 'bg-gray-100 text-gray-800 border-gray-300'
      case 'low':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-300'
      case 'congested':
        return 'bg-red-100 text-red-800 border-red-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const getDensityIcon = (level: string) => {
    switch (level.toLowerCase()) {
      case 'empty':
        return '🟢'
      case 'low':
        return '🟡'
      case 'medium':
        return '🟠'
      case 'high':
        return '🔴'
      case 'congested':
        return '🚨'
      default:
        return '⚪'
    }
  }

  const getCongestionBarColor = (index: number) => {
    if (index <= 0.25) return 'bg-green-500'
    if (index <= 0.5) return 'bg-yellow-500'
    if (index <= 0.75) return 'bg-orange-500'
    return 'bg-red-500'
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Traffic Density Analysis</h3>
        <div className={`px-4 py-2 rounded-full border-2 ${getDensityColor(density.density_level)}`}>
          <div className="flex items-center space-x-2">
            <span className="text-lg">{getDensityIcon(density.density_level)}</span>
            <span className="font-semibold capitalize">{density.density_level}</span>
          </div>
        </div>
      </div>

      {/* Congestion Index */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Congestion Index</span>
          <span className="text-sm font-semibold text-gray-900">
            {(density.congestion_index * 100).toFixed(0)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all duration-500 ${getCongestionBarColor(density.congestion_index)}`}
            style={{ width: `${density.congestion_index * 100}%` }}
          />
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="text-sm text-blue-600 font-medium">Total Vehicles</div>
          <div className="text-2xl font-bold text-blue-900">{density.total_vehicles}</div>
        </div>
        <div className="bg-purple-50 rounded-lg p-4">
          <div className="text-sm text-purple-600 font-medium">Area Coverage</div>
          <div className="text-2xl font-bold text-purple-900">
            {density.area_coverage_percentage.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Detailed Metrics */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-gray-900">Detailed Metrics</h4>
        
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Vehicle Density</span>
            <span className="text-sm font-semibold text-gray-900">
              {density.vehicle_density.toFixed(2)} vehicles/m²
            </span>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Congestion Score</span>
            <span className="text-sm font-semibold text-gray-900">
              {density.density_metrics.congestion_score.toFixed(0)}/100
            </span>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Coverage Percentage</span>
            <span className="text-sm font-semibold text-gray-900">
              {density.density_metrics.coverage_percentage.toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {/* Traffic Level Description */}
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <p className="text-sm text-gray-700">
          {density.density_level === 'Empty' && 'No vehicles detected in the scene.'}
          {density.density_level === 'Low' && 'Light traffic with good flow conditions.'}
          {density.density_level === 'Medium' && 'Moderate traffic density with acceptable flow.'}
          {density.density_level === 'High' && 'Heavy traffic with potential for congestion.'}
          {density.density_level === 'Congested' && 'Severe congestion with limited vehicle movement.'}
        </p>
      </div>
    </div>
  )
}