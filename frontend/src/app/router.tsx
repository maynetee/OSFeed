import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/layout/app-shell'

const DashboardPage = lazy(() => import('@/features/dashboard/dashboard-page').then((m) => ({ default: m.DashboardPage })))
const FeedPage = lazy(() => import('@/features/feed/feed-page').then((m) => ({ default: m.FeedPage })))
const SearchPage = lazy(() => import('@/features/search/search-page').then((m) => ({ default: m.SearchPage })))
const DigestsPage = lazy(() => import('@/features/digests/digests-page').then((m) => ({ default: m.DigestsPage })))
const DigestDetailPage = lazy(() => import('@/features/digests/digest-detail-page').then((m) => ({ default: m.DigestDetailPage })))
const ChannelsPage = lazy(() => import('@/features/channels/channels-page').then((m) => ({ default: m.ChannelsPage })))
const ChannelDetailPage = lazy(() => import('@/features/channels/channel-detail-page').then((m) => ({ default: m.ChannelDetailPage })))
const CollectionsPage = lazy(() => import('@/features/collections/collections-page').then((m) => ({ default: m.CollectionsPage })))
const CollectionDetailPage = lazy(() => import('@/features/collections/collection-detail-page').then((m) => ({ default: m.CollectionDetailPage })))
const ExportsPage = lazy(() => import('@/features/exports/exports-page').then((m) => ({ default: m.ExportsPage })))
const SettingsPage = lazy(() => import('@/features/settings/settings-page').then((m) => ({ default: m.SettingsPage })))
const LoginPage = lazy(() => import('@/features/auth/login-page').then((m) => ({ default: m.LoginPage })))
const RegisterPage = lazy(() => import('@/features/auth/register-page').then((m) => ({ default: m.RegisterPage })))
const AuthGuard = lazy(() => import('@/features/auth/auth-guard').then((m) => ({ default: m.AuthGuard })))

export function AppRouter() {
  return (
    <Suspense fallback={<div className="p-8 text-sm text-foreground/60">Chargement...</div>}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route element={<AuthGuard />}>
          <Route element={<AppShell />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/feed" element={<FeedPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/digests" element={<DigestsPage />} />
            <Route path="/digests/:id" element={<DigestDetailPage />} />
            <Route path="/channels" element={<ChannelsPage />} />
            <Route path="/channels/:id" element={<ChannelDetailPage />} />
            <Route path="/collections" element={<CollectionsPage />} />
            <Route path="/collections/:id" element={<CollectionDetailPage />} />
            <Route path="/exports" element={<ExportsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}
