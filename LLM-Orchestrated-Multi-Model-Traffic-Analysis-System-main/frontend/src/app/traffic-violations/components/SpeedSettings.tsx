'use client'

interface DetectionSettings {
  speed_limit: number
  model_name: string
  confidence_threshold: number
  video_path: string
}

interface SpeedSettingsProps {
  settings: DetectionSettings
  availableModels: string[]
  onSettingsChange: (settings: Partial<DetectionSettings>) => void
}

export default function SpeedSettings({
  settings,
  availableModels,
  onSettingsChange
}: SpeedSettingsProps) {
  const modelInfo = {
    'yolov8s': {
      name: 'YOLOv8 Small',
      description: 'Fast and accurate - Recommended for real-time',
      speed: '⚡ Fast',
      accuracy: '🎯 Good'
    },
    'yolo11s': {
      name: 'YOLOv11 Small', 
      description: 'Enhanced accuracy with moderate speed',
      speed: '⚡ Moderate',
      accuracy: '🎯 Better'
    },
    'yolo12s': {
      name: 'YOLOv12 Small',
      description: 'Latest model with best accuracy',
      speed: '⚡ Moderate',
      accuracy: '🎯 Best'
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <span className="mr-2">⚙️</span>
        Detection Settings
      </h3>

      <div className="space-y-6">
        {/* Speed Limit */}
        <div>
          <label className="block text-sm font-bold text-gray-900 mb-2">
            🚦 Speed Limit (km/h)
          </label>
          <div className="flex items-center space-x-3">
            <input
              type="number"
              min="10"
              max="200"
              value={settings.speed_limit}
              onChange={(e) => onSettingsChange({ speed_limit: parseInt(e.target.value) || 50 })}
              className="w-24 px-3 py-2 border-2 border-gray-400 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 bg-white text-gray-900 font-medium text-center"
            />
            <span className="text-gray-700 font-medium">km/h</span>
            <div className="flex-1">
              <div className="text-sm text-gray-600">
                Vehicles exceeding this speed will be flagged as violations
              </div>
            </div>
          </div>
        </div>

        {/* YOLO Model Selection */}
        <div>
          <label className="block text-sm font-bold text-gray-900 mb-2">
            🤖 YOLO Model
          </label>
          <div className="space-y-3">
            {availableModels.map((model) => (
              <div
                key={model}
                className={`p-3 rounded-lg border-2 cursor-pointer transition-all ${
                  settings.model_name === model
                    ? 'border-red-500 bg-red-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onClick={() => onSettingsChange({ model_name: model })}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-4 h-4 rounded-full border-2 ${
                      settings.model_name === model
                        ? 'border-red-500 bg-red-500'
                        : 'border-gray-300'
                    }`}>
                      {settings.model_name === model && (
                        <div className="w-2 h-2 bg-white rounded-full m-0.5"></div>
                      )}
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">
                        {modelInfo[model as keyof typeof modelInfo]?.name || model}
                      </div>
                      <div className="text-sm text-gray-600">
                        {modelInfo[model as keyof typeof modelInfo]?.description}
                      </div>
                    </div>
                  </div>
                  <div className="text-right text-sm">
                    <div>{modelInfo[model as keyof typeof modelInfo]?.speed}</div>
                    <div>{modelInfo[model as keyof typeof modelInfo]?.accuracy}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Confidence Threshold */}
        <div>
          <label className="block text-sm font-bold text-gray-900 mb-2">
            🎯 Detection Confidence
          </label>
          <div className="space-y-2">
            <input
              type="range"
              min="0.1"
              max="0.9"
              step="0.05"
              value={settings.confidence_threshold}
              onChange={(e) => onSettingsChange({ confidence_threshold: parseFloat(e.target.value) })}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-sm text-gray-600">
              <span>0.1 (More detections)</span>
              <span className="font-semibold text-gray-900">
                {(settings.confidence_threshold * 100).toFixed(0)}%
              </span>
              <span>0.9 (Fewer, more confident)</span>
            </div>
          </div>
          <div className="text-sm text-gray-600 mt-1">
            Lower values detect more vehicles but may include false positives
          </div>
        </div>

        {/* Detection Features */}
        <div className="bg-gray-50 rounded-lg p-4 border">
          <h4 className="font-semibold text-gray-900 mb-3">🎯 Detection Features</h4>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="flex items-center space-x-2">
              <span className="text-green-600">✅</span>
              <span className="text-gray-700 font-medium">Speed Violations</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-600">✅</span>
              <span className="text-gray-700 font-medium">Helmet Detection</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-600">✅</span>
              <span className="text-gray-700 font-medium">Vehicle Classification</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-600">✅</span>
              <span className="text-gray-700 font-medium">Real-time Tracking</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-600">✅</span>
              <span className="text-gray-700 font-medium">Guaranteed Speeds</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-600">✅</span>
              <span className="text-gray-700 font-medium">Live Statistics</span>
            </div>
          </div>
        </div>

        {/* Performance Info */}
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <h4 className="font-semibold text-blue-900 mb-2">📊 Performance Tips</h4>
          <div className="text-sm text-blue-800 space-y-1">
            <div>• <strong>YOLOv8s:</strong> Best for real-time processing</div>
            <div>• <strong>YOLOv11s:</strong> Balanced speed and accuracy</div>
            <div>• <strong>YOLOv12s:</strong> Highest accuracy, slower processing</div>
            <div>• Lower confidence = more detections but more false positives</div>
            <div>• Higher speed limits = fewer violation alerts</div>
          </div>
        </div>
      </div>
    </div>
  )
}