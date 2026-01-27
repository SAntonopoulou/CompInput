import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Allow requests from the ngrok domain
    // Replace 'lamentable-hue-attractingly.ngrok-free.dev' with your actual ngrok domain
    allowedHosts: ['kotobaseed.ngrok.app'],
  },
})
