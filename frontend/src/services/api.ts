import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { useUserStore } from '@/stores/user'

// API基础配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

// 创建axios实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    const userStore = useUserStore()
    const token = userStore.token
    
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error) => {
    const userStore = useUserStore()
    
    if (error.response?.status === 401) {
      userStore.logout()
      window.location.href = '/login'
    }
    
    return Promise.reject(error)
  }
)

// API方法封装
export const api = {
  // 认证相关
  auth: {
    register: (userData: any) => apiClient.post('/auth/register', userData),
    login: (credentials: any) => apiClient.post('/auth/login', credentials),
    getProfile: () => apiClient.get('/auth/me'),
    updateProfile: (data: any) => apiClient.put('/auth/me', data),
    changePassword: (data: any) => apiClient.post('/auth/change-password', data),
  },

  // 搜索相关
  search: {
    papers: (searchData: any) => apiClient.post('/search/', searchData),
    suggestions: (query: string) => apiClient.get(`/search/suggestions?q=${query}`),
    filters: () => apiClient.get('/search/filters'),
    trending: () => apiClient.get('/search/trending'),
    history: () => apiClient.get('/search/history'),
  },

  // 论文相关
  papers: {
    list: (params: any) => apiClient.get('/papers/', { params }),
    get: (id: string) => apiClient.get(`/papers/${id}`),
    truthValue: (id: string) => apiClient.get(`/papers/${id}/truth-value`),
    references: (id: string) => apiClient.get(`/papers/${id}/references`),
    citations: (id: string) => apiClient.get(`/papers/${id}/citations`),
    graph: (id: string, params?: any) => apiClient.get(`/papers/${id}/graph`, { params }),
    similar: (id: string) => apiClient.get(`/papers/${id}/similar`),
    bookmark: (id: string) => apiClient.post(`/papers/${id}/bookmark`),
    unbookmark: (id: string) => apiClient.delete(`/papers/${id}/bookmark`),
    compare: (id1: string, id2: string) => apiClient.post('/papers/compare', { paper_id1: id1, paper_id2: id2 }),
  },

  // 作者相关
  authors: {
    list: (params: any) => apiClient.get('/authors/', { params }),
    get: (id: string) => apiClient.get(`/authors/${id}`),
    papers: (id: string, params?: any) => apiClient.get(`/authors/${id}/papers`, { params }),
    statistics: (id: string) => apiClient.get(`/authors/${id}/statistics`),
    timeline: (id: string) => apiClient.get(`/authors/${id}/career-timeline`),
    evolution: (id: string) => apiClient.get(`/authors/${id}/research-evolution`),
    network: (id: string) => apiClient.get(`/authors/${id}/collaboration-network`),
    graph: (id: string, params?: any) => apiClient.get(`/authors/${id}/graph`, { params }),
    follow: (id: string) => apiClient.post(`/authors/${id}/follow`),
    unfollow: (id: string) => apiClient.delete(`/authors/${id}/follow`),
  },

  // 工作台相关
  workspace: {
    dashboard: () => apiClient.get('/workspace/dashboard'),
    bookmarks: (params?: any) => apiClient.get('/workspace/bookmarks', { params }),
    folders: () => apiClient.get('/workspace/folders'),
    createFolder: (data: any) => apiClient.post('/workspace/folders', data),
    updateFolder: (id: string, data: any) => apiClient.put(`/workspace/folders/${id}`, data),
    deleteFolder: (id: string) => apiClient.delete(`/workspace/folders/${id}`),
    addToFolder: (folderId: string, paperId: string) => 
      apiClient.post(`/workspace/folders/${folderId}/papers/${paperId}`),
    removeFromFolder: (folderId: string, paperId: string) => 
      apiClient.delete(`/workspace/folders/${folderId}/papers/${paperId}`),
    followedAuthors: () => apiClient.get('/workspace/followed-authors'),
    readingHistory: (params?: any) => apiClient.get('/workspace/reading-history', { params }),
    addReading: (paperId: string) => apiClient.post(`/workspace/reading-history/${paperId}`),
    recommendations: (params?: any) => apiClient.get('/workspace/recommendations', { params }),
    stats: () => apiClient.get('/workspace/stats'),
  },

  // AI助手相关
  ai: {
    summarize: (paperId: string) => apiClient.post(`/ai-assistant/summarize/${paperId}`),
    compare: (paperIds: string[]) => apiClient.post('/ai-assistant/compare', { paper_ids: paperIds }),
    trends: (field: string) => apiClient.post('/ai-assistant/research-trends', { research_field: field }),
    explain: (paperId: string, aspect: string) => 
      apiClient.post(`/ai-assistant/explain-paper/${paperId}?aspect=${aspect}`),
    recommend: (paperId: string, limit?: number) => 
      apiClient.post(`/ai-assistant/recommend-readings/${paperId}`, { limit }),
    ideas: (paperId: string) => apiClient.post(`/ai-assistant/generate-research-ideas/${paperId}`),
    capabilities: () => apiClient.get('/ai-assistant/capabilities'),
  },
}

export default apiClient

