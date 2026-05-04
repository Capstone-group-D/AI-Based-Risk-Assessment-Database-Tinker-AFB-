/**
 * App.jsx — Root Layout & Page Router
 *
 * This is the top-level component that defines the app's visual structure:
 *   ┌──────────┬────────────────────────────────┐
 *   │          │  Header                        │
 *   │ Sidebar  ├────────────────────────────────┤
 *   │          │  Main Content (active page)    │
 *   │          │                                │
 *   └──────────┴────────────────────────────────┘
 *
 * Page routing is handled via the `activePage` state variable.
 * The Sidebar passes the selected page ID back up through onNavigate,
 * and renderPage() switches which component is displayed.
 *
 * Currently active pages:
 *   - 'dashboard'   → Dashboard component (task hazard analysis form)
 *   - 'analytics'   → Analytics component (Sprint 3)
 *   - 'assessments' → Placeholder (Sprint 2)
 *   - 'ppe-guide'   → Placeholder (Sprint 2)
 */

import { useState } from 'react'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Dashboard from './components/Dashboard'
import Analytics from './components/Analytics'
import AIFeedbackPanel from './components/AIFeedbackPanel'
import PollutionPrevention from './components/PollutionPrevention'
import './App.css'

function App() {
  // Tracks which page is currently displayed — matches the 'id' values in Sidebar's NAV_ITEMS
  const [activePage, setActivePage] = useState('dashboard')
  // Unlocked by entering the correct admin password in the Header modal
  const [isAdminUnlocked, setIsAdminUnlocked] = useState(false)

  /**
   * Renders the correct page component based on activePage state.
   * Add new pages here as they are built in future sprints.
   */
  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':
        return <Dashboard />
      case 'assessments':
        return (
          <div className="placeholder-page">
            <h2>Risk Assessments</h2>
            <p>Full risk assessment management — coming in Sprint 3.</p>
          </div>
        )
      case 'ppe-guide':
        return (
          <div className="placeholder-page">
            <h2>PPE Guide</h2>
            <p>Complete PPE reference catalog — coming in Sprint 3.</p>
          </div>
        )
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
    <div className="app-layout">
      {/* Left sidebar — navigation menu, passes activePage down and receives page changes back */}
      <Sidebar activePage={activePage} onNavigate={setActivePage} isAdminUnlocked={isAdminUnlocked} />

      {/* Right side — header bar on top, active page content below */}
      <div className="app-main">
        <Header isAdminUnlocked={isAdminUnlocked} onAdminUnlock={() => setIsAdminUnlocked(true)} />
        <main className="app-content">
          {renderPage()}
        </main>
      </div>
    </div>
  )
}

export default App
