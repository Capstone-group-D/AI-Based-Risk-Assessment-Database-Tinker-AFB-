/**
 * client.js — Axios Base Client
 *
 * Shared HTTP client for all backend API calls.
 *
 * Base URL:
 *   - Development: leave VITE_API_BASE_URL unset. Vite's dev proxy (vite.config.js)
 *     forwards all /api/* requests to http://localhost:8000 — no CORS issues.
 *   - Production:  set VITE_API_BASE_URL=https://api.yourdomain.com in your .env file.
 *
 * API Key:
 *   - Set VITE_API_KEY in your .env file to match the backend API_KEY env var.
 *   - When VITE_API_KEY is empty (default), the header is not sent (dev mode).
 */

import axios from 'axios'

const API_KEY = import.meta.env.VITE_API_KEY

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
  },
})

export default client
