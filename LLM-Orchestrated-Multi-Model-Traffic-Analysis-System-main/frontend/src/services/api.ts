/**
 * API Service Layer for Traffic Analysis
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

interface ApiResponse<T = any> {
  data?: T
  error?: string
  message?: string
}

class ApiService {
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('access_token')
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` })
    }
  }

  private getAuthHeadersForFormData(): HeadersInit {
    const token = localStorage.getItem('access_token')
    return {
      ...(token && { Authorization: `Bearer ${token}` })
    }
  }

  private async handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
    try {
      const data = await response.json()
      
      if (!response.ok) {
        return { error: data.error || data.message || 'An error occurred' }
      }
      
      return { data }
    } catch (error) {
      return { error: 'Failed to parse response' }
    }
  }

  // Authentication
  async login(username: string, password: string): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/auth/token/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })
    
    return this.handleResponse(response)
  }

  async register(userData: any): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/auth/register/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    })
    
    return this.handleResponse(response)
  }

  async getCurrentUser(): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/auth/user/`, {
      headers: this.getAuthHeaders()
    })
    
    return this.handleResponse(response)
  }

  // Analysis
  async uploadAndAnalyze(file: File, modelType: 'yolov8' | 'yolov12' | 'comparison' = 'comparison'): Promise<ApiResponse<any>> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('model_type', modelType)

    const response = await fetch(`${API_BASE_URL}/analysis/upload/`, {
      method: 'POST',
      headers: this.getAuthHeadersForFormData(),
      body: formData
    })
    
    return this.handleResponse(response)
  }

  async comprehensiveModelComparison(file: File, options: any = {}): Promise<ApiResponse<any>> {
    const formData = new FormData()
    formData.append('file', file)
    
    // Add ROI polygon if provided
    if (options.roi_polygon) {
      formData.append('roi_polygon', JSON.stringify(options.roi_polygon))
    }

    const response = await fetch(`${API_BASE_URL}/analysis/comprehensive/compare/`, {
      method: 'POST',
      headers: this.getAuthHeadersForFormData(),
      body: formData
    })
    
    return this.handleResponse(response)
  }

  async getAnalysisHistory(page: number = 1, pageSize: number = 10): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/analysis/history/?page=${page}&page_size=${pageSize}`, {
      headers: this.getAuthHeaders()
    })
    
    return this.handleResponse(response)
  }

  async compareModels(file: File): Promise<ApiResponse<any>> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE_URL}/analysis/compare/`, {
      method: 'POST',
      headers: this.getAuthHeadersForFormData(),
      body: formData
    })
    
    return this.handleResponse(response)
  }

  async getPerformanceMetrics(): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/analysis/metrics/`, {
      headers: this.getAuthHeaders()
    })
    
    return this.handleResponse(response)
  }

  async downloadReport(analysisId: number, format: 'json' | 'csv' = 'json'): Promise<Blob | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/analysis/download/${analysisId}/?format=${format}`, {
        headers: this.getAuthHeadersForFormData()
      })
      
      if (response.ok) {
        return await response.blob()
      }
      return null
    } catch (error) {
      console.error('Error downloading report:', error)
      return null
    }
  }

  async getAnalysis(analysisId: string): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/analysis/${analysisId}/`, {
      headers: this.getAuthHeaders()
    })
    
    return this.handleResponse(response)
  }

  // Analytics
  async getDashboardStats(): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/analytics/dashboard/`, {
      headers: this.getAuthHeaders()
    })
    
    return this.handleResponse(response)
  }

  // User Profile Management
  async getUserProfile(): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/users/profile/`, {
      headers: this.getAuthHeaders()
    })
    
    return this.handleResponse(response)
  }

  async updateUserProfile(profileData: any): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/users/profile/`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(profileData)
    })
    
    return this.handleResponse(response)
  }

  // Session Management
  async getActiveSessions(): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/auth/sessions/`, {
      headers: this.getAuthHeaders()
    })
    
    return this.handleResponse(response)
  }

  async terminateSession(sessionId: number): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/auth/sessions/${sessionId}/terminate/`, {
      method: 'POST',
      headers: this.getAuthHeaders()
    })
    
    return this.handleResponse(response)
  }

  async terminateAllSessions(): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/auth/sessions/terminate-all/`, {
      method: 'POST',
      headers: this.getAuthHeaders()
    })
    
    return this.handleResponse(response)
  }

  // Video Analysis
  async uploadVideo(videoFile: File, options: any = {}): Promise<ApiResponse<any>> {
    const formData = new FormData()
    formData.append('video', videoFile)
    
    // Add analysis options
    if (options.model_type) formData.append('model_type', options.model_type)
    if (options.sample_rate) formData.append('sample_rate', options.sample_rate.toString())
    if (options.confidence_threshold) formData.append('confidence_threshold', options.confidence_threshold.toString())
    
    const response = await fetch(`${API_BASE_URL}/analysis/video/upload/`, {
      method: 'POST',
      headers: this.getAuthHeadersForFormData(),
      body: formData
    })
    
    return this.handleResponse(response)
  }

  async getVideoAnalysis(analysisId: string): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/analysis/video/${analysisId}/`, {
      headers: this.getAuthHeaders()
    })
    
    return this.handleResponse(response)
  }

  async getVideoMetrics(analysisId: string): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/analysis/video/${analysisId}/metrics/`, {
      headers: this.getAuthHeaders()
    })
    
    return this.handleResponse(response)
  }

  async downloadVideoReport(analysisId: string, format: 'json' | 'csv'): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/analysis/video/${analysisId}/download/?format=${format}`, {
      headers: this.getAuthHeaders()
    })
    
    if (!response.ok) {
      throw new Error('Download failed')
    }
    
    return response.blob()
  }
}

export const apiService = new ApiService()
export default apiService