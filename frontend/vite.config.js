/**
 * Vite Configuration
 *
 * This is the build tool config for the React frontend.
 * - Runs the dev server on port 3000
 * - Proxies all /api requests to the FastAPI backend on port 8000,
 *   so the frontend can call endpoints like /api/v1/ppe/recommend
 *   without running into CORS issues during development.
 */

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // Forward any request starting with /api to the backend server
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
