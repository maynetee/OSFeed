import React, { useState } from 'react'
import { Button } from '@/components/ui/button'

/**
 * ErrorTrigger - Test component for triggering ErrorBoundary
 *
 * Usage: Add this component to any page to test error boundary behavior
 * Example: import { ErrorTrigger } from '@/components/test/ErrorTrigger'
 *          <ErrorTrigger />
 */
export const ErrorTrigger: React.FC = () => {
  const [shouldThrow, setShouldThrow] = useState(false)

  if (shouldThrow) {
    throw new Error('Test error triggered for ErrorBoundary testing')
  }

  return (
    <div className="fixed bottom-4 right-4 p-4 bg-red-100 border border-red-300 rounded-lg shadow-lg">
      <p className="text-sm text-red-800 mb-2">Error Boundary Test Component</p>
      <Button onClick={() => setShouldThrow(true)} variant="destructive" size="sm">
        Trigger Error
      </Button>
    </div>
  )
}
