'use client'

interface DetectionSettings {
  speed_limit: number
  model_name: string
  confidence_threshold: number
  video_path: string
}

interface LiveVideoStreamProps {
  currentFrame: string | null
  isDetecting: boolean
  settings: DetectionSettings
}

export default function LiveVideoStream({
  currentFrame,
  isDetecting,
  settings
}: LiveVideoStreamProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <span className="mr-2">📺</span>
          Live Video Analysis
        </h3>
        <div className="flex items-center space-x-3">
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
            isDetecting 
              ? 'bg-red-100 text-red-800' 
              : 'bg-gray-100 text-gray-800'
          }`}>
            {isDetecting ? '🔴 LIVE' : '⚫ STOPPED'}
          </div>
          <div className="text-sm text-gray-600">
            Model: <span className="font-semibold">{settings.model_name.toUpperCase()}</span>
          </div>
        </div>
      </div>

      {/* Video Display Area */}
      <div className="relative bg-gray-900 rounded-lg overflow-hidden" style={{ aspectRatio: '16/9' }}>
        {currentFrame ? (
          <img
            src={currentFrame}  // currentFrame already includes data:image/jpeg;base64, prefix
            alt="Live traffic analysis"
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="flex items-center justify-center h-full text-white">
            {isDetecting ? (
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                <div className="text-lg font-semibold">Processing Video...</div>
                <div className="text-sm text-gray-300 mt-2">
                  Analyzing frames with {settings.model_name.toUpperCase()} model
                </div>
              </div>
            ) : (
              <div className="text-center">
                <div className="text-6xl mb-4">🎬</div>
                <div className="text-lg font-semibold">No Video Stream</div>
                <div className="text-sm text-gray-300 mt-2">
                  Select a video and start detection to see live analysis
                </div>
              </div>
            )}
          </div>
        )}

        {/* Overlay Information */}
        {currentFrame && (
          <div className="absolute top-4 left-4 bg-black bg-opacity-70 text-white px-3 py-2 rounded-lg text-sm">
            <div className="flex items-center space-x-4">
              <div>🚦 Limit: {settings.speed_limit} km/h</div>
              <div>🤖 {settings.model_name.toUpperCase()}</div>
              <div>🎯 {(settings.confidence_threshold * 100).toFixed(0)}%</div>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="mt-4 bg-gray-50 rounded-lg p-4">
        <h4 className="font-semibold text-gray-900 mb-3">🎨 Color Legend</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-green-500 rounded"></div>
            <span className="text-gray-700 font-medium">Normal Speed</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-red-500 rounded"></div>
            <span className="text-gray-700 font-medium">Speeding</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-gray-500 rounded"></div>
            <span className="text-gray-700 font-medium">Stationary</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-orange-500 rounded"></div>
            <span className="text-gray-700 font-medium">No Helmet</span>
          </div>
        </div>
      </div>

      {/* Detection Info */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
          <div className="font-semibold text-blue-900 mb-1">🎯 Detection Features</div>
          <div className="text-blue-800">
            • Guaranteed speed display for ALL vehicles<br/>
            • Real-time helmet detection for motorcycles<br/>
            • Color-coded violation indicators
          </div>
        </div>
        
        <div className="bg-green-50 rounded-lg p-3 border border-green-200">
          <div className="font-semibold text-green-900 mb-1">🚗 Vehicle Types</div>
          <div className="text-green-800">
            • Cars (speed monitoring)<br/>
            • Motorcycles (speed + helmet)<br/>
            • Buses & Trucks (speed monitoring)
          </div>
        </div>
        
        <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
          <div className="font-semibold text-purple-900 mb-1">⚡ Performance</div>
          <div className="text-purple-800">
            • Real-time processing at 20 FPS<br/>
            • Physics-based speed calculation<br/>
            • Multi-method helmet detection
          </div>
        </div>
      </div>
    </div>
  )
}