import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useTranslation } from 'react-i18next'
import { AxiosError } from 'axios'

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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import type { BulkAddResponse } from '@/lib/api/client'

interface AddChannelDialogProps {
  onSubmit: (username: string) => Promise<unknown>
  onBulkSubmit?: (usernames: string[]) => Promise<BulkAddResponse>
  open?: boolean
  onOpenChange?: (open: boolean) => void
  showTrigger?: boolean
}

export function AddChannelDialog({ onSubmit, onBulkSubmit, open: controlledOpen, onOpenChange, showTrigger = true }: AddChannelDialogProps) {
  const { t } = useTranslation()
  const schema = z.object({
    username: z.string().min(2, t('channels.validation')),
  })

  type FormValues = z.infer<typeof schema>

  const [internalOpen, setInternalOpen] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)
  const [mode, setMode] = useState<'single' | 'bulk'>('single')
  const [bulkText, setBulkText] = useState('')
  const [bulkSubmitting, setBulkSubmitting] = useState(false)
  const [bulkResults, setBulkResults] = useState<BulkAddResponse | null>(null)

  // Support both controlled and uncontrolled modes
  const isControlled = controlledOpen !== undefined
  const open = isControlled ? controlledOpen : internalOpen
  const setOpen = isControlled ? (onOpenChange ?? (() => {})) : setInternalOpen
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const submitHandler = async (values: FormValues) => {
    setApiError(null)
    try {
      await onSubmit(values.username)
      reset()
      setOpen(false)
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>
      setApiError(axiosError.response?.data?.detail || t('channels.addError'))
    }
  }

  const parseUsernames = (text: string): string[] => {
    // Split by newlines and commas, then clean up each username
    return text
      .split(/[\n,]/)
      .map(u => u.trim())
      .filter(u => u.length > 0)
  }

  const bulkSubmitHandler = async () => {
    if (!onBulkSubmit) return

    const usernames = parseUsernames(bulkText)
    if (usernames.length === 0) {
      setApiError(t('channels.bulkValidation'))
      return
    }

    setApiError(null)
    setBulkSubmitting(true)
    setBulkResults(null)

    try {
      const results = await onBulkSubmit(usernames)
      setBulkResults(results)

      // If all succeeded, close the dialog after a short delay
      if (results.failure_count === 0) {
        setTimeout(() => {
          setBulkText('')
          setBulkResults(null)
          setOpen(false)
        }, 1500)
      }
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>
      setApiError(axiosError.response?.data?.detail || t('channels.addError'))
    } finally {
      setBulkSubmitting(false)
    }
  }

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      setApiError(null)
      reset()
      setBulkText('')
      setBulkResults(null)
      setMode('single')
    }
    setOpen(newOpen)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      {showTrigger && (
        <DialogTrigger asChild>
          <Button>{t('channels.add')}</Button>
        </DialogTrigger>
      )}
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('channels.addTitle')}</DialogTitle>
          <DialogDescription>
            {mode === 'single' ? t('channels.addDescription') : t('channels.bulkDescription')}
          </DialogDescription>
        </DialogHeader>

        {onBulkSubmit && (
          <Tabs value={mode} onValueChange={(v) => setMode(v as 'single' | 'bulk')}>
            <TabsList className="w-full">
              <TabsTrigger value="single" className="flex-1">{t('channels.singleMode')}</TabsTrigger>
              <TabsTrigger value="bulk" className="flex-1">{t('channels.bulkMode')}</TabsTrigger>
            </TabsList>

            <TabsContent value="single">
              <form className="flex flex-col gap-4" onSubmit={handleSubmit(submitHandler)}>
                {apiError && (
                  <div className="rounded-md bg-danger/10 p-3 text-sm text-danger">{apiError}</div>
                )}
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
            </TabsContent>

            <TabsContent value="bulk">
              <div className="flex flex-col gap-4">
                {apiError && (
                  <div className="rounded-md bg-danger/10 p-3 text-sm text-danger">{apiError}</div>
                )}

                {bulkResults && (
                  <div className={`rounded-md p-3 text-sm ${bulkResults.failure_count === 0 ? 'bg-green-500/10 text-green-700 dark:text-green-400' : 'bg-amber-500/10 text-amber-700 dark:text-amber-400'}`}>
                    <p className="font-medium">
                      {t('channels.bulkResults', { success: bulkResults.success_count, failed: bulkResults.failure_count })}
                    </p>
                    {bulkResults.failed.length > 0 && (
                      <ul className="mt-2 space-y-1 text-xs">
                        {bulkResults.failed.map((f) => (
                          <li key={f.username}>
                            <span className="font-medium">{f.username}</span>: {f.error}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                <div className="flex flex-col gap-2">
                  <Label htmlFor="bulk-channels">{t('channels.channelLabel')}</Label>
                  <Textarea
                    id="bulk-channels"
                    placeholder={t('channels.bulkPlaceholder')}
                    value={bulkText}
                    onChange={(e) => setBulkText(e.target.value)}
                    rows={5}
                  />
                </div>
                <Button type="button" onClick={bulkSubmitHandler} disabled={bulkSubmitting}>
                  {bulkSubmitting ? t('channels.bulkAddSubmitting') : t('channels.addConfirm')}
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        )}

        {!onBulkSubmit && (
          <form className="mt-4 flex flex-col gap-4" onSubmit={handleSubmit(submitHandler)}>
            {apiError && (
              <div className="rounded-md bg-danger/10 p-3 text-sm text-danger">{apiError}</div>
            )}
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
        )}
      </DialogContent>
    </Dialog>
  )
}
