import { Command } from 'cmdk'

import { Dialog, DialogContent } from '@/components/ui/dialog'
import { useCommandPalette } from '@/hooks/use-command-palette'
import { useUiStore } from '@/stores/ui-store'
import { cn } from '@/lib/cn'

export function CommandPalette() {
  const open = useUiStore((state) => state.commandPaletteOpen)
  const setOpen = useUiStore((state) => state.setCommandPaletteOpen)
  const { commands, handleSelect } = useCommandPalette()

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="max-w-xl overflow-hidden p-0">
        <Command className="w-full">
          <div className="border-b border-border/60 px-4 py-3">
            <Command.Input
              className="w-full bg-transparent text-sm outline-none placeholder:text-foreground/50"
              placeholder="Tapez une commande..."
            />
          </div>
          <Command.List className="max-h-80 overflow-y-auto p-2">
            <Command.Empty className="px-4 py-6 text-sm text-foreground/60">
              Aucun resultat.
            </Command.Empty>
            <Command.Group heading="Navigation" className="px-2 py-1 text-xs uppercase text-foreground/40">
              {commands.map((item) => (
                <Command.Item
                  key={item.id}
                  onSelect={() => handleSelect(item)}
                  className={cn(
                    'flex items-center justify-between rounded-lg px-3 py-2 text-sm text-foreground/80 transition',
                    'data-[selected=true]:bg-primary/10 data-[selected=true]:text-primary',
                  )}
                >
                  <div className="flex items-center gap-2">
                    {item.icon ? <item.icon className="h-4 w-4" /> : null}
                    <span>{item.label}</span>
                  </div>
                  {item.shortcut ? (
                    <span className="text-xs text-foreground/40">{item.shortcut}</span>
                  ) : null}
                </Command.Item>
              ))}
            </Command.Group>
          </Command.List>
        </Command>
      </DialogContent>
    </Dialog>
  )
}
