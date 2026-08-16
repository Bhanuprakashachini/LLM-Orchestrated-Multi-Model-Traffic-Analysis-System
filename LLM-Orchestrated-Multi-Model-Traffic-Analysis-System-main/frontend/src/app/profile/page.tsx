'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import Navigation from '@/components/ui/Navigation'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import apiService from '@/services/api'
import toast from 'react-hot-toast'

interface UserSession {
  id: number
  created_at: string
  last_activity: string
  ip_address: string
  device_type: string
  browser: string
  operating_system: string
  location: string
  is_current: boolean
}

interface UserProfile {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  date_joined: string
  last_login: string
}

export default function ProfilePage() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [sessions, setSessions] = useState<UserSession[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isUpdating, setIsUpdating] = useState(false)
  const [activeTab, setActiveTab] = useState<'profile' | 'sessions' | 'security'>('profile')

  useEffect(() => {
    if (!user) {
      router.push('/login')
      return
    }
    
    loadProfileData()
  }, [user, router])

  const loadProfileData = async () => {
    setIsLoading(true)
    try {
      const [profileResponse, sessionsResponse] = await Promise.all([
        apiService.getUserProfile(),
        apiService.getActiveSessions()
      ])

      if ((profileResponse as any).success) {
        setProfile((profileResponse as any).data)
      }

      if ((sessionsResponse as any).success) {
        setSessions((sessionsResponse as any).data)
      }
    } catch (error) {
      console.error('Error loading profile data:', error)
      toast.error('Failed to load profile data')
    } finally {
      setIsLoading(false)
    }
  }

  const updateProfile = async (updatedData: Partial<UserProfile>) => {
    setIsUpdating(true)
    try {
      const response = await apiService.updateUserProfile(updatedData)
      if ((response as any).success) {
        setProfile((response as any).data)
        toast.success('Profile updated successfully')
      } else {
        toast.error('Failed to update profile')
      }
    } catch (error) {
      console.error('Error updating profile:', error)
      toast.error('Failed to update profile')
    } finally {
      setIsUpdating(false)
    }
  }

  const terminateSession = async (sessionId: number) => {
    try {
      const response = await apiService.terminateSession(sessionId)
      if ((response as any).success) {
        setSessions(sessions.filter(s => s.id !== sessionId))
        toast.success('Session terminated successfully')
      } else {
        toast.error('Failed to terminate session')
      }
    } catch (error) {
      console.error('Error terminating session:', error)
      toast.error('Failed to terminate session')
    }
  }

  const terminateAllSessions = async () => {
    try {
      const response = await apiService.terminateAllSessions()
      if ((response as any).success) {
        toast.success('All sessions terminated successfully')
        logout() // Force logout since all sessions are terminated
      } else {
        toast.error('Failed to terminate sessions')
      }
    } catch (error) {
      console.error('Error terminating all sessions:', error)
      toast.error('Failed to terminate sessions')
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Profile Not Found</h2>
          <p className="text-gray-600">Unable to load your profile information.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Navigation />
      
      <div className="py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">User Profile</h1>
            <p className="text-gray-600">Manage your account settings and active sessions</p>
          </div>

          <div className="bg-white rounded-lg shadow-lg">
            <div className="p-6">
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Username
                    </label>
                    <input
                      type="text"
                      value={profile.username}
                      disabled
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email
                    </label>
                    <input
                      type="email"
                      value={profile.email}
                      onChange={(e) => setProfile({...profile, email: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={() => updateProfile({
                      email: profile.email,
                      first_name: profile.first_name,
                      last_name: profile.last_name
                    })}
                    disabled={isUpdating}
                    className="bg-blue-600 text-white py-2 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                  >
                    {isUpdating ? (
                      <>
                        <LoadingSpinner size="sm" className="mr-2" />
                        Updating...
                      </>
                    ) : (
                      'Update Profile'
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}