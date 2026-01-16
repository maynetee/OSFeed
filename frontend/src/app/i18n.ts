import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

const resources = {
  en: {
    translation: {
      navigation: {
        dashboard: 'Dashboard',
        feed: 'Feed',
        search: 'Search',
        digests: 'Digests',
        channels: 'Channels',
        collections: 'Collections',
        exports: 'Exports',
        settings: 'Settings',
      },
    },
  },
  fr: {
    translation: {
      navigation: {
        dashboard: 'Dashboard',
        feed: 'Fil',
        search: 'Recherche',
        digests: 'Digests',
        channels: 'Canaux',
        collections: 'Collections',
        exports: 'Exports',
        settings: 'Parametres',
      },
    },
  },
}

const storedLanguage =
  typeof window !== 'undefined' ? localStorage.getItem('telescope_language') : null

i18n.use(initReactI18next).init({
  resources,
  lng: storedLanguage ?? 'fr',
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
})

export default i18n
