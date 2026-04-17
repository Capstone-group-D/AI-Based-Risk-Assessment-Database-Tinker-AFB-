/**
 * Sidebar.jsx — Left Navigation Menu
 *
 * Renders the fixed left sidebar with:
 *   - Brand section (Tinker AFB logo and title)
 *   - Navigation links (Dashboard, Risk Assessments, PPE Guide)
 *   - Footer with sprint/version info
 *
 * Props:
 *   - activePage (string): The currently active page ID (e.g. 'dashboard').
 *     Used to highlight the active nav link with the .active class.
 *   - onNavigate (function): Callback fired when a nav link is clicked.
 *     Receives the page ID (e.g. 'assessments') so App.jsx can switch pages.
 *
 * To add a new page:
 *   1. Add an entry to the NAV_ITEMS array below with a unique id
 *   2. Add a matching case in App.jsx's renderPage() function
 */

import './Sidebar.css'

// Each nav item needs an id (used for routing), a display label, and an icon
const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: '⬡' },
  { id: 'analytics', label: 'Analytics', icon: '◈' },
  { id: 'assessments', label: 'Risk Assessments', icon: '⬢' },
  { id: 'ppe-guide', label: 'PPE Guide', icon: '⬣' },
]

export default function Sidebar({ activePage, onNavigate }) {
  return (
    <aside className="sidebar">
      {/* Brand section — project identity at the top of the sidebar */}
      <div className="sidebar-brand">
        <span className="sidebar-logo">◆</span>
        <span className="sidebar-title">TINKER AFB</span>
        <span className="sidebar-subtitle">Risk Assessment</span>
      </div>

      {/* Navigation links — loops over NAV_ITEMS and highlights the active page */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            className={`sidebar-link ${activePage === item.id ? 'active' : ''}`}
            onClick={() => onNavigate(item.id)}
          >
            <span className="sidebar-icon">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      {/* Footer — displays current sprint and version number */}
      <div className="sidebar-footer">
        <span className="sidebar-version">Sprint 2 — v0.2.0</span>
      </div>
    </aside>
  )
}
