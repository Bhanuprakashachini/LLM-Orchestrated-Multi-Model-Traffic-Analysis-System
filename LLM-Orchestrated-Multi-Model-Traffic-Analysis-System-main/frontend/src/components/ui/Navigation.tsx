'use client'

import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

interface NavigationProps {
  currentPage?: string
  showBackButton?: boolean
  backUrl?: string
}

export default function Navigation({ currentPage, showBackButton = false, backUrl = '/dashboard' }: NavigationProps) {
  const { user, logout } = useAuth()
  const router = useRouter()

  const handleLogout = async () => {
    await logout()
  }

  const handleBack = () => {
    router.push(backUrl)
  }

  return (
    <header className="bg-white shadow-sm border-b border-blue-200">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {showBackButton && (
              <button
                onClick={handleBack}
                className="flex items-center text-blue-600 hover:text-blue-700 transition-colors"
              >
                <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back
              </button>
            )}
            
            <div className="flex items-center">
              <Link href="/dashboard" className="text-2xl font-bold text-blue-700 hover:text-blue-800 transition-colors">
                TrafficAI
              </Link>
              {currentPage && (
                <>
                  <span className="mx-2 text-gray-400">/</span>
                  <span className="text-lg font-medium text-gray-700">{currentPage}</span>
                </>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Navigation Links */}
            <nav className="hidden md:flex items-center space-x-4">
              <Link 
                href="/dashboard" 
                className="text-gray-600 hover:text-blue-600 transition-colors"
              >
                Dashboard
              </Link>
              <Link 
                href="/upload" 
                className="text-gray-600 hover:text-blue-600 transition-colors"
              >
                Upload
              </Link>
              <Link 
                href="/video-analysis" 
                className="text-gray-600 hover:text-blue-600 transition-colors"
              >
                Video Analysis
              </Link>
              <Link 
                href="/history" 
                className="text-gray-600 hover:text-blue-600 transition-colors"
              >
                History
              </Link>
              <Link 
                href="/profile" 
                className="text-gray-600 hover:text-blue-600 transition-colors"
              >
                Profile
              </Link>
            </nav>

            {/* User Info */}
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-medium">
                  {user?.first_name?.charAt(0) || user?.username?.charAt(0) || 'U'}
                </span>
              </div>
              <div className="hidden sm:block text-sm">
                <p className="font-medium text-gray-900">
                  {user?.first_name && user?.last_name 
                    ? `${user.first_name} ${user.last_name}` 
                    : user?.username || 'User'}
                </p>
                <p className="text-gray-500">{user?.email || 'No email provided'}</p>
              </div>
            </div>

            {/* Logout Button */}
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}