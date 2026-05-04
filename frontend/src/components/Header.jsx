/**
 * Header.jsx — Top Header Bar
 *
 * Pings GET /api/v1/health on mount to show backend connectivity status.
 * When JWT auth is active, also displays the logged-in user's name, role badge,
 * and a Sign Out button.
 * Also renders an "Admin Login" button that opens a password modal when the
 * admin panel is not yet unlocked.
 *
 * Props:
 *   - currentUser (object|null): Logged-in JWT user ({ username, full_name, role }).
 *   - onLogout (function|null): Called when Sign Out is clicked (null = hide button).
 *   - isAdminUnlocked (bool): Hides the Admin Login button once unlocked.
 *   - onAdminUnlock (function): Called when the correct admin password is verified.
 */

import { useState, useEffect } from 'react'
import { checkHealth, adminLogin } from '../api/hazmat'
import './Header.css'

const STATUS_LABEL = {
  pending:   'Connecting…',
  connected: 'System Online',
  offline:   'API Offline',
}

const ROLE_COLOR = {
  supervisor: '#f97316',
  analyst:    '#60a5fa',
  viewer:     '#34d399',
}

export default function Header({ currentUser, onLogout, isAdminUnlocked, onAdminUnlock }) {
  const [status, setStatus] = useState('pending')
  const [showModal, setShowModal] = useState(false)
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const [loginLoading, setLoginLoading] = useState(false)

  useEffect(() => {
    checkHealth()
      .then(() => setStatus('connected'))
      .catch(() => setStatus('offline'))
  }, [])

  function openModal() {
    setPassword('')
    setLoginError('')
    setShowModal(true)
  }

  function closeModal() {
    setShowModal(false)
    setPassword('')
    setLoginError('')
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setLoginLoading(true)
    setLoginError('')
    try {
      await adminLogin(password)
      if (onAdminUnlock) onAdminUnlock()
      closeModal()
    } catch {
      setLoginError('Invalid password. Please try again.')
    } finally {
      setLoginLoading(false)
    }
  }

  return (
    <>
      <header className="header" role="banner">
        <div className="header-left">
          <h1 className="header-title">PPE Recommendation Engine</h1>
          <span className="header-desc">AI-Based Risk Assessment Database — Tinker AFB</span>
        </div>

        <div className="header-right">
          {/* JWT user info + sign out */}
          {currentUser && (
            <div className="header-user">
              <span
                className="header-role-badge"
                style={{ color: ROLE_COLOR[currentUser.role] ?? '#9ca3af' }}
              >
                {currentUser.role}
              </span>
              <span className="header-username">{currentUser.full_name || currentUser.username}</span>
              {onLogout && (
                <button className="header-logout-btn" onClick={onLogout} aria-label="Sign out">
                  Sign Out
                </button>
              )}
            </div>
          )}

          {/* Admin login button (hidden once unlocked) */}
          {!isAdminUnlocked && (
            <button className="admin-login-btn" onClick={openModal}>
              Admin Login
            </button>
          )}

          <span className={`header-status ${status}`} aria-live="polite">
            <span className="status-dot" />
            {STATUS_LABEL[status]}
          </span>
        </div>
      </header>

      {/* Admin Login Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2 className="modal-title">Admin Login</h2>
            <p className="modal-subtitle">Enter the master password to unlock the Admin Panel.</p>
            <form onSubmit={handleSubmit}>
              <input
                className="modal-input"
                type="password"
                placeholder="Master password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoFocus
              />
              {loginError && <p className="modal-error">{loginError}</p>}
              <div className="modal-actions">
                <button type="button" className="modal-cancel-btn" onClick={closeModal}>
                  Cancel
                </button>
                <button type="submit" className="modal-submit-btn" disabled={loginLoading || !password}>
                  {loginLoading ? 'Verifying…' : 'Unlock'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}
