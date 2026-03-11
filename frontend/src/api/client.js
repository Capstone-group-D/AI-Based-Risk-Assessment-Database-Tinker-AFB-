/**
 * client.js — Axios Base Client
 *
 * Shared HTTP client for all backend API calls.
 *
 * Base URL:
 *   - Development: leave VITE_API_BASE_URL unset. Vite's dev proxy (vite.config.js)
 *     forwards all /api/* requests to http://localhost:8000 — no CORS issues.
 *   - Production:  set VITE_API_BASE_URL=https://api.yourdomain.com in your .env file.
 */

import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

export default client
