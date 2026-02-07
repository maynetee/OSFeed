import React from 'react'
import { withTranslation, WithTranslation } from 'react-i18next'
import { Button } from '@/components/ui/button'

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

interface ErrorBoundaryProps extends WithTranslation {
  children: React.ReactNode
  fallback?: React.ReactNode
}

class ErrorBoundaryComponent extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-8">
          <h1 className="text-xl font-semibold text-foreground">
            {this.props.t('common.errorTitle')}
          </h1>
          <p className="text-sm text-foreground/60">
            {this.state.error?.message || this.props.t('common.errorUnknown')}
          </p>
          <div className="flex gap-2">
            <Button onClick={this.handleRetry}>{this.props.t('common.errorRetry')}</Button>
            <Button variant="outline" onClick={() => (window.location.href = '/login')}>
              {this.props.t('common.errorReconnect')}
            </Button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export const ErrorBoundary = withTranslation()(ErrorBoundaryComponent)
