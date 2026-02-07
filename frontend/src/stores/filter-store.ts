import { create } from 'zustand'

interface FilterState {
  channelIds: string[]
  collectionIds: string[]
  mediaTypes: string[]
  dateRange: '24h' | '7d' | '30d' | 'all'
  region: string
  topic: string
  filtersTouched: boolean
  setChannelIds: (ids: string[]) => void
  setCollectionIds: (ids: string[]) => void
  setMediaTypes: (types: string[]) => void
  setDateRange: (range: FilterState['dateRange']) => void
  setRegion: (region: string) => void
  setTopic: (topic: string) => void
  setFiltersTouched: (touched: boolean) => void
  resetFilters: () => void
}

export const useFilterStore = create<FilterState>((set) => ({
  channelIds: [],
  collectionIds: [],
  mediaTypes: [],
  dateRange: 'all',
  region: '',
  topic: '',
  filtersTouched: false,
  setChannelIds: (ids) => set({ channelIds: ids }),
  setCollectionIds: (ids) => set({ collectionIds: ids }),
  setMediaTypes: (types) => set({ mediaTypes: types }),
  setDateRange: (range) => set({ dateRange: range }),
  setRegion: (region) => set({ region }),
  setTopic: (topic) => set({ topic }),
  setFiltersTouched: (touched) => set({ filtersTouched: touched }),
  resetFilters: () => set({ channelIds: [], collectionIds: [], mediaTypes: [], region: '', topic: '', filtersTouched: false, dateRange: 'all' }),
}))
