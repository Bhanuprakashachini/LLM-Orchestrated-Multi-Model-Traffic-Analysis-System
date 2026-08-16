'use client'

interface VehicleDetection {
  detections: Array<{
    class: string
    confidence: number
    bbox: {
      x1: number
      y1: number
      x2: number
      y2: number
    }
    vehicle_details?: {
      type: string
      size_category: string
      description: string
      confidence_level: string
      confidence_description: string
      detection_quality: string
    }
  }>
  vehicle_counts: {
    car: number
    motorcycle: number
    bus: number
    truck: number
    bicycle: number
  }
  total_vehicles: number
  average_confidence: number
  detection_summary: {
    cars: number
    motorcycles: number
    buses: number
    trucks: number
    bicycles: number
  }
  vehicle_breakdown?: {
    by_type: Record<string, {
      count: number
      avg_confidence: number
      confidence_range: { min: number; max: number }
      sizes: Record<string, number>
    }>
    by_confidence: { high: number; medium: number; low: number }
    by_size: { small: number; medium: number; large: number; very_large: number }
    detailed_list: Array<{
      id: number
      type: string
      description: string
      confidence: string
      confidence_level: string
      size: string
      quality: string
    }>
  }
}

interface VehicleDetectionCardProps {
  detection: VehicleDetection
  className?: string
}

export default function VehicleDetectionCard({ detection, className = '' }: VehicleDetectionCardProps) {
  const vehicleIcons = {
    cars: '🚗',
    motorcycles: '🏍️',
    buses: '🚌',
    trucks: '🚛',
    bicycles: '🚲'
  }

  const vehicleColors = {
    cars: 'bg-blue-100 text-blue-800',
    motorcycles: 'bg-purple-100 text-purple-800',
    buses: 'bg-green-100 text-green-800',
    trucks: 'bg-orange-100 text-orange-800',
    bicycles: 'bg-yellow-100 text-yellow-800'
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Vehicle Detection Results</h3>
        <div className="text-right">
          <div className="text-2xl font-bold text-blue-600">{detection.total_vehicles}</div>
          <div className="text-sm text-gray-500">Total Vehicles</div>
        </div>
      </div>

      {/* Vehicle Counts Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        {Object.entries(detection.detection_summary).map(([vehicleType, count]) => (
          <div
            key={vehicleType}
            className={`rounded-lg p-4 text-center ${vehicleColors[vehicleType as keyof typeof vehicleColors]}`}
          >
            <div className="text-2xl mb-1">
              {vehicleIcons[vehicleType as keyof typeof vehicleIcons]}
            </div>
            <div className="text-xl font-bold">{count}</div>
            <div className="text-xs capitalize">{vehicleType}</div>
          </div>
        ))}
      </div>

      {/* Enhanced Vehicle Breakdown */}
      {detection.vehicle_breakdown && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Vehicle Analysis</h4>
          
          {/* Confidence Distribution */}
          <div className="grid grid-cols-3 gap-2 mb-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
              <div className="text-lg font-bold text-green-700">{detection.vehicle_breakdown.by_confidence.high}</div>
              <div className="text-xs text-green-600">High Confidence</div>
            </div>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-center">
              <div className="text-lg font-bold text-yellow-700">{detection.vehicle_breakdown.by_confidence.medium}</div>
              <div className="text-xs text-yellow-600">Medium Confidence</div>
            </div>
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-center">
              <div className="text-lg font-bold text-red-700">{detection.vehicle_breakdown.by_confidence.low}</div>
              <div className="text-xs text-red-600">Low Confidence</div>
            </div>
          </div>

          {/* Detailed Vehicle List */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h5 className="text-sm font-medium text-gray-700 mb-3">Detected Vehicles</h5>
            <div className="max-h-48 overflow-y-auto space-y-2">
              {detection.vehicle_breakdown.detailed_list.map((vehicle) => (
                <div key={vehicle.id} className="bg-white rounded-lg p-3 border border-gray-200">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">
                        {vehicleIcons[`${vehicle.type}s` as keyof typeof vehicleIcons] || '🚗'}
                      </span>
                      <span className="font-medium text-gray-900 capitalize">{vehicle.type}</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        vehicle.quality === 'excellent' ? 'bg-green-100 text-green-800' :
                        vehicle.quality === 'good' ? 'bg-blue-100 text-blue-800' :
                        vehicle.quality === 'fair' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {vehicle.quality}
                      </span>
                    </div>
                    <span className="text-sm font-medium text-gray-600">{vehicle.confidence}</span>
                  </div>
                  <div className="text-sm text-gray-600">{vehicle.description}</div>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-xs text-gray-500 capitalize">Size: {vehicle.size}</span>
                    <span className={`text-xs px-2 py-1 rounded ${
                      vehicle.confidence_level === 'very_high' ? 'bg-green-100 text-green-700' :
                      vehicle.confidence_level === 'high' ? 'bg-blue-100 text-blue-700' :
                      vehicle.confidence_level === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {vehicle.confidence_level.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Detection Statistics */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-600">Average Confidence</div>
          <div className="text-xl font-semibold text-gray-900">
            {(detection.average_confidence * 100).toFixed(1)}%
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-600">Detections</div>
          <div className="text-xl font-semibold text-gray-900">
            {detection.detections.length}
          </div>
        </div>
      </div>

      {/* Legacy Detection Details - Show only if no enhanced breakdown */}
      {detection.detections.length > 0 && !detection.vehicle_breakdown && (
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Detection Details</h4>
          <div className="max-h-40 overflow-y-auto space-y-2">
            {detection.detections.map((det, index) => (
              <div key={index} className="flex items-center justify-between text-sm bg-gray-50 rounded p-2">
                <span className="capitalize font-medium">{det.class}</span>
                <span className="text-gray-600">{(det.confidence * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}