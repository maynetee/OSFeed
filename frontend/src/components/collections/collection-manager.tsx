import { useEffect, useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'

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
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { channelsApi, collectionsApi } from '@/lib/api/client'
import type { Collection } from '@/lib/api/client'

interface CollectionManagerProps {
  onSubmit: (payload: {
    name: string
    description?: string
    channel_ids?: string[]
    is_global?: boolean
    is_default?: boolean
    color?: string
    icon?: string
    auto_assign_languages?: string[]
    auto_assign_keywords?: string[]
    auto_assign_tags?: string[]
    parent_id?: string | null
  }) => Promise<void>
  collection?: Collection | null
  hideTrigger?: boolean
}

export function CollectionManager({ onSubmit, collection, hideTrigger }: CollectionManagerProps) {
  const { t } = useTranslation()
  const schema = z.object({
    name: z.string().min(2, t('collections.validation')),
    description: z.string().optional(),
    is_global: z.boolean().optional(),
    is_default: z.boolean().optional(),
    color: z.string().optional(),
    icon: z.string().optional(),
    auto_assign_languages: z.string().optional(),
    auto_assign_keywords: z.string().optional(),
    auto_assign_tags: z.string().optional(),
    parent_id: z.string().optional(),
  })

  type FormValues = z.infer<typeof schema>

  const [open, setOpen] = useState(false)
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const channelsQuery = useQuery({
    queryKey: ['channels'],
    queryFn: async () => (await channelsApi.list()).data,
  })
  const collectionsQuery = useQuery({
    queryKey: ['collections'],
    queryFn: async () => (await collectionsApi.list()).data,
  })

  const [channelSearch, setChannelSearch] = useState('')
  const [selectedChannels, setSelectedChannels] = useState<string[]>([])
  const [isGlobal, setIsGlobal] = useState(false)
  const [isDefault, setIsDefault] = useState(false)
  const [parentId, setParentId] = useState<string | null>(null)

  useEffect(() => {
    if (collection) {
      reset({
        name: collection.name,
        description: collection.description ?? '',
        is_global: collection.is_global,
        is_default: collection.is_default,
        color: collection.color ?? '',
        icon: collection.icon ?? '',
        auto_assign_languages: (collection.auto_assign_languages ?? []).join(', '),
        auto_assign_keywords: (collection.auto_assign_keywords ?? []).join(', '),
        auto_assign_tags: (collection.auto_assign_tags ?? []).join(', '),
        parent_id: collection.parent_id ?? '',
      })
      setSelectedChannels(collection.channel_ids ?? [])
      setIsGlobal(Boolean(collection.is_global))
      setIsDefault(Boolean(collection.is_default))
      setParentId(collection.parent_id ?? null)
      setOpen(true)
    } else {
      reset({ name: '', description: '' })
      setSelectedChannels([])
      setIsGlobal(false)
      setIsDefault(false)
      setParentId(null)
      setOpen(false)
    }
  }, [collection, reset])

  useEffect(() => {
    setValue('is_global', isGlobal)
    setValue('is_default', isDefault)
  }, [isGlobal, isDefault, setValue])

  const channels = channelsQuery.data ?? []
  const filteredChannels = useMemo(() => {
    const query = channelSearch.trim().toLowerCase()
    if (!query) return channels
    return channels.filter((channel) =>
      [channel.title, channel.username].some((value) => value?.toLowerCase().includes(query)),
    )
  }, [channels, channelSearch])

  const submitHandler = async (values: FormValues) => {
    const toList = (value?: string) =>
      value
        ? value
            .split(',')
            .map((item) => item.trim())
            .filter(Boolean)
        : []
    await onSubmit({
      name: values.name,
      description: values.description,
      channel_ids: isGlobal ? [] : selectedChannels,
      is_global: isGlobal,
      is_default: isDefault,
      color: values.color,
      icon: values.icon,
      auto_assign_languages: toList(values.auto_assign_languages),
      auto_assign_keywords: toList(values.auto_assign_keywords),
      auto_assign_tags: toList(values.auto_assign_tags),
      parent_id: parentId,
    })
    reset({ name: '', description: '' })
    setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      {!hideTrigger ? (
        <DialogTrigger asChild>
          <Button>{t('collections.create')}</Button>
        </DialogTrigger>
      ) : null}
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {collection ? t('collections.editTitle') : t('collections.createTitle')}
          </DialogTitle>
          <DialogDescription>{t('collections.createDescription')}</DialogDescription>
        </DialogHeader>
        <form className="mt-4 flex flex-col gap-4" onSubmit={handleSubmit(submitHandler)}>
          <div className="flex flex-col gap-2">
            <Label htmlFor="name">{t('collections.nameLabel')}</Label>
            <Input id="name" placeholder={t('collections.namePlaceholder')} {...register('name')} />
            {errors.name ? (
              <span className="text-xs text-danger">{errors.name.message}</span>
            ) : null}
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="description">{t('collections.descriptionLabel')}</Label>
            <Textarea
              id="description"
              placeholder={t('collections.descriptionPlaceholder')}
              {...register('description')}
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant={isGlobal ? 'default' : 'outline'}
              size="sm"
              onClick={() =>
                setIsGlobal((value) => {
                  if (!value) {
                    setSelectedChannels([])
                  }
                  return !value
                })
              }
            >
              {t('collections.allChannels')}
            </Button>
            <Button
              type="button"
              variant={isDefault ? 'default' : 'outline'}
              size="sm"
              onClick={() => setIsDefault((value) => !value)}
            >
              {t('collections.defaultCollection')}
            </Button>
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="channelSearch">{t('collections.channelSearch')}</Label>
            <Input
              id="channelSearch"
              placeholder={t('collections.channelSearchPlaceholder')}
              value={channelSearch}
              onChange={(event) => setChannelSearch(event.target.value)}
            />
          </div>
          <div className="flex flex-wrap gap-2">
            {filteredChannels.map((channel) => {
              const active = selectedChannels.includes(channel.id)
              return (
                <Button
                  key={channel.id}
                  type="button"
                  variant={active ? 'secondary' : 'outline'}
                  size="sm"
                  disabled={isGlobal}
                  onClick={() =>
                    setSelectedChannels(
                      active
                        ? selectedChannels.filter((id) => id !== channel.id)
                        : [...selectedChannels, channel.id],
                    )
                  }
                >
                  {channel.title}
                </Button>
              )
            })}
          </div>
          {selectedChannels.length ? (
            <div className="flex flex-wrap gap-2">
              {selectedChannels.map((channelId) => {
                const channel = channels.find((item) => item.id === channelId)
                return (
                  <Badge key={channelId} variant="outline">
                    {channel?.title ?? channelId}
                  </Badge>
                )
              })}
            </div>
          ) : null}
          <div className="grid gap-3 md:grid-cols-2">
            <div className="flex flex-col gap-2">
              <Label htmlFor="color">{t('collections.colorLabel')}</Label>
              <Input id="color" placeholder="#1f2937" {...register('color')} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="icon">{t('collections.iconLabel')}</Label>
              <Input id="icon" placeholder="🛰️" {...register('icon')} />
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="auto_assign_languages">{t('collections.autoAssignLanguages')}</Label>
            <Input
              id="auto_assign_languages"
              placeholder={t('collections.autoAssignLanguagesPlaceholder')}
              {...register('auto_assign_languages')}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="auto_assign_keywords">{t('collections.autoAssignKeywords')}</Label>
            <Input
              id="auto_assign_keywords"
              placeholder={t('collections.autoAssignKeywordsPlaceholder')}
              {...register('auto_assign_keywords')}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="auto_assign_tags">{t('collections.autoAssignTags')}</Label>
            <Input
              id="auto_assign_tags"
              placeholder={t('collections.autoAssignTagsPlaceholder')}
              {...register('auto_assign_tags')}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label>{t('collections.parentLabel')}</Label>
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant={!parentId ? 'secondary' : 'outline'}
                size="sm"
                onClick={() => setParentId(null)}
              >
                {t('collections.parentNone')}
              </Button>
              {(collectionsQuery.data ?? [])
                .filter((item) => item.id !== collection?.id)
                .map((item) => (
                  <Button
                    key={item.id}
                    type="button"
                    variant={parentId === item.id ? 'secondary' : 'outline'}
                    size="sm"
                    onClick={() => setParentId(item.id)}
                  >
                    {item.name}
                  </Button>
                ))}
            </div>
          </div>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? t('collections.saving') : t('collections.save')}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
