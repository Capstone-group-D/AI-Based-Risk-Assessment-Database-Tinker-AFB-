/**
 * Header.jsx — Top Header Bar
 *
 * Pings GET /api/v1/health on mount to determine backend connectivity,
 * then displays a live status indicator using the CSS classes already
 * defined in Header.css:
 *   .connected  → green  "System Online"
 *   .pending    → yellow "Connecting…"
 *   .offline    → red    "API Offline"
 */

import { useState, useEffect } from 'react'
import { checkHealth } from '../api/hazmat'
import './Header.css'

const STATUS_LABEL = {
  pending:   'Connecting…',
  connected: 'System Online',
  offline:   'API Offline',
}

export default function Header() {
  const [status, setStatus] = useState('pending')

  useEffect(() => {
    checkHealth()
      .then(() => setStatus('connected'))
      .catch(() => setStatus('offline'))
  }, [])

  return (
    <header className="header">
      {/* Left side — project title and subtitle */}
      <div className="header-left">
        <h1 className="header-title">PPE Recommendation Engine</h1>
        <span className="header-desc">AI-Based Risk Assessment Database — Tinker AFB</span>
      </div>

      {/* Right side — live backend connection status */}
      <div className="header-right">
        <span className={`header-status ${status}`}>
          <span className="status-dot" />
          {STATUS_LABEL[status]}
        </span>
      </div>
    </header>
  )
}
