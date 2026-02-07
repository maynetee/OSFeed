declare global {
  interface Window {
    plausible?: (
      eventName: string,
      options?: { props?: Record<string, string | number | boolean> },
    ) => void
  }
}

export function trackEvent(eventName: string, props?: Record<string, string | number | boolean>) {
  if (typeof window !== 'undefined' && window.plausible) {
    window.plausible(eventName, { props })
  }
}
