/**
 * auth.js — Authentication API helpers + token storage
 *
 * Tokens are stored in sessionStorage so they're scoped to the tab and
 * cleared when the browser is closed (safer than localStorage for government use).
 */

import client from './client'

const ACCESS_KEY = 'ras_access_token'
const REFRESH_KEY = 'ras_refresh_token'
const USER_KEY = 'ras_user'

// ── Storage helpers ────────────────────────────────────────────────────────

export function getStoredUser() {
  try { return JSON.parse(sessionStorage.getItem(USER_KEY)) } catch { return null }
}

export function getAccessToken() {
  return sessionStorage.getItem(ACCESS_KEY)
}

function storeSession(tokenResponse) {
  sessionStorage.setItem(ACCESS_KEY, tokenResponse.access_token)
  sessionStorage.setItem(REFRESH_KEY, tokenResponse.refresh_token)
  sessionStorage.setItem(USER_KEY, JSON.stringify({
    username: tokenResponse.username,
    full_name: tokenResponse.full_name,
    role: tokenResponse.role,
  }))
}

export function clearSession() {
  sessionStorage.removeItem(ACCESS_KEY)
  sessionStorage.removeItem(REFRESH_KEY)
  sessionStorage.removeItem(USER_KEY)
}

// ── Axios request interceptor — attaches Bearer token when present ─────────

client.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

// ── API calls ──────────────────────────────────────────────────────────────

/**
 * Login with username + password. Returns user info on success.
 * Throws Axios error on failure.
 */
export async function login(username, password) {
  // OAuth2 password flow expects application/x-www-form-urlencoded
  const params = new URLSearchParams()
  params.append('username', username)
  params.append('password', password)

  const response = await client.post('/api/v1/auth/login', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  storeSession(response.data)
  return response.data
}

export async function refreshTokens() {
  const refreshToken = sessionStorage.getItem(REFRESH_KEY)
  if (!refreshToken) throw new Error('No refresh token stored')
  const response = await client.post('/api/v1/auth/refresh', { refresh_token: refreshToken })
  storeSession(response.data)
  return response.data
}

export async function logout() {
  clearSession()
}

export async function fetchCurrentUser() {
  const response = await client.get('/api/v1/auth/me')
  return response.data
}
