/**
 * App.jsx — Root Layout, Auth Gate & Page Router
 *
 * On mount, pings /api/v1/health to determine the auth_mode:
 *   - "open" or "api_key" → renders app directly (no login screen)
 *   - "jwt"               → shows Login screen first; once logged in renders app
 *
 * Active pages:
 *   - 'dashboard'            → Dashboard  (task hazard analysis + safety records)
 *   - 'analytics'            → Analytics  (charts & trends)
 *   - 'assessments'          → RiskAssessments (AI assessment history + log safety records)
 *   - 'ppe-guide'            → PPEGuide   (PPE catalog, hazard reference, AUL materials)
 *   - 'ai-feedback'          → AIFeedbackPanel
 *   - 'pollution-prevention' → PollutionPrevention
 */

import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Dashboard from './components/Dashboard'
import Analytics from './components/Analytics'
import AIFeedbackPanel from './components/AIFeedbackPanel'
import PollutionPrevention from './components/PollutionPrevention'
import RiskAssessments from './components/RiskAssessments'
import PPEGuide from './components/PPEGuide'
import Login from './components/Login'
import { getStoredUser, clearSession } from './api/auth'
import { checkHealth } from './api/hazmat'
import './App.css'

function App() {
  const [activePage, setActivePage] = useState('dashboard')
  const [isAdminUnlocked, setIsAdminUnlocked] = useState(false)
  const [authMode, setAuthMode] = useState(null)   // null = loading, "open"/"api_key"/"jwt"
  const [currentUser, setCurrentUser] = useState(getStoredUser)

  // Determine auth mode from backend on mount
  useEffect(() => {
    checkHealth()
      .then((data) => setAuthMode(data.auth_mode || 'open'))
      .catch(() => setAuthMode('open'))  // if health check fails, let app render
  }, [])

  const handleLogin = (userInfo) => {
    setCurrentUser(userInfo)
  }

  const handleLogout = () => {
    clearSession()
    setCurrentUser(null)
  }

  // Show nothing while detecting auth mode
  if (authMode === null) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: '#12141a', color: '#6b7280', fontFamily: 'IBM Plex Mono, monospace', fontSize: '0.82rem' }}>
        Connecting to API…
      </div>
    )
  }

  // Show login if JWT is required and no valid session exists
  if (authMode === 'jwt' && !currentUser) {
    return <Login onLogin={handleLogin} />
  }

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':
        return <Dashboard />
      case 'assessments':
        return <RiskAssessments onNavigate={setActivePage} />
      case 'ppe-guide':
        return <PPEGuide />
      case 'analytics':
        return <Analytics />
      case 'ai-feedback':
        return <AIFeedbackPanel />
      case 'pollution-prevention':
        return <PollutionPrevention />
      default:
        return <Dashboard />
    }
  }

  return (
    <>
      {/* Skip navigation link for keyboard/screen reader users */}
      <a href="#main-content" className="skip-link">Skip to main content</a>

      <div className="app-layout">
        <Sidebar activePage={activePage} onNavigate={setActivePage} isAdminUnlocked={isAdminUnlocked} />
        <div className="app-main">
          <Header
            currentUser={currentUser}
            onLogout={authMode === 'jwt' ? handleLogout : null}
            isAdminUnlocked={isAdminUnlocked}
            onAdminUnlock={() => setIsAdminUnlocked(true)}
          />
          <main className="app-content" id="main-content" tabIndex={-1}>
            {renderPage()}
          </main>
        </div>
      </div>
    </>
  )
}

export default App
