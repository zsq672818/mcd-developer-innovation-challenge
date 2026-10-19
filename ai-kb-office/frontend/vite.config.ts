import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 开发期将 /api 代理到后端，避免跨域；生产环境由网关统一转发
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
