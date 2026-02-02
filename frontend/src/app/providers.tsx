import React, { useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { I18nextProvider } from 'react-i18next'
import { useTranslation } from 'react-i18next'

import i18n from '@/app/i18n'
import { useTheme } from '@/hooks/use-theme'
import { ErrorBoundary } from '@/components/common/error-boundary'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function ThemeBridge() {
  useTheme()
  return null
}

function LanguageBridge() {
  const { i18n } = useTranslation()

  useEffect(() => {
    document.documentElement.lang = i18n.language
  }, [i18n.language])

  return null
}

interface AppProvidersProps {
  children: React.ReactNode
}

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <I18nextProvider i18n={i18n}>
          <ErrorBoundary>
            <BrowserRouter>
              <ThemeBridge />
              <LanguageBridge />
              {children}
            </BrowserRouter>
          </ErrorBoundary>
        </I18nextProvider>
      </QueryClientProvider>
    </React.StrictMode>
  )
}
