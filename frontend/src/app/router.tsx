import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { AppShell } from '@/components/layout/app-shell'

const FeedPage = lazy(() => import('@/features/feed/feed-page').then((m) => ({ default: m.FeedPage })))
const SearchPage = lazy(() => import('@/features/search/search-page').then((m) => ({ default: m.SearchPage })))
const ChannelsPage = lazy(() => import('@/features/channels/channels-page').then((m) => ({ default: m.ChannelsPage })))
const ChannelDetailPage = lazy(() => import('@/features/channels/channel-detail-page').then((m) => ({ default: m.ChannelDetailPage })))
const CollectionsPage = lazy(() => import('@/features/collections/collections-page').then((m) => ({ default: m.CollectionsPage })))
const CollectionDetailPage = lazy(() => import('@/features/collections/collection-detail-page').then((m) => ({ default: m.CollectionDetailPage })))
const ExportsPage = lazy(() => import('@/features/exports/exports-page').then((m) => ({ default: m.ExportsPage })))
const SettingsPage = lazy(() => import('@/features/settings/settings-page').then((m) => ({ default: m.SettingsPage })))
const LoginPage = lazy(() => import('@/features/auth/login-page').then((m) => ({ default: m.LoginPage })))
const SignupPage = lazy(() => import('@/features/auth/signup-page').then((m) => ({ default: m.SignupPage })))
const AuthGuard = lazy(() => import('@/features/auth/auth-guard').then((m) => ({ default: m.AuthGuard })))
const LandingPage = lazy(() => import('@/features/landing/landing-page').then((m) => ({ default: m.LandingPage })))
const PricingPage = lazy(() => import('@/features/landing/pricing-page').then((m) => ({ default: m.PricingPage })))
const HowItWorksPage = lazy(() => import('@/features/landing/how-it-works-page').then((m) => ({ default: m.HowItWorksPage })))
const ResourcesPage = lazy(() => import('@/features/landing/resources-page').then((m) => ({ default: m.ResourcesPage })))
const ResourceDetailPage = lazy(() => import('@/features/landing/resource-detail-page').then((m) => ({ default: m.ResourceDetailPage })))
const ContactPage = lazy(() => import('@/features/landing/contact-page').then((m) => ({ default: m.ContactPage })))
const ContactSalesPage = lazy(() => import('@/features/landing/contact-sales-page').then((m) => ({ default: m.ContactSalesPage })))
const TermsPage = lazy(() => import('@/features/landing/terms-page').then((m) => ({ default: m.TermsPage })))
const PrivacyPage = lazy(() => import('@/features/landing/privacy-page').then((m) => ({ default: m.PrivacyPage })))
const NotFoundPage = lazy(() => import('@/features/landing/not-found-page').then((m) => ({ default: m.NotFoundPage })))
const ForgotPasswordPage = lazy(() => import('@/features/auth/forgot-password-page').then((m) => ({ default: m.ForgotPasswordPage })))
const ResetPasswordPage = lazy(() => import('@/features/auth/reset-password-page').then((m) => ({ default: m.ResetPasswordPage })))
const VerifyEmailPage = lazy(() => import('@/features/auth/verify-email-page').then((m) => ({ default: m.VerifyEmailPage })))

export function AppRouter() {
  const { t } = useTranslation()

  return (
    <Suspense fallback={<div className="p-8 text-sm text-foreground/60">{t('common.loading')}</div>}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="/how-it-works" element={<HowItWorksPage />} />
        <Route path="/resources" element={<ResourcesPage />} />
        <Route path="/resources/:slug" element={<ResourceDetailPage />} />
        <Route path="/contact" element={<ContactPage />} />
        <Route path="/contact-sales" element={<ContactSalesPage />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/register" element={<Navigate to="/signup" replace />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />

        <Route element={<AuthGuard />}>
          <Route element={<AppShell />}>
            <Route path="/dashboard" element={<Navigate to="/feed" replace />} />
            <Route path="/feed" element={<FeedPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/channels" element={<ChannelsPage />} />
            <Route path="/channels/:id" element={<ChannelDetailPage />} />
            <Route path="/collections" element={<CollectionsPage />} />
            <Route path="/collections/:id" element={<CollectionDetailPage />} />
            <Route path="/exports" element={<ExportsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Route>

        {/* 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  )
}
