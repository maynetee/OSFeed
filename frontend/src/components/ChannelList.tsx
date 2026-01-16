import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { channelsApi, collectionsApi } from '../api/client'

export default function ChannelList() {
  const [newChannelUsername, setNewChannelUsername] = useState('')
  const [error, setError] = useState('')
  const [newCollectionName, setNewCollectionName] = useState('')
  const [newCollectionDescription, setNewCollectionDescription] = useState('')
  const [newCollectionChannelIds, setNewCollectionChannelIds] = useState<string[]>([])
  const [editingCollectionId, setEditingCollectionId] = useState<string | null>(null)
  const [editingChannelIds, setEditingChannelIds] = useState<string[]>([])
  const queryClient = useQueryClient()

  const { data: channels, isLoading } = useQuery({
    queryKey: ['channels'],
    queryFn: () => channelsApi.list().then((res) => res.data),
  })

  const { data: collections, isLoading: collectionsLoading } = useQuery({
    queryKey: ['collections'],
    queryFn: () => collectionsApi.list().then((res) => res.data),
  })

  const addChannelMutation = useMutation({
    mutationFn: (username: string) => channelsApi.add(username),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] })
      setNewChannelUsername('')
      setError('')
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to add channel')
    },
  })

  const deleteChannelMutation = useMutation({
    mutationFn: (id: string) => channelsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] })
    },
  })

  const createCollectionMutation = useMutation({
    mutationFn: (payload: { name: string; description?: string; channel_ids?: string[] }) =>
      collectionsApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] })
      setNewCollectionName('')
      setNewCollectionDescription('')
      setNewCollectionChannelIds([])
    },
  })

  const updateCollectionMutation = useMutation({
    mutationFn: (payload: { id: string; channel_ids: string[] }) =>
      collectionsApi.update(payload.id, { channel_ids: payload.channel_ids }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] })
      setEditingCollectionId(null)
      setEditingChannelIds([])
    },
  })

  const deleteCollectionMutation = useMutation({
    mutationFn: (id: string) => collectionsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
  })

  const handleAddChannel = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newChannelUsername.trim()) {
      setError('Please enter a channel username')
      return
    }
    addChannelMutation.mutate(newChannelUsername.trim())
  }

  const handleCreateCollection = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newCollectionName.trim()) {
      return
    }
    createCollectionMutation.mutate({
      name: newCollectionName.trim(),
      description: newCollectionDescription.trim() || undefined,
      channel_ids: newCollectionChannelIds,
    })
  }

  const toggleChannelSelection = (
    channelId: string,
    selected: string[],
    setSelected: (value: string[]) => void
  ) => {
    if (selected.includes(channelId)) {
      setSelected(selected.filter((id) => id !== channelId))
    } else {
      setSelected([...selected, channelId])
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">Channels</h2>
      </div>

      {/* Add Channel Form */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Channel</h3>
        <form onSubmit={handleAddChannel} className="flex items-start space-x-4">
          <div className="flex-1">
            <input
              type="text"
              value={newChannelUsername}
              onChange={(e) => setNewChannelUsername(e.target.value)}
              placeholder="@channelname or channel username"
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
            {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
          </div>
          <button
            type="submit"
            disabled={addChannelMutation.isPending}
            className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {addChannelMutation.isPending ? 'Adding...' : 'Add Channel'}
          </button>
        </form>
      </div>

      {/* Collections */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">Collections</h3>
        </div>

        <form onSubmit={handleCreateCollection} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              type="text"
              value={newCollectionName}
              onChange={(e) => setNewCollectionName(e.target.value)}
              placeholder="Collection name"
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
            <input
              type="text"
              value={newCollectionDescription}
              onChange={(e) => setNewCollectionDescription(e.target.value)}
              placeholder="Short description (optional)"
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="flex flex-wrap gap-3">
            {channels?.map((channel) => (
              <label key={channel.id} className="flex items-center space-x-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={newCollectionChannelIds.includes(channel.id)}
                  onChange={() =>
                    toggleChannelSelection(
                      channel.id,
                      newCollectionChannelIds,
                      setNewCollectionChannelIds
                    )
                  }
                />
                <span>{channel.title}</span>
              </label>
            ))}
          </div>

          <button
            type="submit"
            disabled={createCollectionMutation.isPending}
            className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            {createCollectionMutation.isPending ? 'Creating...' : 'Create Collection'}
          </button>
        </form>

        <div className="mt-6 space-y-4">
          {collectionsLoading ? (
            <div className="text-gray-500">Loading collections...</div>
          ) : collections && collections.length > 0 ? (
            collections.map((collection) => (
              <div key={collection.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="text-lg font-medium text-gray-900">{collection.name}</h4>
                    {collection.description && (
                      <p className="text-sm text-gray-600 mt-1">{collection.description}</p>
                    )}
                    <p className="text-xs text-gray-500 mt-2">
                      {collection.channel_ids.length} channel(s)
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => {
                        setEditingCollectionId(collection.id)
                        setEditingChannelIds(collection.channel_ids)
                      }}
                      className="px-3 py-1 border border-gray-300 text-sm rounded-md hover:bg-gray-50"
                    >
                      Edit Channels
                    </button>
                    <button
                      onClick={() => deleteCollectionMutation.mutate(collection.id)}
                      className="px-3 py-1 border border-red-300 text-sm rounded-md text-red-700 hover:bg-red-50"
                    >
                      Delete
                    </button>
                  </div>
                </div>

                {editingCollectionId === collection.id && (
                  <div className="mt-4 space-y-3">
                    <div className="flex flex-wrap gap-3">
                      {channels?.map((channel) => (
                        <label key={channel.id} className="flex items-center space-x-2 text-sm text-gray-700">
                          <input
                            type="checkbox"
                            checked={editingChannelIds.includes(channel.id)}
                            onChange={() =>
                              toggleChannelSelection(
                                channel.id,
                                editingChannelIds,
                                setEditingChannelIds
                              )
                            }
                          />
                          <span>{channel.title}</span>
                        </label>
                      ))}
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() =>
                          updateCollectionMutation.mutate({
                            id: collection.id,
                            channel_ids: editingChannelIds,
                          })
                        }
                        className="px-3 py-1 border border-transparent text-sm rounded-md text-white bg-blue-600 hover:bg-blue-700"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => {
                          setEditingCollectionId(null)
                          setEditingChannelIds([])
                        }}
                        className="px-3 py-1 border border-gray-300 text-sm rounded-md hover:bg-gray-50"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="text-gray-500">No collections yet.</div>
          )}
        </div>
      </div>

      {/* Channels List */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Your Channels</h3>

          {isLoading ? (
            <div className="text-gray-500">Loading channels...</div>
          ) : channels && channels.length > 0 ? (
            <div className="space-y-4">
              {channels.map((channel) => (
                <div
                  key={channel.id}
                  className="flex items-start justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <Link
                        to={`/channels/${channel.id}`}
                        className="text-lg font-medium text-blue-600 hover:text-blue-800 hover:underline"
                      >
                        {channel.title}
                      </Link>
                      <span className="text-sm text-gray-500">@{channel.username}</span>
                    </div>
                    {channel.description && (
                      <p className="mt-1 text-sm text-gray-600">{channel.description}</p>
                    )}
                    <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500">
                      <span>{channel.subscriber_count.toLocaleString()} subscribers</span>
                      {channel.detected_language && <span>Language: {channel.detected_language}</span>}
                      {channel.last_fetched_at && (
                        <span>
                          Last fetched: {new Date(channel.last_fetched_at).toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => deleteChannelMutation.mutate(channel.id)}
                    disabled={deleteChannelMutation.isPending}
                    className="ml-4 px-3 py-1 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-500">
                No channels yet. Add your first channel above to get started.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
