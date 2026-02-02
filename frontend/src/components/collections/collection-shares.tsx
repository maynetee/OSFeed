import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'

import { collectionsApi } from '@/lib/api/client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ConfirmDialog } from '@/components/common/confirm-dialog'

interface CollectionSharesProps {
  collectionId: string
}

export function CollectionShares({ collectionId }: CollectionSharesProps) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [userId, setUserId] = useState('')
  const [permission, setPermission] = useState('viewer')

  const sharesQuery = useQuery({
    queryKey: ['collection-shares', collectionId],
    queryFn: async () => (await collectionsApi.shares(collectionId)).data,
  })

  const addShare = useMutation({
    mutationFn: () => collectionsApi.addShare(collectionId, { user_id: userId, permission }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collection-shares', collectionId] })
      setUserId('')
    },
  })

  const removeShare = useMutation({
    mutationFn: (id: string) => collectionsApi.removeShare(collectionId, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collection-shares', collectionId] })
    },
  })

  const shares = sharesQuery.data ?? []

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('collections.sharesTitle')}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-[2fr_1fr_auto]">
          <div className="flex flex-col gap-2">
            <Label htmlFor="share-user">{t('collections.sharesUser')}</Label>
            <Input
              id="share-user"
              placeholder="UUID"
              value={userId}
              onChange={(event) => setUserId(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label>{t('collections.sharesPermission')}</Label>
            <div className="flex flex-wrap gap-2">
              {['viewer', 'editor', 'admin'].map((role) => (
                <Button
                  key={role}
                  type="button"
                  variant={permission === role ? 'secondary' : 'outline'}
                  size="sm"
                  onClick={() => setPermission(role)}
                >
                  {role}
                </Button>
              ))}
            </div>
          </div>
          <div className="flex items-end">
            <Button onClick={() => addShare.mutate()} disabled={!userId.trim()}>
              {t('collections.sharesAdd')}
            </Button>
          </div>
        </div>
        <div className="space-y-2">
          {shares.length ? (
            shares.map((share: { user_id: string; permission: string }) => (
              <div key={share.user_id} className="flex items-center justify-between text-sm">
                <span>{share.user_id}</span>
                <div className="flex items-center gap-2">
                  <span className="text-foreground/60">{share.permission}</span>
                  <ConfirmDialog
                    title={t('collections.removeShareTitle')}
                    description={t('collections.removeShareDescription')}
                    confirmText={t('collections.remove')}
                    cancelText={t('collections.cancel')}
                    variant="destructive"
                    onConfirm={() => removeShare.mutate(share.user_id)}
                    triggerButton={
                      <Button variant="outline" size="sm">
                        {t('collections.remove')}
                      </Button>
                    }
                  />
                </div>
              </div>
            ))
          ) : (
            <p className="text-sm text-foreground/60">{t('collections.sharesEmpty')}</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
