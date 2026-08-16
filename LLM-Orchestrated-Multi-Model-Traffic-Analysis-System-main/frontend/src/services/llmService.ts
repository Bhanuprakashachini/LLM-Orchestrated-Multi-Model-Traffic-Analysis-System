/**
 * LLM Service for Traffic Analysis Intelligence
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

interface ApiResponse<T = any> {
  data?: T
  error?: string
  message?: string
}

class LLMService {
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('access_token')
    return {
      'Content-Type': 'application/json',
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

  // Feature 8: LLM-Based Decision Making
  async analyzeTrafficConditions(analysisData: any): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/llm/analyze-conditions/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ analysis_data: analysisData })
    })
    
    return this.handleResponse(response)
  }

  // Feature 9: LLM-Based Model Comparison
  async compareModelPerformance(yolov8Results: any, yolov12Results: any): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/llm/compare-models/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ 
        yolov8_results: yolov8Results,
        yolov12_results: yolov12Results
      })
    })
    
    return this.handleResponse(response)
  }

  // Feature 10: LLM-Based Traffic Summary Generation
  async generateTrafficSummary(analysisData: any): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/llm/generate-summary/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ analysis_data: analysisData })
    })
    
    return this.handleResponse(response)
  }

  // Feature 11: LLM-Based Insight & Recommendation
  async generateRecommendations(analysisData: any): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/llm/generate-recommendations/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ analysis_data: analysisData })
    })
    
    return this.handleResponse(response)
  }

  // Feature 12: LLM-Based Natural Language Query Handling
  async handleNaturalLanguageQuery(query: string, analysisData?: any): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/llm/natural-language-query/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ 
        query,
        analysis_data: analysisData || {}
      })
    })
    
    return this.handleResponse(response)
  }

  // Get LLM Insights History
  async getTrafficInsights(page: number = 1, pageSize: number = 10): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/llm/insights/?page=${page}&page_size=${pageSize}`, {
      headers: this.getAuthHeaders()
    })
    
    return this.handleResponse(response)
  }

  // Get Scene Descriptions
  async getSceneDescriptions(page: number = 1, pageSize: number = 10): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/llm/descriptions/?page=${page}&page_size=${pageSize}`, {
      headers: this.getAuthHeaders()
    })
    
    return this.handleResponse(response)
  }

  // Get Conversation History
  async getConversationHistory(page: number = 1, pageSize: number = 10): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/llm/conversations/?page=${page}&page_size=${pageSize}`, {
      headers: this.getAuthHeaders()
    })
    
    return this.handleResponse(response)
  }

  // Delete Conversation
  async deleteConversation(sessionId: number): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/llm/conversations/${sessionId}/`, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    })
    
    return this.handleResponse(response)
  }
}

export const llmService = new LLMService()
export default llmService