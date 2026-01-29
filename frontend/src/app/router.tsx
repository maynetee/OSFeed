import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { AppShell } from '@/components/layout/app-shell'

const DashboardPage = lazy(() => import('@/features/dashboard/dashboard-page').then((m) => ({ default: m.DashboardPage })))
const FeedPage = lazy(() => import('@/features/feed/feed-page').then((m) => ({ default: m.FeedPage })))
const SearchPage = lazy(() => import('@/features/search/search-page').then((m) => ({ default: m.SearchPage })))
const ChannelsPage = lazy(() => import('@/features/channels/channels-page').then((m) => ({ default: m.ChannelsPage })))
const ChannelDetailPage = lazy(() => import('@/features/channels/channel-detail-page').then((m) => ({ default: m.ChannelDetailPage })))
const CollectionsPage = lazy(() => import('@/features/collections/collections-page').then((m) => ({ default: m.CollectionsPage })))
const CollectionDetailPage = lazy(() => import('@/features/collections/collection-detail-page').then((m) => ({ default: m.CollectionDetailPage })))
const ExportsPage = lazy(() => import('@/features/exports/exports-page').then((m) => ({ default: m.ExportsPage })))
const SettingsPage = lazy(() => import('@/features/settings/settings-page').then((m) => ({ default: m.SettingsPage })))
const LoginPage = lazy(() => import('@/features/auth/login-page').then((m) => ({ default: m.LoginPage })))
const RegisterPage = lazy(() => import('@/features/auth/register-page').then((m) => ({ default: m.RegisterPage })))
const AuthGuard = lazy(() => import('@/features/auth/auth-guard').then((m) => ({ default: m.AuthGuard })))
const LandingPage = lazy(() => import('@/features/landing/landing-page').then((m) => ({ default: m.LandingPage })))
const ForgotPasswordPage = lazy(() => import('@/features/auth/forgot-password-page').then((m) => ({ default: m.ForgotPasswordPage })))
const ResetPasswordPage = lazy(() => import('@/features/auth/reset-password-page').then((m) => ({ default: m.ResetPasswordPage })))
const VerifyEmailPage = lazy(() => import('@/features/auth/verify-email-page').then((m) => ({ default: m.VerifyEmailPage })))

export function AppRouter() {
  const { t } = useTranslation()

  return (
    <Suspense fallback={<div className="p-8 text-sm text-foreground/60">{t('common.loading')}</div>}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />

        <Route element={<AuthGuard />}>
          <Route element={<AppShell />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/feed" element={<FeedPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/channels" element={<ChannelsPage />} />
            <Route path="/channels/:id" element={<ChannelDetailPage />} />
            <Route path="/collections" element={<CollectionsPage />} />
            <Route path="/collections/:id" element={<CollectionDetailPage />} />
            <Route path="/exports" element={<ExportsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            {/* Redirect / to /dashboard if we unintentionally fall through, 
                though LandingPage handles the auth check check too. 
                Actually, to be safe, if we are in this guarded block, we are authed. 
                But this route is outside / path so it won't catch /. 
            */}
          </Route>
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}
