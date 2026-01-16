import { useEffect, useState } from 'react'
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
import { Textarea } from '@/components/ui/textarea'
import type { Collection } from '@/lib/api/client'

const schema = z.object({
  name: z.string().min(2, 'Nom requis'),
  description: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

interface CollectionManagerProps {
  onSubmit: (payload: { name: string; description?: string }) => Promise<void>
  collection?: Collection | null
}

export function CollectionManager({ onSubmit, collection }: CollectionManagerProps) {
  const [open, setOpen] = useState(false)
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  useEffect(() => {
    if (collection) {
      reset({ name: collection.name, description: collection.description ?? '' })
      setOpen(true)
    }
  }, [collection, reset])

  const submitHandler = async (values: FormValues) => {
    await onSubmit(values)
    reset({ name: '', description: '' })
    setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Nouvelle collection</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{collection ? 'Modifier la collection' : 'Nouvelle collection'}</DialogTitle>
          <DialogDescription>Regroupez vos canaux par thematique.</DialogDescription>
        </DialogHeader>
        <form className="mt-4 flex flex-col gap-4" onSubmit={handleSubmit(submitHandler)}>
          <div className="flex flex-col gap-2">
            <Label htmlFor="name">Nom</Label>
            <Input id="name" placeholder="Nom de collection" {...register('name')} />
            {errors.name ? <span className="text-xs text-danger">{errors.name.message}</span> : null}
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="description">Description</Label>
            <Textarea id="description" placeholder="Objectif, sources, focus" {...register('description')} />
          </div>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Sauvegarde...' : 'Enregistrer'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
