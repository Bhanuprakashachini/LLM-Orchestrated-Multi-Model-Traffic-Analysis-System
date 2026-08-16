// LocalStorage Utility with Quota Handling
export const safeLocalStorage = {
  setItem: (key: string, value: any): boolean => {
    try {
      const serialized = JSON.stringify(value)
      
      // Check if the data is too large (>5MB)
      if (serialized.length > 5 * 1024 * 1024) {
        console.warn(`⚠️ Data too large for localStorage: ${serialized.length} bytes`)
        return false
      }
      
      localStorage.setItem(key, serialized)
      return true
    } catch (error) {
      if (error instanceof DOMException && error.code === 22) {
        console.warn('⚠️ LocalStorage quota exceeded:', error)
        // Try to clear old data and retry
        safeLocalStorage.clearOldData()
        try {
          localStorage.setItem(key, JSON.stringify(value))
          return true
        } catch {
          return false
        }
      }
      console.error('❌ LocalStorage error:', error)
      return false
    }
  },
  
  getItem: (key: string): any => {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : null
    } catch (error) {
      console.error('❌ LocalStorage parse error:', error)
      return null
    }
  },
  
  removeItem: (key: string): void => {
    try {
      localStorage.removeItem(key)
    } catch (error) {
      console.error('❌ LocalStorage remove error:', error)
    }
  },
  
  clearOldData: (): void => {
    try {
      // Remove old analysis data (keep only the most recent)
      const keys = Object.keys(localStorage)
      const analysisKeys = keys.filter(key => key.startsWith('analysis_') || key.startsWith('currentAnalysis'))
      
      // Sort by timestamp and keep only the most recent 3
      analysisKeys.sort().slice(0, -3).forEach(key => {
        localStorage.removeItem(key)
      })
      
      console.log(`🧹 Cleared ${analysisKeys.length - 3} old analysis entries`)
    } catch (error) {
      console.error('❌ Error clearing old data:', error)
    }
  },
  
  getStorageInfo: (): { used: number, available: number } => {
    let used = 0
    try {
      for (const key in localStorage) {
        if (localStorage.hasOwnProperty(key)) {
          used += localStorage[key].length + key.length
        }
      }
    } catch (error) {
      console.error('❌ Error calculating storage usage:', error)
    }
    
    // Estimate available space (browsers typically allow 5-10MB)
    const estimated = 5 * 1024 * 1024 // 5MB
    return { used, available: Math.max(0, estimated - used) }
  }
}