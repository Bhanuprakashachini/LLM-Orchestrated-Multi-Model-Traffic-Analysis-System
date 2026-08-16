'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import toast from 'react-hot-toast'

interface SessionManagerProps {
  className?: string
}

export default function SessionManager({ className = '' }: SessionManagerProps) {
  const { activeSessions, terminateSession, terminateAllSessions, getLoginHistory } = useAuth()
  const [loginHistory, setLoginHistory] = useState<any[]>([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [showHistory, setShowHistory] = useState(false)

  const loadLoginHistory = async () => {
    setIsLoadingHistory(true)
    try {
      const history = await getLoginHistory()
      setLoginHistory(history)
    } catch (error) {
      toast.error('Failed to load login history')
    } finally {
      setIsLoadingHistory(false)
    }
  }

  const handleTerminateSession = async (sessionId: number) => {
    if (confirm('Are you sure you want to terminate this session?')) {
      await terminateSession(sessionId)
    }
  }

  const handleTerminateAllSessions = async () => {
    if (confirm('Are you sure you want to terminate ALL sessions? This will log you out from all devices.')) {
      await terminateAllSessions()
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const getDeviceIcon = (deviceType: string) => {
    switch (deviceType.toLowerCase()) {
      case 'mobile':
        return '📱'
      case 'tablet':
        return '📱'
      case 'desktop':
      default:
        return '💻'
    }
  }

  const getBrowserIcon = (browser: string) => {
    switch (browser.toLowerCase()) {
      case 'chrome':
        return '🌐'
      case 'firefox':
        return '🦊'
      case 'safari':
        return '🧭'
      case 'edge':
        return '🔷'
      default:
        return '🌐'
    }
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Session Management</h3>
        <div className="flex space-x-2">
          <button
            onClick={() => {
              setShowHistory(!showHistory)
              if (!showHistory && loginHistory.length === 0) {
                loadLoginHistory()
              }
            }}
            className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
          >
            {showHistory ? 'Hide History' : 'Login History'}
          </button>
          <button
            onClick={handleTerminateAllSessions}
            className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
          >
            Terminate All
          </button>
        </div>
      </div>

      {/* Active Sessions */}
      <div className="mb-6">
        <h4 className="text-md font-medium text-gray-900 mb-3">
          Active Sessions ({activeSessions.length})
        </h4>
        
        {activeSessions.length === 0 ? (
          <p className="text-gray-500 text-sm">No active sessions found.</p>
        ) : (
          <div className="space-y-3">
            {activeSessions.map((session) => (
              <div
                key={session.id}
                className={`p-4 border rounded-lg ${
                  session.is_current ? 'border-green-300 bg-green-50' : 'border-gray-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">
                      {getDeviceIcon(session.device_type)}
                    </span>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-gray-900">
                          {session.device_type} • {session.operating_system}
                        </span>
                        {session.is_current && (
                          <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full">
                            Current
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-600">
                        {getBrowserIcon(session.browser)} {session.browser} • {session.ip_address}
                      </div>
                      <div className="text-xs text-gray-500">
                        Created: {formatDate(session.created_at)}
                        {session.last_activity && (
                          <> • Last active: {formatDate(session.last_activity)}</>
                        )}
                      </div>
                      {session.location && (
                        <div className="text-xs text-gray-500">
                          📍 {session.location}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {!session.is_current && (
                    <button
                      onClick={() => handleTerminateSession(session.id)}
                      className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                    >
                      Terminate
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Login History */}
      {showHistory && (
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-3">
            Recent Login History
          </h4>
          
          {isLoadingHistory ? (
            <div className="flex items-center justify-center py-4">
              <LoadingSpinner size="sm" />
            </div>
          ) : loginHistory.length === 0 ? (
            <p className="text-gray-500 text-sm">No login history available.</p>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {loginHistory.map((attempt, index) => (
                <div
                  key={index}
                  className={`p-3 border rounded-lg ${
                    attempt.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className={`w-2 h-2 rounded-full ${
                          attempt.success ? 'bg-green-500' : 'bg-red-500'
                        }`} />
                        <span className="text-sm font-medium">
                          {attempt.success ? 'Successful Login' : 'Failed Login'}
                        </span>
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {attempt.ip_address} • {formatDate(attempt.timestamp)}
                      </div>
                      {!attempt.success && attempt.failure_reason && (
                        <div className="text-xs text-red-600 mt-1">
                          Reason: {attempt.failure_reason}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}