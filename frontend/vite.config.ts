import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': resolve(__dirname, 'src') },
  },
  server: {
    // Lets the dev server be shared through a Cloudflare quick tunnel
    // (cloudflared tunnel --url http://localhost:5175) for previews
    allowedHosts: ['.trycloudflare.com'],
    proxy: {
      '/api': { target: process.env.API_TARGET || 'http://backend:8000', rewrite: (p) => p.replace(/^\/api/, '') },
    },
  },
})
