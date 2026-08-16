// Chart Rendering Fix
// Add this to components that use charts

import { useEffect, useRef, useState, ReactNode } from 'react'

interface ChartContainerProps {
  children: ReactNode
  minHeight?: number
}

const ChartContainer = ({ children, minHeight = 300 }: ChartContainerProps) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })
  
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { offsetWidth, offsetHeight } = containerRef.current
        setDimensions({
          width: Math.max(offsetWidth, 300), // Minimum width
          height: Math.max(offsetHeight, minHeight) // Minimum height
        })
      }
    }
    
    // Initial measurement
    updateDimensions()
    
    // Update on resize
    const resizeObserver = new ResizeObserver(updateDimensions)
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current)
    }
    
    return () => {
      resizeObserver.disconnect()
    }
  }, [minHeight])
  
  return (
    <div 
      ref={containerRef}
      className="w-full"
      style={{ 
        minHeight: `${minHeight}px`,
        minWidth: '300px'
      }}
    >
      {dimensions.width > 0 && dimensions.height > 0 && (
        <div style={{ width: dimensions.width, height: dimensions.height }}>
          {children}
        </div>
      )}
    </div>
  )
}

export default ChartContainer