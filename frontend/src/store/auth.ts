import { create } from 'zustand'

type User = {
  id: number
  username: string
  email: string
  full_name?: string
  is_active: boolean
}

interface AuthStore {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  setAuth: (user: User, token: string) => void
  logout: () => void
  loadFromStorage: () => void
  setTokenOnly: (token: string) => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  setAuth: (user, token) => {
    localStorage.setItem('access_token', token)
    localStorage.setItem('user', JSON.stringify(user))
    set({ user, token, isAuthenticated: true })
  },
  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    set({ user: null, token: null, isAuthenticated: false })
  },
  loadFromStorage: () => {
    const token = localStorage.getItem('access_token')
    const userStr = localStorage.getItem('user')
    if (token && userStr) {
      const user = JSON.parse(userStr)
      set({ user, token, isAuthenticated: true })
    }
  },
  setTokenOnly: (token) => {
    localStorage.setItem('access_token', token)
    set((state) => ({ token, isAuthenticated: Boolean(state.user || token) }))
  },
}))
