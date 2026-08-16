'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import Link from 'next/link'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [focusedField, setFocusedField] = useState('')
  const { login } = useAuth()
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    
    try {
      const success = await login(username, password)
      if (success) {
        router.push('/dashboard')
      }
    } catch (error) {
      console.error('Login failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background elements */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 right-1/4 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl animate-pulse" />
        <div 
          className="absolute bottom-1/4 left-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl animate-pulse"
          style={{ animationDelay: '1s' }}
        />
      </div>

      <div className="relative min-h-screen flex items-center justify-center p-4">
        <div className="w-full max-w-2xl relative z-10">
          <div className="bg-white/90 backdrop-blur-xl rounded-2xl shadow-2xl p-8 border-0">
            {/* Project Title */}
            <div className="text-center mb-8">
              <div className="mb-6">
                <div className="relative p-4 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl shadow-lg mx-auto w-16 h-16 flex items-center justify-center">
                  <span className="text-2xl">🚗</span>
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl blur-lg opacity-50"></div>
                </div>
              </div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-blue-600 bg-clip-text text-transparent mb-3">
                Traffic Analysis System
              </h1>
              <p className="text-lg text-gray-600">
                LLM Orchestrated Multi Model Traffic Analysis
              </p>
            </div>

            {/* User Login Section */}
            <div className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 text-center mb-3">
                Welcome Back
              </h2>
              <p className="text-center text-gray-600 mb-6 text-lg">Sign in to your account</p>
            </div>

            {/* Login Form */}
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* User ID */}
              <div>
                <label htmlFor="username" className="block text-lg font-semibold text-gray-700 mb-3">
                  User ID
                </label>
                <input
                  id="username"
                  type="text"
                  autoComplete="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  onFocus={() => setFocusedField('username')}
                  onBlur={() => setFocusedField('')}
                  className={`w-full px-6 py-4 h-14 border-2 rounded-lg transition-all duration-200 text-lg text-gray-900 bg-white/70 ${
                    focusedField === 'username'
                      ? 'border-blue-500 focus:ring-blue-500/20 shadow-md'
                      : 'border-gray-200 hover:border-blue-300'
                  } focus:outline-none focus:ring-4`}
                  placeholder="Enter your user ID"
                  required
                  disabled={isLoading}
                />
              </div>

              {/* Password */}
              <div>
                <label htmlFor="password" className="block text-lg font-semibold text-gray-700 mb-3">
                  Password
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onFocus={() => setFocusedField('password')}
                    onBlur={() => setFocusedField('')}
                    className={`w-full px-6 py-4 pr-14 h-14 border-2 rounded-lg transition-all duration-200 text-lg text-gray-900 bg-white/70 ${
                      focusedField === 'password'
                        ? 'border-blue-500 focus:ring-blue-500/20 shadow-md'
                        : 'border-gray-200 hover:border-blue-300'
                    } focus:outline-none focus:ring-4`}
                    placeholder="Enter your password"
                    required
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-500 hover:text-gray-700 transition-colors duration-200"
                    disabled={isLoading}
                  >
                    {showPassword ? (
                      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                      </svg>
                    ) : (
                      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {/* Login Button */}
              <div className="pt-4">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full h-16 text-lg font-semibold text-white py-4 px-6 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-4 focus:ring-blue-500/25 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/25"
                >
                  {isLoading ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-3"></div>
                      Logging in...
                    </div>
                  ) : (
                    'Login'
                  )}
                </button>
              </div>

              {/* Register Button */}
              <div className="pt-6">
                <Link href="/register">
                  <button
                    type="button"
                    className="w-full h-16 bg-white text-blue-600 py-4 px-6 rounded-xl font-semibold border-2 border-blue-600 hover:bg-blue-50 focus:outline-none focus:ring-4 focus:ring-blue-500/20 transition-all duration-200 hover:shadow-lg text-lg"
                  >
                    Create New Account
                  </button>
                </Link>
              </div>
            </form>

            {/* Footer */}
            <div className="mt-10 text-center">
              <p className="text-sm text-gray-500">
                Traffic Analysis System
              </p>
              <p className="text-sm text-gray-400 mt-2">
                Secure • Reliable • AI-Powered
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}