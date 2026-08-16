'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'

export default function TestAPIPage() {
  const { user } = useAuth()
  const [testResults, setTestResults] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const testAPI = async (name: string, url: string) => {
    const token = localStorage.getItem('access_token')
    
    try {
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      const data = await response.json()
      
      return {
        name,
        url,
        status: response.status,
        success: response.ok,
        data: response.ok ? data : { error: data },
        token_exists: !!token
      }
    } catch (error) {
      return {
        name,
        url,
        status: 0,
        success: false,
        data: { error: (error as Error).message },
        token_exists: !!token
      }
    }
  }

  const runTests = async () => {
    setIsLoading(true)
    setTestResults([])
    
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    const tests = [
      { name: 'User Stats', url: `${baseUrl}/api/v1/analytics/user-stats/` },
      { name: 'Analysis History', url: `${baseUrl}/api/v1/analysis/history/` },
      { name: 'Analysis Trends', url: `${baseUrl}/api/v1/analysis/trends/` },
      { name: 'LLM Insights', url: `${baseUrl}/api/v1/analysis/insights/` }
    ]

    const results = []
    for (const test of tests) {
      const result = await testAPI(test.name, test.url)
      results.push(result)
      setTestResults([...results])
    }
    
    setIsLoading(false)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">API Test Page</h1>
        
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Authentication Status</h2>
          <div className="space-y-2">
            <p><strong>User:</strong> {user ? user.username : 'Not logged in'}</p>
            <p><strong>Token:</strong> {localStorage.getItem('access_token') ? 'Present' : 'Missing'}</p>
            <p><strong>User ID:</strong> {user?.id || 'N/A'}</p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">API Tests</h2>
            <button
              onClick={runTests}
              disabled={isLoading || !user}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
            >
              {isLoading ? 'Testing...' : 'Run Tests'}
            </button>
          </div>

          {!user && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <p className="text-yellow-800">Please log in first to test the APIs.</p>
            </div>
          )}

          <div className="space-y-4">
            {testResults.map((result, index) => (
              <div key={index} className={`border rounded-lg p-4 ${
                result.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
              }`}>
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold">{result.name}</h3>
                  <span className={`px-2 py-1 rounded text-sm ${
                    result.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {result.status}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2">{result.url}</p>
                <p className="text-sm"><strong>Token:</strong> {result.token_exists ? 'Present' : 'Missing'}</p>
                
                {result.success && (
                  <div className="mt-2">
                    <p className="text-sm font-medium text-green-800">Success! Sample data:</p>
                    <pre className="text-xs bg-white p-2 rounded border mt-1 overflow-x-auto">
                      {JSON.stringify(result.data, null, 2)}
                    </pre>
                  </div>
                )}
                
                {!result.success && (
                  <div className="mt-2">
                    <p className="text-sm font-medium text-red-800">Error:</p>
                    <pre className="text-xs bg-white p-2 rounded border mt-1 overflow-x-auto">
                      {JSON.stringify(result.data, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}