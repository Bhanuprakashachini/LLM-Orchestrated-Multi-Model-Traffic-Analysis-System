// Media URL Utility with Error Handling
export const getMediaUrl = (path: string): string => {
  if (!path) return ''
  
  // Remove leading slash if present
  const cleanPath = path.startsWith('/') ? path.slice(1) : path
  
  // Construct full URL
  const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '') || 'http://localhost:8000'
  return `${baseUrl}/media/${cleanPath}`
}

export const preloadMedia = async (path: string): Promise<boolean> => {
  return new Promise((resolve) => {
    const url = getMediaUrl(path)
    
    if (path.match(/\.(mp4|webm|avi|mov)$/i)) {
      // Video preload
      const video = document.createElement('video')
      video.preload = 'metadata'
      video.onloadedmetadata = () => resolve(true)
      video.onerror = () => resolve(false)
      video.src = url
    } else {
      // Image preload
      const img = new Image()
      img.onload = () => resolve(true)
      img.onerror = () => resolve(false)
      img.src = url
    }
  })
}

export const checkMediaAvailability = async (paths: string[]): Promise<Record<string, boolean>> => {
  const results: Record<string, boolean> = {}
  
  await Promise.all(
    paths.map(async (path) => {
      try {
        const url = getMediaUrl(path)
        const response = await fetch(url, { method: 'HEAD' })
        results[path] = response.ok
      } catch {
        results[path] = false
      }
    })
  )
  
  return results
}