'use client'

interface Violation {
  type: string
  timestamp: string
  vehicle_type: string
  speed?: number
  speed_limit?: number
  excess_speed?: number
  confidence: number
  details: any
}

interface ViolationHistoryProps {
  violations: Violation[]
}

export default function ViolationHistory({ violations }: ViolationHistoryProps) {
  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp)
      return date.toLocaleTimeString('en-US', { 
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    } catch {
      return timestamp
    }
  }

  const getViolationIcon = (type: string) => {
    switch (type) {
      case 'OVERSPEEDING':
        return '🚗💨'
      case 'NO_HELMET':
        return '🏍️⚠️'
      case 'RED_LIGHT_VIOLATION':
        return '🚦❌'
      default:
        return '⚠️'
    }
  }

  const getViolationColor = (type: string) => {
    switch (type) {
      case 'OVERSPEEDING':
        return 'border-red-200 bg-red-50'
      case 'NO_HELMET':
        return 'border-orange-200 bg-orange-50'
      case 'RED_LIGHT_VIOLATION':
        return 'border-purple-200 bg-purple-50'
      default:
        return 'border-gray-200 bg-gray-50'
    }
  }

  const getViolationTextColor = (type: string) => {
    switch (type) {
      case 'OVERSPEEDING':
        return 'text-red-900'
      case 'NO_HELMET':
        return 'text-orange-900'
      case 'RED_LIGHT_VIOLATION':
        return 'text-purple-900'
      default:
        return 'text-gray-900'
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <span className="mr-2">🚨</span>
          Recent Violations
        </h3>
        <div className="text-sm text-gray-500">
          Last {violations.length} violations
        </div>
      </div>

      {violations.length > 0 ? (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {violations.slice().reverse().map((violation, index) => (
            <div
              key={index}
              className={`p-3 rounded-lg border ${getViolationColor(violation.type)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <div className="text-lg">
                    {getViolationIcon(violation.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className={`font-semibold ${getViolationTextColor(violation.type)}`}>
                      {violation.type === 'OVERSPEEDING' && 'Speed Violation'}
                      {violation.type === 'NO_HELMET' && 'Helmet Violation'}
                      {violation.type === 'RED_LIGHT_VIOLATION' && 'Red Light Violation'}
                    </div>
                    
                    <div className="text-sm text-gray-600 mt-1">
                      <div className="flex items-center space-x-2">
                        <span>🚗 {violation.vehicle_type.toUpperCase()}</span>
                        <span>•</span>
                        <span>🕒 {formatTime(violation.timestamp)}</span>
                      </div>
                      
                      {violation.type === 'OVERSPEEDING' && violation.speed && (
                        <div className="mt-1">
                          <span className="font-medium text-red-700">
                            {violation.speed.toFixed(1)} km/h
                          </span>
                          <span className="text-gray-600">
                            {' '}(limit: {violation.speed_limit} km/h, excess: +{violation.excess_speed?.toFixed(1)} km/h)
                          </span>
                        </div>
                      )}
                      
                      {violation.type === 'NO_HELMET' && (
                        <div className="mt-1 text-orange-700 font-medium">
                          Motorcycle rider without helmet detected
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="text-xs text-gray-500 ml-2">
                  {(violation.confidence * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <div className="text-3xl mb-2">✅</div>
          <div className="font-medium">No Violations Detected</div>
          <div className="text-sm mt-1">
            All vehicles are following traffic rules
          </div>
        </div>
      )}

      {/* Summary */}
      {violations.length > 0 && (
        <div className="mt-4 pt-4 border-t">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="text-center">
              <div className="font-bold text-red-700">
                {violations.filter(v => v.type === 'OVERSPEEDING').length}
              </div>
              <div className="text-gray-600">Speed Violations</div>
            </div>
            <div className="text-center">
              <div className="font-bold text-orange-700">
                {violations.filter(v => v.type === 'NO_HELMET').length}
              </div>
              <div className="text-gray-600">Helmet Violations</div>
            </div>
          </div>
        </div>
      )}

      {/* Auto-refresh indicator */}
      <div className="mt-4 text-xs text-gray-500 text-center">
        🔄 Updates automatically during detection
      </div>
    </div>
  )
}