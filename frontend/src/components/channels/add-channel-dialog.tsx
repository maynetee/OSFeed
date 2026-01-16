import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useTranslation } from 'react-i18next'

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

interface AddChannelDialogProps {
  onSubmit: (username: string) => Promise<unknown>
}

export function AddChannelDialog({ onSubmit }: AddChannelDialogProps) {
  const { t } = useTranslation()
  const schema = z.object({
    username: z.string().min(2, t('channels.validation')),
  })

  type FormValues = z.infer<typeof schema>

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
        <Button>{t('channels.add')}</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('channels.addTitle')}</DialogTitle>
          <DialogDescription>{t('channels.addDescription')}</DialogDescription>
        </DialogHeader>
        <form className="mt-4 flex flex-col gap-4" onSubmit={handleSubmit(submitHandler)}>
          <div className="flex flex-col gap-2">
            <Label htmlFor="username">{t('channels.channelLabel')}</Label>
            <Input id="username" placeholder={t('channels.channelPlaceholder')} {...register('username')} />
            {errors.username ? (
              <span className="text-xs text-danger">{errors.username.message}</span>
            ) : null}
          </div>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? t('channels.addSubmitting') : t('channels.addConfirm')}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
