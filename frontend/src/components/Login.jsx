/**
 * Login.jsx — Login screen shown when JWT_SECRET_KEY is configured on the backend
 *
 * Detects whether JWT is active by checking the /api/v1/health `auth_mode` field.
 * When auth_mode is "open" or "api_key", this screen is skipped entirely and the
 * app renders normally without credentials.
 *
 * Default credentials (development):
 *   admin / admin123   (supervisor)
 *   analyst / analyst123 (analyst)
 *   viewer / viewer123   (viewer)
 */

import { useState } from 'react'
import { login } from '../api/auth'
import './Login.css'

const ROLE_BADGES = {
  supervisor: { label: 'Supervisor', color: '#f97316' },
  analyst:    { label: 'Analyst',    color: '#60a5fa' },
  viewer:     { label: 'Viewer',     color: '#34d399' },
}

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const user = await login(username, password)
      onLogin(user)
    } catch (err) {
      const msg = err.response?.data?.detail
        || (err.response?.status === 401 ? 'Incorrect username or password.' : 'Could not reach the API.')
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-backdrop">
      <div className="login-card">
        <div className="login-brand">
          <span className="login-logo">◆</span>
          <div>
            <div className="login-title">TINKER AFB</div>
            <div className="login-subtitle">Risk Assessment System</div>
          </div>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="login-field">
            <label className="login-label" htmlFor="login-username">Username</label>
            <input
              id="login-username"
              type="text"
              className="login-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              autoFocus
              required
            />
          </div>

          <div className="login-field">
            <label className="login-label" htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              className="login-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>

          {error && <div className="login-error" role="alert">{error}</div>}

          <button type="submit" className="login-btn" disabled={loading || !username || !password}>
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        <div className="login-roles-info">
          <p className="login-roles-title">Role Permissions</p>
          <div className="login-roles-list">
            {Object.entries(ROLE_BADGES).map(([role, meta]) => (
              <div key={role} className="login-role-row">
                <span className="role-dot" style={{ background: meta.color }} />
                <span className="role-name" style={{ color: meta.color }}>{meta.label}</span>
                <span className="role-desc">
                  {role === 'supervisor' && 'Full access — log records, run analysis, manage data'}
                  {role === 'analyst' && 'Run AI analysis, submit feedback, view all data'}
                  {role === 'viewer' && 'Read-only access to records and reference data'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
