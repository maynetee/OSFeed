import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const schema = z.object({
  username: z.string().min(2, 'Renseignez un canal'),
})

type FormValues = z.infer<typeof schema>

interface AddChannelDialogProps {
  onSubmit: (username: string) => Promise<unknown>
}

export function AddChannelDialog({ onSubmit }: AddChannelDialogProps) {
  const [open, setOpen] = useState(false)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const submitHandler = async (values: FormValues) => {
    await onSubmit(values.username)
    reset()
    setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Ajouter un canal</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Ajouter une source Telegram</DialogTitle>
          <DialogDescription>Entrez le @username du canal.</DialogDescription>
        </DialogHeader>
        <form className="mt-4 flex flex-col gap-4" onSubmit={handleSubmit(submitHandler)}>
          <div className="flex flex-col gap-2">
            <Label htmlFor="username">Canal</Label>
            <Input id="username" placeholder="@channel" {...register('username')} />
            {errors.username ? (
              <span className="text-xs text-danger">{errors.username.message}</span>
            ) : null}
          </div>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Ajout en cours...' : 'Ajouter'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
