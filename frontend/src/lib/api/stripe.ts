import { api } from './axios-instance'

export const stripeApi = {
  createCheckoutSession: (plan: string, billing: string) =>
    api.post<{ url: string }>('/api/stripe/create-checkout-session', { plan, billing }),

  createPortalSession: () =>
    api.post<{ url: string }>('/api/stripe/customer-portal'),
}
