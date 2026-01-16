import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useUserStore } from '@/stores/user-store'

export function RegisterPage() {
  const navigate = useNavigate()
  const setUser = useUserStore((state) => state.setUser)

  const handleRegister = () => {
    setUser({ id: 'demo', name: 'Demo Analyst', role: 'analyst' })
    navigate('/')
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-auth px-6 py-12">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Creer votre espace</CardTitle>
          <CardDescription>Lancez un briefing sans bruit, des aujourd'hui.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Input type="text" placeholder="Nom complet" />
          <Input type="email" placeholder="Email" />
          <Input type="password" placeholder="Mot de passe" />
          <Button className="w-full" onClick={handleRegister}>
            Demarrer
          </Button>
          <Button variant="ghost" className="w-full text-foreground/60">
            J'ai deja un compte
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
