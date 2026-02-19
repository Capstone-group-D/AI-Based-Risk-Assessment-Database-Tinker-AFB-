/**
 * Header.jsx — Top Header Bar
 *
 * Displays the project title and a backend connection status indicator.
 *
 * Currently shows a static "Awaiting Backend" status since the API
 * is not yet configured. When the backend is ready, this component
 * should be updated to ping the health endpoint (GET /api/v1/health)
 * and display "System Online" or "Offline" based on the response.
 *
 * Status CSS classes (defined in Header.css):
 *   - .connected → green (backend responding)
 *   - .pending   → yellow (awaiting backend)
 *   - .error     → red (API returned an error)
 *   - .offline   → red (backend unreachable)
 */

import './Header.css'

export default function Header() {
  return (
    <header className="header">
      {/* Left side — project title and subtitle */}
      <div className="header-left">
        <h1 className="header-title">PPE Recommendation Engine</h1>
        <span className="header-desc">AI-Based Risk Assessment Database — Tinker AFB</span>
      </div>

      {/* Right side — backend connection status indicator */}
      <div className="header-right">
        <span className="header-status pending">
          <span className="status-dot" />
          Awaiting Backend
        </span>
      </div>
    </header>
  )
}
