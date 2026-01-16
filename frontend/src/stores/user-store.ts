import { create } from 'zustand'

interface User {
  id: string
  name: string
  role: string
}

interface UserState {
  user: User | null
  setUser: (user: User | null) => void
}

export const useUserStore = create<UserState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}))
