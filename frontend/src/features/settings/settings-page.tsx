import { useState, useEffect, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'

import { PageTransition } from '@/components/layout/page-transition'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { messagesApi, LANGUAGES, collectionsApi } from '@/lib/api/client'
import { digestsApi } from '@/lib/api/digests'

const PREFS_KEY = 'osfeed_notification_prefs'

function loadPrefs(): { email: boolean; in_app: boolean } {
  try {
    const stored = localStorage.getItem(PREFS_KEY)
    if (stored) return JSON.parse(stored)
  } catch {
    /* ignore */
  }
  return { email: false, in_app: true }
}

function savePrefs(prefs: { email: boolean; in_app: boolean }) {
  localStorage.setItem(PREFS_KEY, JSON.stringify(prefs))
}

const HOURS = Array.from({ length: 24 }, (_, i) => i)
const MAX_MSG_OPTIONS = [10, 20, 50]

export function SettingsPage() {
  const { i18n, t } = useTranslation()
  const queryClient = useQueryClient()
  const [isTranslating, setIsTranslating] = useState(false)
  const [prefs, setPrefs] = useState(loadPrefs)
  const [previewStatus, setPreviewStatus] = useState<string | null>(null)

  useEffect(() => {
    savePrefs(prefs)
  }, [prefs])

  // Fetch digest preferences
  const { data: digestData, isLoading: digestLoading } = useQuery({
    queryKey: ['digest-preferences'],
    queryFn: () => digestsApi.getPreferences().then((r) => r.data),
  })

  // Fetch user collections for multi-select
  const { data: collectionsData } = useQuery({
    queryKey: ['collections'],
    queryFn: () => collectionsApi.list().then((r) => r.data),
  })

  // Update digest preferences
  const updateDigest = useMutation({
    mutationFn: (payload: Parameters<typeof digestsApi.updatePreferences>[0]) =>
      digestsApi.updatePreferences(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['digest-preferences'] }),
  })

  // Send preview
  const sendPreview = useMutation({
    mutationFn: () =>
      digestsApi.sendPreview({
        collection_ids: digestData?.collection_ids || undefined,
        max_messages: digestData?.max_messages,
      }),
    onSuccess: () => setPreviewStatus(t('settings.digestPreviewSent')),
    onError: () => setPreviewStatus(t('settings.digestPreviewError')),
  })

  const handleDigestToggle = useCallback(
    (enabled: boolean) => updateDigest.mutate({ enabled }),
    [updateDigest],
  )

  const handleFrequencyChange = useCallback(
    (frequency: string) => updateDigest.mutate({ frequency }),
    [updateDigest],
  )

  const handleHourChange = useCallback(
    (send_hour: number) => updateDigest.mutate({ send_hour }),
    [updateDigest],
  )

  const handleMaxMessagesChange = useCallback(
    (max_messages: number) => updateDigest.mutate({ max_messages }),
    [updateDigest],
  )

  const handleCollectionToggle = useCallback(
    (collectionId: string, checked: boolean) => {
      const current = digestData?.collection_ids || []
      const updated = checked
        ? [...current, collectionId]
        : current.filter((id) => id !== collectionId)
      updateDigest.mutate({ collection_ids: updated })
    },
    [updateDigest, digestData],
  )

  const handleLanguageChange = async (value: string) => {
    setIsTranslating(true)
    i18n.changeLanguage(value)
    localStorage.setItem('osfeed_language', value)
    try {
      await messagesApi.translate(value)
      queryClient.invalidateQueries({ queryKey: ['messages'] })
    } finally {
      setIsTranslating(false)
    }
  }

  return (
    <PageTransition>
      <div className="flex flex-col gap-6">
        <div>
          <p className="text-sm text-foreground/60">{t('settings.subtitle')}</p>
          <h2 className="text-2xl font-semibold">{t('settings.title')}</h2>
        </div>

        <Card>
          <CardContent className="flex flex-col gap-4 py-6">
            <div>
              <p className="text-sm font-semibold">{t('settings.notificationsTitle')}</p>
              <p className="text-xs text-foreground/60">{t('settings.notificationsDescription')}</p>
            </div>
            <div className="flex flex-col gap-3">
              <label className="flex items-center justify-between">
                <span className="text-sm">{t('settings.notificationInApp')}</span>
                <input
                  type="checkbox"
                  checked={prefs.in_app}
                  onChange={(e) => setPrefs((p) => ({ ...p, in_app: e.target.checked }))}
                  className="h-4 w-4 accent-primary"
                />
              </label>
              <label className="flex items-center justify-between">
                <span className="text-sm">{t('settings.notificationEmail')}</span>
                <input
                  type="checkbox"
                  checked={prefs.email}
                  onChange={(e) => setPrefs((p) => ({ ...p, email: e.target.checked }))}
                  className="h-4 w-4 accent-primary"
                />
              </label>
            </div>
          </CardContent>
        </Card>

        {/* Daily Digest Section */}
        <Card>
          <CardContent className="flex flex-col gap-4 py-6">
            <div>
              <p className="text-sm font-semibold">{t('settings.digestTitle')}</p>
              <p className="text-xs text-foreground/60">{t('settings.digestDescription')}</p>
            </div>

            {digestLoading ? (
              <p className="text-xs text-foreground/40">{t('settings.digestLoading')}</p>
            ) : (
              <div className="flex flex-col gap-4">
                {/* Enable toggle */}
                <label className="flex items-center justify-between">
                  <span className="text-sm">{t('settings.digestEnabled')}</span>
                  <input
                    type="checkbox"
                    checked={digestData?.enabled ?? false}
                    onChange={(e) => handleDigestToggle(e.target.checked)}
                    className="h-4 w-4 accent-primary"
                  />
                </label>

                {/* Frequency */}
                <div className="flex flex-col gap-1">
                  <Label htmlFor="digest-frequency">{t('settings.digestFrequency')}</Label>
                  <select
                    id="digest-frequency"
                    value={digestData?.frequency ?? 'daily'}
                    onChange={(e) => handleFrequencyChange(e.target.value)}
                    className="rounded border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="daily">{t('settings.digestDaily')}</option>
                    <option value="weekly">{t('settings.digestWeekly')}</option>
                  </select>
                </div>

                {/* Send hour */}
                <div className="flex flex-col gap-1">
                  <Label htmlFor="digest-hour">{t('settings.digestSendHour')}</Label>
                  <select
                    id="digest-hour"
                    value={digestData?.send_hour ?? 8}
                    onChange={(e) => handleHourChange(Number(e.target.value))}
                    className="rounded border border-input bg-background px-3 py-2 text-sm"
                  >
                    {HOURS.map((h) => (
                      <option key={h} value={h}>
                        {String(h).padStart(2, '0')}:00 UTC
                      </option>
                    ))}
                  </select>
                </div>

                {/* Max messages */}
                <div className="flex flex-col gap-1">
                  <Label htmlFor="digest-max">{t('settings.digestMaxMessages')}</Label>
                  <select
                    id="digest-max"
                    value={digestData?.max_messages ?? 20}
                    onChange={(e) => handleMaxMessagesChange(Number(e.target.value))}
                    className="rounded border border-input bg-background px-3 py-2 text-sm"
                  >
                    {MAX_MSG_OPTIONS.map((n) => (
                      <option key={n} value={n}>
                        {n}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Collection multi-select */}
                {collectionsData && collectionsData.length > 0 && (
                  <div className="flex flex-col gap-2">
                    <Label>{t('settings.digestCollections')}</Label>
                    <div className="flex flex-col gap-1 max-h-48 overflow-y-auto rounded border border-input p-2">
                      {collectionsData.map((col) => (
                        <label key={col.id} className="flex items-center gap-2 text-sm">
                          <input
                            type="checkbox"
                            checked={(digestData?.collection_ids || []).includes(col.id)}
                            onChange={(e) => handleCollectionToggle(col.id, e.target.checked)}
                            className="h-3.5 w-3.5 accent-primary"
                          />
                          {col.name}
                        </label>
                      ))}
                    </div>
                    <p className="text-xs text-foreground/40">
                      {t('settings.digestCollectionsHint')}
                    </p>
                  </div>
                )}

                {/* Send Preview */}
                <button
                  onClick={() => {
                    setPreviewStatus(null)
                    sendPreview.mutate()
                  }}
                  disabled={sendPreview.isPending}
                  className="self-start rounded bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  {sendPreview.isPending
                    ? t('settings.digestSending')
                    : t('settings.digestSendPreview')}
                </button>
                {previewStatus && <p className="text-xs text-foreground/60">{previewStatus}</p>}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex flex-col gap-4 py-6">
            <div>
              <p className="text-sm font-semibold">{t('settings.languageTitle')}</p>
              <p className="text-xs text-foreground/60">{t('settings.languageDescription')}</p>
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="language">{t('settings.languageLabel')}</Label>
              <Input
                id="language"
                list="language-options"
                defaultValue={i18n.language}
                onBlur={(event) => handleLanguageChange(event.target.value)}
              />
              <datalist id="language-options">
                {LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name}
                  </option>
                ))}
              </datalist>
              {isTranslating ? (
                <p className="text-xs text-primary">{t('settings.translating')}</p>
              ) : null}
            </div>
          </CardContent>
        </Card>
      </div>
    </PageTransition>
  )
}
