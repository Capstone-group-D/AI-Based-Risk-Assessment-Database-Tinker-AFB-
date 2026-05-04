/**
 * Header.jsx — Top Header Bar
 *
 * Pings GET /api/v1/health on mount to determine backend connectivity,
 * then displays a live status indicator using the CSS classes already
 * defined in Header.css:
 *   .connected  → green  "System Online"
 *   .pending    → yellow "Connecting…"
 *   .offline    → red    "API Offline"
 *
 * Also renders an "Admin Login" button that opens a password modal.
 * On success, calls onAdminUnlock() to unlock the admin panel in App.jsx.
 *
 * Props:
 *   - isAdminUnlocked (bool): Hides the login button once unlocked.
 *   - onAdminUnlock (function): Called when the correct password is verified.
 */

import { useState, useEffect } from 'react'
import { checkHealth, adminLogin } from '../api/hazmat'
import './Header.css'

const STATUS_LABEL = {
  pending:   'Connecting…',
  connected: 'System Online',
  offline:   'API Offline',
}

export default function Header({ isAdminUnlocked, onAdminUnlock }) {
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
      onAdminUnlock()
      closeModal()
    } catch {
      setLoginError('Invalid password. Please try again.')
    } finally {
      setLoginLoading(false)
    }
  }

  return (
    <>
      <header className="header">
        {/* Left side — project title and subtitle */}
        <div className="header-left">
          <h1 className="header-title">PPE Recommendation Engine</h1>
          <span className="header-desc">AI-Based Risk Assessment Database — Tinker AFB</span>
        </div>

        {/* Right side — status indicator and admin login button */}
        <div className="header-right">
          {!isAdminUnlocked && (
            <button className="admin-login-btn" onClick={openModal}>
              Admin Login
            </button>
          )}
          <span className={`header-status ${status}`}>
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
