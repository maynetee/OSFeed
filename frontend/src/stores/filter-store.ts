import { create } from 'zustand'

interface FilterState {
  channelIds: string[]
  collectionIds: string[]
  dateRange: '24h' | '7d' | '30d' | 'all'
  filtersTouched: boolean
  setChannelIds: (ids: string[]) => void
  setCollectionIds: (ids: string[]) => void
  setDateRange: (range: FilterState['dateRange']) => void
  setFiltersTouched: (touched: boolean) => void
  resetFilters: () => void
}

export const useFilterStore = create<FilterState>((set) => ({
  channelIds: [],
  collectionIds: [],
  dateRange: 'all',
  filtersTouched: false,
  setChannelIds: (ids) => set({ channelIds: ids }),
  setCollectionIds: (ids) => set({ collectionIds: ids }),
  setDateRange: (range) => set({ dateRange: range }),
  setFiltersTouched: (touched) => set({ filtersTouched: touched }),
  resetFilters: () => set({ channelIds: [], collectionIds: [], filtersTouched: false, dateRange: 'all' }),
}))
