import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import enNavigation from '../locales/en/navigation.json'
import enCommon from '../locales/en/common.json'
import enTheme from '../locales/en/theme.json'
import enBranding from '../locales/en/branding.json'
import enHeader from '../locales/en/header.json'
import enSidebar from '../locales/en/sidebar.json'
import enAuth from '../locales/en/auth.json'
import enDashboard from '../locales/en/dashboard.json'
import enFeed from '../locales/en/feed.json'
import enFilters from '../locales/en/filters.json'
import enSearch from '../locales/en/search.json'
import enDigests from '../locales/en/digests.json'
import enDigestViewer from '../locales/en/digestViewer.json'
import enExports from '../locales/en/exports.json'
import enChannels from '../locales/en/channels.json'
import enCollections from '../locales/en/collections.json'
import enCuratedCollections from '../locales/en/curatedCollections.json'
import enSettings from '../locales/en/settings.json'
import enMessages from '../locales/en/messages.json'
import enAlerts from '../locales/en/alerts.json'
import enStats from '../locales/en/stats.json'
import enSummaries from '../locales/en/summaries.json'
import enAnalysis from '../locales/en/analysis.json'
import frNavigation from '../locales/fr/navigation.json'
import frCommon from '../locales/fr/common.json'
import frTheme from '../locales/fr/theme.json'
import frBranding from '../locales/fr/branding.json'
import frHeader from '../locales/fr/header.json'
import frSidebar from '../locales/fr/sidebar.json'
import frAuth from '../locales/fr/auth.json'
import frDashboard from '../locales/fr/dashboard.json'
import frFeed from '../locales/fr/feed.json'
import frFilters from '../locales/fr/filters.json'
import frSearch from '../locales/fr/search.json'
import frDigests from '../locales/fr/digests.json'
import frDigestViewer from '../locales/fr/digestViewer.json'
import frExports from '../locales/fr/exports.json'
import frChannels from '../locales/fr/channels.json'
import frCollections from '../locales/fr/collections.json'
import frCuratedCollections from '../locales/fr/curatedCollections.json'
import frSettings from '../locales/fr/settings.json'
import frMessages from '../locales/fr/messages.json'
import frAlerts from '../locales/fr/alerts.json'
import frStats from '../locales/fr/stats.json'
import frSummaries from '../locales/fr/summaries.json'
import frAnalysis from '../locales/fr/analysis.json'

const storedLanguage =
  typeof window !== 'undefined' ? localStorage.getItem('osfeed_language') : null

i18n.use(initReactI18next).init({
  resources: {
    en: {
      translation: {
        navigation: enNavigation,
        common: enCommon,
        theme: enTheme,
        branding: enBranding,
        header: enHeader,
        sidebar: enSidebar,
        auth: enAuth,
        dashboard: enDashboard,
        feed: enFeed,
        filters: enFilters,
        search: enSearch,
        digests: enDigests,
        digestViewer: enDigestViewer,
        exports: enExports,
        channels: enChannels,
        collections: enCollections,
        curatedCollections: enCuratedCollections,
        settings: enSettings,
        messages: enMessages,
        alerts: enAlerts,
        stats: enStats,
        summaries: enSummaries,
        analysis: enAnalysis,
      },
    },
    fr: {
      translation: {
        navigation: frNavigation,
        common: frCommon,
        theme: frTheme,
        branding: frBranding,
        header: frHeader,
        sidebar: frSidebar,
        auth: frAuth,
        dashboard: frDashboard,
        feed: frFeed,
        filters: frFilters,
        search: frSearch,
        digests: frDigests,
        digestViewer: frDigestViewer,
        exports: frExports,
        channels: frChannels,
        collections: frCollections,
        curatedCollections: frCuratedCollections,
        settings: frSettings,
        messages: frMessages,
        alerts: frAlerts,
        stats: frStats,
        summaries: frSummaries,
        analysis: frAnalysis,
      },
    },
  },
  lng: storedLanguage ?? 'fr',
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
})
export default i18n
