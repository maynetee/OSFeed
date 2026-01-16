import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { messagesApi, LANGUAGES } from '@/lib/api/client'

export function SettingsPage() {
  const { i18n } = useTranslation()
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
        <p className="text-sm text-foreground/60">Preferences</p>
        <h2 className="text-2xl font-semibold">Parametres</h2>
      </div>

      <Card>
        <CardContent className="flex flex-col gap-4 py-6">
          <div>
            <p className="text-sm font-semibold">Notifications</p>
            <p className="text-xs text-foreground/60">Activez les alertes sur signaux forts.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline">Email</Button>
            <Button variant="outline">Slack</Button>
            <Button variant="outline">Telegram</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="flex flex-col gap-4 py-6">
          <div>
            <p className="text-sm font-semibold">Langue interface</p>
            <p className="text-xs text-foreground/60">Synchronise les traductions des messages.</p>
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="language">Langue</Label>
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
            {isTranslating ? <p className="text-xs text-primary">Traduction en cours...</p> : null}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
