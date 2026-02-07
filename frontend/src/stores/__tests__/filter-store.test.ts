import { describe, it, expect, beforeEach } from 'vitest'
import { useFilterStore } from '../filter-store'

describe('useFilterStore', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useFilterStore.setState({
      channelIds: [],
      collectionIds: [],
      mediaTypes: [],
      dateRange: 'all',
      filtersTouched: false,
    })
  })

  describe('initial state', () => {
    it('should have empty channelIds array initially', () => {
      const state = useFilterStore.getState()
      expect(state.channelIds).toEqual([])
    })

    it('should have empty collectionIds array initially', () => {
      const state = useFilterStore.getState()
      expect(state.collectionIds).toEqual([])
    })

    it('should have empty mediaTypes array initially', () => {
      const state = useFilterStore.getState()
      expect(state.mediaTypes).toEqual([])
    })

    it('should have dateRange as "all" initially', () => {
      const state = useFilterStore.getState()
      expect(state.dateRange).toBe('all')
    })

    it('should have filtersTouched as false initially', () => {
      const state = useFilterStore.getState()
      expect(state.filtersTouched).toBe(false)
    })
  })

  describe('setChannelIds', () => {
    it('should set channelIds with single id', () => {
      const { setChannelIds } = useFilterStore.getState()

      setChannelIds(['channel-1'])

      expect(useFilterStore.getState().channelIds).toEqual(['channel-1'])
    })

    it('should set channelIds with multiple ids', () => {
      const { setChannelIds } = useFilterStore.getState()

      setChannelIds(['channel-1', 'channel-2', 'channel-3'])

      expect(useFilterStore.getState().channelIds).toEqual(['channel-1', 'channel-2', 'channel-3'])
    })

    it('should update channelIds when called multiple times', () => {
      const { setChannelIds } = useFilterStore.getState()

      setChannelIds(['channel-a'])
      expect(useFilterStore.getState().channelIds).toEqual(['channel-a'])

      setChannelIds(['channel-b', 'channel-c'])
      expect(useFilterStore.getState().channelIds).toEqual(['channel-b', 'channel-c'])
    })

    it('should set channelIds to empty array', () => {
      const { setChannelIds } = useFilterStore.getState()

      setChannelIds(['channel-x'])
      expect(useFilterStore.getState().channelIds).toEqual(['channel-x'])

      setChannelIds([])
      expect(useFilterStore.getState().channelIds).toEqual([])
    })
  })

  describe('setCollectionIds', () => {
    it('should set collectionIds with single id', () => {
      const { setCollectionIds } = useFilterStore.getState()

      setCollectionIds(['collection-1'])

      expect(useFilterStore.getState().collectionIds).toEqual(['collection-1'])
    })

    it('should set collectionIds with multiple ids', () => {
      const { setCollectionIds } = useFilterStore.getState()

      setCollectionIds(['collection-1', 'collection-2', 'collection-3'])

      expect(useFilterStore.getState().collectionIds).toEqual([
        'collection-1',
        'collection-2',
        'collection-3',
      ])
    })

    it('should update collectionIds when called multiple times', () => {
      const { setCollectionIds } = useFilterStore.getState()

      setCollectionIds(['collection-a'])
      expect(useFilterStore.getState().collectionIds).toEqual(['collection-a'])

      setCollectionIds(['collection-b', 'collection-c'])
      expect(useFilterStore.getState().collectionIds).toEqual(['collection-b', 'collection-c'])
    })

    it('should set collectionIds to empty array', () => {
      const { setCollectionIds } = useFilterStore.getState()

      setCollectionIds(['collection-x'])
      expect(useFilterStore.getState().collectionIds).toEqual(['collection-x'])

      setCollectionIds([])
      expect(useFilterStore.getState().collectionIds).toEqual([])
    })
  })

  describe('setMediaTypes', () => {
    it('should set mediaTypes with single type', () => {
      const { setMediaTypes } = useFilterStore.getState()

      setMediaTypes(['image'])

      expect(useFilterStore.getState().mediaTypes).toEqual(['image'])
    })

    it('should set mediaTypes with multiple types', () => {
      const { setMediaTypes } = useFilterStore.getState()

      setMediaTypes(['image', 'video', 'audio', 'text'])

      expect(useFilterStore.getState().mediaTypes).toEqual(['image', 'video', 'audio', 'text'])
    })

    it('should update mediaTypes when called multiple times', () => {
      const { setMediaTypes } = useFilterStore.getState()

      setMediaTypes(['image'])
      expect(useFilterStore.getState().mediaTypes).toEqual(['image'])

      setMediaTypes(['video', 'audio'])
      expect(useFilterStore.getState().mediaTypes).toEqual(['video', 'audio'])
    })

    it('should set mediaTypes to empty array', () => {
      const { setMediaTypes } = useFilterStore.getState()

      setMediaTypes(['image', 'video'])
      expect(useFilterStore.getState().mediaTypes).toEqual(['image', 'video'])

      setMediaTypes([])
      expect(useFilterStore.getState().mediaTypes).toEqual([])
    })
  })

  describe('setDateRange', () => {
    it('should set dateRange to "24h"', () => {
      const { setDateRange } = useFilterStore.getState()

      setDateRange('24h')

      expect(useFilterStore.getState().dateRange).toBe('24h')
    })

    it('should set dateRange to "7d"', () => {
      const { setDateRange } = useFilterStore.getState()

      setDateRange('7d')

      expect(useFilterStore.getState().dateRange).toBe('7d')
    })

    it('should set dateRange to "30d"', () => {
      const { setDateRange } = useFilterStore.getState()

      setDateRange('30d')

      expect(useFilterStore.getState().dateRange).toBe('30d')
    })

    it('should set dateRange to "all"', () => {
      const { setDateRange } = useFilterStore.getState()

      // First change to something else
      setDateRange('24h')
      expect(useFilterStore.getState().dateRange).toBe('24h')

      // Then back to all
      setDateRange('all')
      expect(useFilterStore.getState().dateRange).toBe('all')
    })

    it('should update dateRange when called multiple times', () => {
      const { setDateRange } = useFilterStore.getState()

      setDateRange('24h')
      expect(useFilterStore.getState().dateRange).toBe('24h')

      setDateRange('7d')
      expect(useFilterStore.getState().dateRange).toBe('7d')

      setDateRange('30d')
      expect(useFilterStore.getState().dateRange).toBe('30d')

      setDateRange('all')
      expect(useFilterStore.getState().dateRange).toBe('all')
    })
  })

  describe('setFiltersTouched', () => {
    it('should set filtersTouched to true', () => {
      const { setFiltersTouched } = useFilterStore.getState()

      expect(useFilterStore.getState().filtersTouched).toBe(false)

      setFiltersTouched(true)

      expect(useFilterStore.getState().filtersTouched).toBe(true)
    })

    it('should set filtersTouched to false', () => {
      const { setFiltersTouched } = useFilterStore.getState()

      setFiltersTouched(true)
      expect(useFilterStore.getState().filtersTouched).toBe(true)

      setFiltersTouched(false)

      expect(useFilterStore.getState().filtersTouched).toBe(false)
    })

    it('should toggle filtersTouched multiple times', () => {
      const { setFiltersTouched } = useFilterStore.getState()

      setFiltersTouched(true)
      expect(useFilterStore.getState().filtersTouched).toBe(true)

      setFiltersTouched(false)
      expect(useFilterStore.getState().filtersTouched).toBe(false)

      setFiltersTouched(true)
      expect(useFilterStore.getState().filtersTouched).toBe(true)
    })
  })

  describe('resetFilters', () => {
    it('should reset all filter values to initial state', () => {
      const {
        setChannelIds,
        setCollectionIds,
        setMediaTypes,
        setDateRange,
        setFiltersTouched,
        resetFilters,
      } = useFilterStore.getState()

      // Set some values
      setChannelIds(['channel-1', 'channel-2'])
      setCollectionIds(['collection-1'])
      setMediaTypes(['image', 'video'])
      setDateRange('24h')
      setFiltersTouched(true)

      // Verify values are set
      expect(useFilterStore.getState().channelIds).toEqual(['channel-1', 'channel-2'])
      expect(useFilterStore.getState().collectionIds).toEqual(['collection-1'])
      expect(useFilterStore.getState().mediaTypes).toEqual(['image', 'video'])
      expect(useFilterStore.getState().dateRange).toBe('24h')
      expect(useFilterStore.getState().filtersTouched).toBe(true)

      // Reset
      resetFilters()

      // Verify all values are reset
      expect(useFilterStore.getState().channelIds).toEqual([])
      expect(useFilterStore.getState().collectionIds).toEqual([])
      expect(useFilterStore.getState().mediaTypes).toEqual([])
      expect(useFilterStore.getState().dateRange).toBe('all')
      expect(useFilterStore.getState().filtersTouched).toBe(false)
    })

    it('should work when filters are already at initial state', () => {
      const { resetFilters } = useFilterStore.getState()

      // Initial state
      expect(useFilterStore.getState().channelIds).toEqual([])
      expect(useFilterStore.getState().collectionIds).toEqual([])
      expect(useFilterStore.getState().mediaTypes).toEqual([])
      expect(useFilterStore.getState().dateRange).toBe('all')
      expect(useFilterStore.getState().filtersTouched).toBe(false)

      // Reset
      resetFilters()

      // Should remain at initial state
      expect(useFilterStore.getState().channelIds).toEqual([])
      expect(useFilterStore.getState().collectionIds).toEqual([])
      expect(useFilterStore.getState().mediaTypes).toEqual([])
      expect(useFilterStore.getState().dateRange).toBe('all')
      expect(useFilterStore.getState().filtersTouched).toBe(false)
    })

    it('should reset only some filters when only some are set', () => {
      const { setChannelIds, setDateRange, resetFilters } = useFilterStore.getState()

      // Set only some filters
      setChannelIds(['channel-a', 'channel-b'])
      setDateRange('7d')

      expect(useFilterStore.getState().channelIds).toEqual(['channel-a', 'channel-b'])
      expect(useFilterStore.getState().dateRange).toBe('7d')

      // Reset all
      resetFilters()

      // All should be reset
      expect(useFilterStore.getState().channelIds).toEqual([])
      expect(useFilterStore.getState().collectionIds).toEqual([])
      expect(useFilterStore.getState().mediaTypes).toEqual([])
      expect(useFilterStore.getState().dateRange).toBe('all')
      expect(useFilterStore.getState().filtersTouched).toBe(false)
    })

    it('should allow setting filters again after reset', () => {
      const { setChannelIds, setDateRange, resetFilters } = useFilterStore.getState()

      // Set filters
      setChannelIds(['channel-1'])
      setDateRange('30d')

      // Reset
      resetFilters()

      // Set new filters
      setChannelIds(['channel-2', 'channel-3'])
      setDateRange('24h')

      expect(useFilterStore.getState().channelIds).toEqual(['channel-2', 'channel-3'])
      expect(useFilterStore.getState().dateRange).toBe('24h')
    })
  })

  describe('state independence', () => {
    it('should not affect other state when setting channelIds', () => {
      const { setChannelIds, setCollectionIds, setMediaTypes, setDateRange, setFiltersTouched } =
        useFilterStore.getState()

      // Set some initial state
      setCollectionIds(['collection-1'])
      setMediaTypes(['video'])
      setDateRange('7d')
      setFiltersTouched(true)

      const beforeChange = {
        collectionIds: useFilterStore.getState().collectionIds,
        mediaTypes: useFilterStore.getState().mediaTypes,
        dateRange: useFilterStore.getState().dateRange,
        filtersTouched: useFilterStore.getState().filtersTouched,
      }

      // Change channelIds
      setChannelIds(['channel-new'])

      // Other state should be unchanged
      expect(useFilterStore.getState().collectionIds).toEqual(beforeChange.collectionIds)
      expect(useFilterStore.getState().mediaTypes).toEqual(beforeChange.mediaTypes)
      expect(useFilterStore.getState().dateRange).toBe(beforeChange.dateRange)
      expect(useFilterStore.getState().filtersTouched).toBe(beforeChange.filtersTouched)
    })

    it('should not affect other state when setting collectionIds', () => {
      const { setChannelIds, setCollectionIds, setMediaTypes, setDateRange } =
        useFilterStore.getState()

      // Set some initial state
      setChannelIds(['channel-1'])
      setMediaTypes(['image'])
      setDateRange('24h')

      const beforeChange = {
        channelIds: useFilterStore.getState().channelIds,
        mediaTypes: useFilterStore.getState().mediaTypes,
        dateRange: useFilterStore.getState().dateRange,
      }

      // Change collectionIds
      setCollectionIds(['collection-new'])

      // Other state should be unchanged
      expect(useFilterStore.getState().channelIds).toEqual(beforeChange.channelIds)
      expect(useFilterStore.getState().mediaTypes).toEqual(beforeChange.mediaTypes)
      expect(useFilterStore.getState().dateRange).toBe(beforeChange.dateRange)
    })

    it('should not affect other state when setting mediaTypes', () => {
      const { setChannelIds, setCollectionIds, setMediaTypes, setDateRange } =
        useFilterStore.getState()

      // Set some initial state
      setChannelIds(['channel-1'])
      setCollectionIds(['collection-1'])
      setDateRange('30d')

      const beforeChange = {
        channelIds: useFilterStore.getState().channelIds,
        collectionIds: useFilterStore.getState().collectionIds,
        dateRange: useFilterStore.getState().dateRange,
      }

      // Change mediaTypes
      setMediaTypes(['audio', 'text'])

      // Other state should be unchanged
      expect(useFilterStore.getState().channelIds).toEqual(beforeChange.channelIds)
      expect(useFilterStore.getState().collectionIds).toEqual(beforeChange.collectionIds)
      expect(useFilterStore.getState().dateRange).toBe(beforeChange.dateRange)
    })

    it('should not affect other state when setting dateRange', () => {
      const { setChannelIds, setCollectionIds, setMediaTypes, setDateRange } =
        useFilterStore.getState()

      // Set some initial state
      setChannelIds(['channel-1'])
      setCollectionIds(['collection-1'])
      setMediaTypes(['video'])

      const beforeChange = {
        channelIds: useFilterStore.getState().channelIds,
        collectionIds: useFilterStore.getState().collectionIds,
        mediaTypes: useFilterStore.getState().mediaTypes,
      }

      // Change dateRange
      setDateRange('7d')

      // Other state should be unchanged
      expect(useFilterStore.getState().channelIds).toEqual(beforeChange.channelIds)
      expect(useFilterStore.getState().collectionIds).toEqual(beforeChange.collectionIds)
      expect(useFilterStore.getState().mediaTypes).toEqual(beforeChange.mediaTypes)
    })

    it('should not affect other state when setting filtersTouched', () => {
      const { setChannelIds, setCollectionIds, setMediaTypes, setDateRange, setFiltersTouched } =
        useFilterStore.getState()

      // Set some initial state
      setChannelIds(['channel-1'])
      setCollectionIds(['collection-1'])
      setMediaTypes(['image'])
      setDateRange('24h')

      const beforeChange = {
        channelIds: useFilterStore.getState().channelIds,
        collectionIds: useFilterStore.getState().collectionIds,
        mediaTypes: useFilterStore.getState().mediaTypes,
        dateRange: useFilterStore.getState().dateRange,
      }

      // Change filtersTouched
      setFiltersTouched(true)

      // Other state should be unchanged
      expect(useFilterStore.getState().channelIds).toEqual(beforeChange.channelIds)
      expect(useFilterStore.getState().collectionIds).toEqual(beforeChange.collectionIds)
      expect(useFilterStore.getState().mediaTypes).toEqual(beforeChange.mediaTypes)
      expect(useFilterStore.getState().dateRange).toBe(beforeChange.dateRange)
    })
  })
})
