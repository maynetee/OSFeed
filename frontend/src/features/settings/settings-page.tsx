import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { messagesApi, LANGUAGES } from '@/lib/api/client'

export function SettingsPage() {
  const { i18n, t } = useTranslation()
  const queryClient = useQueryClient()
  const [isTranslating, setIsTranslating] = useState(false)

  const handleLanguageChange = async (value: string) => {
    setIsTranslating(true)
    i18n.changeLanguage(value)
    localStorage.setItem('telescope_language', value)
    try {
      await messagesApi.translate(value)
      queryClient.invalidateQueries({ queryKey: ['messages'] })
    } finally {
      setIsTranslating(false)
    }
  }

  return (
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
          <div className="flex flex-wrap gap-2">
            <Button variant="outline">{t('settings.notificationEmail')}</Button>
            <Button variant="outline">{t('settings.notificationSlack')}</Button>
            <Button variant="outline">{t('settings.notificationTelegram')}</Button>
          </div>
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
            {isTranslating ? <p className="text-xs text-primary">{t('settings.translating')}</p> : null}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
