import { create } from 'zustand'

export interface Model {
  id: number
  model_id: string
  name: string
  description?: string
  author_id: number
  downloads: number
  created_at: string
}

interface ModelsStore {
  models: Model[]
  currentModel: Model | null
  loading: boolean
  error: string | null
  setModels: (models: Model[]) => void
  setCurrentModel: (model: Model) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useModelsStore = create<ModelsStore>((set) => ({
  models: [],
  currentModel: null,
  loading: false,
  error: null,
  setModels: (models) => set({ models }),
  setCurrentModel: (model) => set({ currentModel: model }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}))
