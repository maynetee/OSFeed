import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useUserStore } from '@/stores/user-store'

export function RegisterPage() {
  const navigate = useNavigate()
  const setUser = useUserStore((state) => state.setUser)
  const { t } = useTranslation()

  const handleRegister = () => {
    setUser({ id: 'demo', name: 'Demo Analyst', role: 'analyst' })
    navigate('/')
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-auth px-6 py-12">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>{t('auth.registerTitle')}</CardTitle>
          <CardDescription>{t('auth.registerDescription')}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Input type="text" placeholder={t('auth.fullNamePlaceholder')} />
          <Input type="email" placeholder={t('auth.emailPlaceholder')} />
          <Input type="password" placeholder={t('auth.passwordPlaceholder')} />
          <Button className="w-full" onClick={handleRegister}>
            {t('auth.start')}
          </Button>
          <Button variant="ghost" className="w-full text-foreground/60">
            {t('auth.haveAccount')}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
