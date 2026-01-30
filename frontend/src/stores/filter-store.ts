import { create } from 'zustand'

interface FilterState {
  channelIds: string[]
  collectionIds: string[]
  mediaTypes: string[]
  dateRange: '24h' | '7d' | '30d' | 'all'
  filtersTouched: boolean
  setChannelIds: (ids: string[]) => void
  setCollectionIds: (ids: string[]) => void
  setMediaTypes: (types: string[]) => void
  setDateRange: (range: FilterState['dateRange']) => void
  setFiltersTouched: (touched: boolean) => void
  resetFilters: () => void
}

export const useFilterStore = create<FilterState>((set) => ({
  channelIds: [],
  collectionIds: [],
  mediaTypes: [],
  dateRange: 'all',
  filtersTouched: false,
  setChannelIds: (ids) => set({ channelIds: ids }),
  setCollectionIds: (ids) => set({ collectionIds: ids }),
  setMediaTypes: (types) => set({ mediaTypes: types }),
  setDateRange: (range) => set({ dateRange: range }),
  setFiltersTouched: (touched) => set({ filtersTouched: touched }),
  resetFilters: () => set({ channelIds: [], collectionIds: [], mediaTypes: [], filtersTouched: false, dateRange: 'all' }),
}))
