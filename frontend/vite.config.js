import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',       // 👈 very important — listen on all IPs, not just localhost
    port: 5173,
    strictPort: true,
    allowedHosts: ['philatelical-ula-unsanctifying.ngrok-free.dev'], // 👈 allow external hosts like ngrok
    cors: true             // 👈 optional, but useful
  },
})
