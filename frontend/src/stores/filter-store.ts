import { create } from 'zustand'

interface FilterState {
  channelIds: string[]
  collectionIds: string[]
  dateRange: '24h' | '7d' | '30d'
  setChannelIds: (ids: string[]) => void
  setCollectionIds: (ids: string[]) => void
  setDateRange: (range: FilterState['dateRange']) => void
}

export const useFilterStore = create<FilterState>((set) => ({
  channelIds: [],
  collectionIds: [],
  dateRange: '24h',
  setChannelIds: (ids) => set({ channelIds: ids }),
  setCollectionIds: (ids) => set({ collectionIds: ids }),
  setDateRange: (range) => set({ dateRange: range }),
}))
