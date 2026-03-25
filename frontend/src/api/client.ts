import axios from 'axios'
import { useAuthStore } from '../store/auth'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status
      const requestPath = error.config?.url || ''
      const isAuthRequest = requestPath.includes('/users/login') || requestPath.includes('/users/register')

      if (status === 401 && !isAuthRequest) {
        useAuthStore.getState().logout()
        return Promise.reject(new Error('Session expired. Please log in again.'))
      }

      const detail = error.response?.data?.detail
      if (typeof detail === 'string' && detail.trim()) {
        return Promise.reject(new Error(detail))
      }
    }
    return Promise.reject(error)
  },
)

export default api

export type ModelFile = {
  filename: string
  file_size?: number
  file_hash?: string
  created_at: string
}

export type HubModel = {
  id: number
  model_id: string
  name: string
  description?: string
  model_type?: string
  tags?: string
  downloads: number
  is_private?: boolean
  latest_revision?: string
  created_at: string
  updated_at?: string
}

export type Dataset = {
  id: number
  dataset_id: string
  name: string
  description?: string
  tags?: string
  downloads: number
  created_at: string
  updated_at?: string
  is_private?: boolean
}

export type DatasetFile = {
  filename: string
  file_size?: number
  created_at: string
}

export type DatasetPreview = {
  dataset_id: string
  filename: string
  format: string
  columns: string[]
  rows: Array<Record<string, unknown>>
  truncated: boolean
}

export type AuthUser = {
  id: number
  username: string
  email: string
  full_name?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export type LoginResponse = {
  access_token: string
  token_type: 'bearer'
}

export async function fetchModels(search?: string): Promise<HubModel[]> {
  const response = await api.get('/models', { params: { search } })
  return response.data.models
}

export async function fetchDatasets(search?: string): Promise<Dataset[]> {
  const response = await api.get('/datasets', { params: { search } })
  return response.data.datasets
}

export async function fetchModelFiles(modelId: string): Promise<ModelFile[]> {
  const response = await api.get('/models/files', { params: { model_id: modelId } })
  return response.data.files
}

export async function fetchModel(modelId: string): Promise<HubModel> {
  const response = await api.get(`/models/${encodeURIComponent(modelId).replace(/%2F/g, '/')}`)
  return response.data
}

export async function fetchDataset(datasetId: string): Promise<Dataset> {
  const response = await api.get(`/datasets/${encodeURIComponent(datasetId).replace(/%2F/g, '/')}`)
  return response.data
}

export async function createModel(input: {
  model_id: string
  name: string
  description?: string
  model_type?: string
  tags?: string
  is_private?: boolean
}): Promise<HubModel> {
  const response = await api.post('/models', input)
  return response.data
}

export async function createDataset(input: {
  dataset_id: string
  name: string
  description?: string
  tags?: string
  is_private?: boolean
}): Promise<Dataset> {
  const response = await api.post('/datasets', input)
  return response.data
}

export async function fetchDatasetFiles(datasetId: string): Promise<DatasetFile[]> {
  const response = await api.get('/datasets/files', { params: { dataset_id: datasetId } })
  return response.data.files
}

export async function uploadDatasetFile(datasetId: string, file: File): Promise<void> {
  const formData = new FormData()
  formData.append('file', file)
  await api.post('/datasets/files', formData, {
    params: { dataset_id: datasetId },
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export async function fetchDatasetPreview(datasetId: string, filename: string): Promise<DatasetPreview> {
  const response = await api.get('/datasets/preview', { params: { dataset_id: datasetId, filename } })
  return response.data
}

export async function uploadModelFile(modelId: string, file: File): Promise<void> {
  const formData = new FormData()
  formData.append('file', file)
  await api.post('/models/files', formData, {
    params: { model_id: modelId },
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export async function registerUser(input: {
  username: string
  email: string
  password: string
  full_name?: string
}): Promise<AuthUser> {
  const response = await api.post('/users/register', input)
  return response.data
}

export async function loginUser(input: { username: string; password: string }): Promise<LoginResponse> {
  const response = await api.post('/users/login', input)
  return response.data
}

export async function getUserProfile(username: string): Promise<AuthUser> {
  const response = await api.get(`/users/${username}`)
  return response.data
}
