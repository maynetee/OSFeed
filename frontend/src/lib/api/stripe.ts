import { api } from './axios-instance'

export const stripeApi = {
  createCheckoutSession: (plan: string, billing: string) =>
    api.post<{ url: string }>('/api/stripe/create-checkout-session', { plan, billing }),

  createPortalSession: () => api.post<{ url: string }>('/api/stripe/customer-portal'),

  getSubscriptionStatus: () =>
    api.get<{
      plan: string
      status: string
      period_end: string | null
      created_at: string | null
      is_refund_eligible: boolean
    }>('/api/subscription/status'),

  cancelSubscription: (immediate: boolean) =>
    api.post<{ status: string; period_end: string | null; message: string }>(
      '/api/subscription/cancel',
      { immediate },
    ),

  requestRefund: () =>
    api.post<{ status: string; amount: number | null; currency: string | null; message: string }>(
      '/api/subscription/refund',
    ),
}
