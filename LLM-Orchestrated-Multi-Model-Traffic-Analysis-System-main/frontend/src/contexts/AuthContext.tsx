'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import toast from 'react-hot-toast'

interface User {
  id: string
  username: string
  email: string
  first_name: string
  last_name: string
  profile?: {
    theme: string
    language: string
    notifications_enabled: boolean
  }
}

interface Session {
  session_id: number
  expires_at: string
  device_info: {
    device_type: string
    browser: string
    os: string
  }
  ip_address: string
}

interface AuthContextType {
  user: User | null
  session: Session | null
  activeSessions: any[]
  isLoading: boolean
  login: (username: string, password: string) => Promise<boolean>
  logout: () => void
  terminateSession: (sessionId: number) => Promise<boolean>
  terminateAllSessions: () => Promise<boolean>
  getLoginHistory: () => Promise<any[]>
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [activeSessions, setActiveSessions] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check if user is already logged in
    const savedUser = localStorage.getItem('user')
    const savedSession = localStorage.getItem('session')
    const token = localStorage.getItem('access_token')
    
    if (savedUser && token) {
      try {
        setUser(JSON.parse(savedUser))
        if (savedSession) {
          setSession(JSON.parse(savedSession))
        }
        // Verify token and get current user info
        getCurrentUser()
      } catch (error) {
        localStorage.removeItem('user')
        localStorage.removeItem('session')
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
      }
    }
    setIsLoading(false)
  }, [])

  const getCurrentUser = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) return

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/auth/user/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        setUser(data.user)
        setActiveSessions(data.active_sessions || [])
        
        // Update stored user data
        localStorage.setItem('user', JSON.stringify(data.user))
      } else if (response.status === 401) {
        // Token expired, clear auth data
        logout()
      }
    } catch (error) {
      console.error('Error getting current user:', error)
    }
  }

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      // First try to connect to the backend API
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/auth/token/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      })

      const data = await response.json()

      if (response.ok) {
        // Store tokens and user data
        localStorage.setItem('access_token', data.access)
        localStorage.setItem('refresh_token', data.refresh)
        localStorage.setItem('user', JSON.stringify(data.user))
        
        if (data.session) {
          localStorage.setItem('session', JSON.stringify(data.session))
          setSession(data.session)
        }

        setUser(data.user)
        console.log('✅ Login successful, user set:', data.user)
        toast.success(`Welcome back, ${data.user.first_name || data.user.username}!`)
        return true
      } else {
        if (data.error) {
          toast.error(data.error)
        } else {
          toast.error('Login failed')
        }
        return false
      }
    } catch (error) {
      console.error('Backend connection failed:', error)
      toast.error('Unable to connect to authentication server. Please try again later.')
      return false
    }
  }

  const logout = async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token')
      const token = localStorage.getItem('access_token')
      
      if (token) {
        // Call logout endpoint
        await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/auth/logout/`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ refresh_token: refreshToken })
        })
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // Clear all auth data
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      localStorage.removeItem('session')
      
      setUser(null)
      setSession(null)
      setActiveSessions([])
      
      toast.success('Logged out successfully')
      
      // Redirect to login page
      window.location.href = '/login'
    }
  }

  const terminateSession = async (sessionId: number): Promise<boolean> => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) return false

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/auth/sessions/terminate/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ session_id: sessionId })
      })

      if (response.ok) {
        // Refresh active sessions
        getCurrentUser()
        toast.success('Session terminated successfully')
        return true
      } else {
        toast.error('Failed to terminate session')
        return false
      }
    } catch (error) {
      toast.error('Error terminating session')
      console.error('Terminate session error:', error)
      return false
    }
  }

  const terminateAllSessions = async (): Promise<boolean> => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) return false

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/auth/sessions/terminate-all/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        toast.success(`Terminated ${data.terminated_sessions} sessions`)
        
        // This will log out the current user as well
        logout()
        return true
      } else {
        toast.error('Failed to terminate sessions')
        return false
      }
    } catch (error) {
      toast.error('Error terminating sessions')
      console.error('Terminate all sessions error:', error)
      return false
    }
  }

  const getLoginHistory = async (): Promise<any[]> => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) return []

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/auth/login-history/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        return data.login_history || []
      }
      return []
    } catch (error) {
      console.error('Error getting login history:', error)
      return []
    }
  }

  const value = {
    user,
    session,
    activeSessions,
    isLoading,
    login,
    logout,
    terminateSession,
    terminateAllSessions,
    getLoginHistory,
    isAuthenticated: !!user
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}