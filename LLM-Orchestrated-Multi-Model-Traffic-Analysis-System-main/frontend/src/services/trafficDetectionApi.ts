/**
 * Traffic Detection API Service
 * Handles all API calls for traffic violation detection
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

class TrafficDetectionApiService {
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

  /**
   * Upload a video file
   */
  async uploadVideo(file: File): Promise<any> {
    const formData = new FormData()
    formData.append('video', file)

    const response = await fetch(`${API_BASE_URL}/traffic-violations/upload/`, {
      method: 'POST',
      headers: this.getAuthHeadersForFormData(),
      body: formData
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Upload failed')
    }

    return response.json()
  }

  /**
   * Get list of available videos
   */
  async getAvailableVideos(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/traffic-violations/videos/`, {
      headers: this.getAuthHeaders()
    })

    if (!response.ok) {
      throw new Error('Failed to fetch videos')
    }

    return response.json()
  }

  /**
   * Get/Set detection settings
   */
  async getSettings(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/traffic-violations/settings/`, {
      headers: this.getAuthHeaders()
    })

    if (!response.ok) {
      throw new Error('Failed to fetch settings')
    }

    return response.json()
  }

  async updateSettings(settings: any): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/traffic-violations/settings/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(settings)
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Failed to update settings')
    }

    return response.json()
  }

  /**
   * Start detection
   */
  async startDetection(videoPath: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/traffic-violations/start/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ video_path: videoPath })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Failed to start detection')
    }

    return response.json()
  }

  /**
   * Stop detection
   */
  async stopDetection(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/traffic-violations/stop/`, {
      method: 'POST',
      headers: this.getAuthHeaders()
    })

    if (!response.ok) {
      throw new Error('Failed to stop detection')
    }

    return response.json()
  }

  /**
   * Get current frame
   */
  async getCurrentFrame(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/traffic-violations/frame/`, {
      headers: this.getAuthHeaders()
    })

    if (!response.ok) {
      throw new Error('Failed to fetch frame')
    }

    return response.json()
  }

  /**
   * Get violations
   */
  async getViolations(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/traffic-violations/violations/`, {
      headers: this.getAuthHeaders()
    })

    if (!response.ok) {
      throw new Error('Failed to fetch violations')
    }

    return response.json()
  }

  /**
   * Get statistics
   */
  async getStatistics(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/traffic-violations/statistics/`, {
      headers: this.getAuthHeaders()
    })

    if (!response.ok) {
      throw new Error('Failed to fetch statistics')
    }

    return response.json()
  }

  /**
   * Reset session
   */
  async resetSession(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/traffic-violations/session/reset/`, {
      method: 'POST',
      headers: this.getAuthHeaders()
    })

    if (!response.ok) {
      throw new Error('Failed to reset session')
    }

    return response.json()
  }

  /**
   * Get available models
   */
  async getAvailableModels(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/traffic-violations/models/`, {
      headers: this.getAuthHeaders()
    })

    if (!response.ok) {
      throw new Error('Failed to fetch models')
    }

    return response.json()
  }

  /**
   * Switch model
   */
  async switchModel(modelName: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/traffic-violations/models/switch/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ model_name: modelName })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Failed to switch model')
    }

    return response.json()
  }

  /**
   * Export session data
   */
  async exportSession(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/traffic-violations/session/export/`, {
      headers: this.getAuthHeaders()
    })

    if (!response.ok) {
      throw new Error('Failed to export session')
    }

    return response.json()
  }
}

export const trafficDetectionApi = new TrafficDetectionApiService()
export default trafficDetectionApi