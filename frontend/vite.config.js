import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// In Docker the API is another container, so the proxy target is injected.
// Outside Docker this is unset and it stays localhost, as before.
const apiTarget = process.env.VITE_API_PROXY || 'http://localhost:8000'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    host: true,
    proxy: { '/api': apiTarget },
    // polling keeps hot reload working over a bind mount from macOS
    watch: { usePolling: true },
  },
})
