import { api } from './axios-instance'
import type { Notification, NotificationListResponse } from './types'

export const notificationsApi = {
  list: (params?: { is_read?: boolean; limit?: number; offset?: number }) =>
    api.get<NotificationListResponse>('/api/notifications', { params }),

  unreadCount: () => api.get<{ count: number }>('/api/notifications/unread-count'),

  markRead: (id: string) => api.put<Notification>(`/api/notifications/${id}/read`),

  markAllRead: () => api.post<{ message: string }>('/api/notifications/mark-all-read'),

  delete: (id: string) => api.delete(`/api/notifications/${id}`),
}
