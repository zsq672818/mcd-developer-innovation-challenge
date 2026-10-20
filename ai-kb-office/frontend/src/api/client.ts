import axios from 'axios'

// 开发期走 Vite 代理（/api），生产期可由 VITE_API_BASE 指定网关地址
const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '',
  timeout: 15000,
})

export interface HealthResp {
  status: string
  app: string
  env: string
}

export interface ReadyResp {
  status: string
  database: string
  database_url_scheme: string
}

export interface LlmHealthResp {
  ok: boolean
  detail: string
  provider: string
}

export const getHealth = () => client.get<HealthResp>('/api/health').then((r) => r.data)
export const getReady = () => client.get<ReadyResp>('/api/health/ready').then((r) => r.data)
export const getLlmHealth = () => client.get<LlmHealthResp>('/api/llm/health').then((r) => r.data)

export default client
