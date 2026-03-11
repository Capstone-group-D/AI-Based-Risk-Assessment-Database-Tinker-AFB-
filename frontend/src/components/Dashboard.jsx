/**
 * Dashboard.jsx — Main Task Hazard Analysis Page
 *
 * Sections:
 *   1. Task input form  — describe a task, pick severity, submit for analysis
 *   2. Hazardous Materials Database — fetched from GET /api/v1/hazmat on mount,
 *      with loading spinner, error card, and per-material detail cards.
 */

import { useState, useEffect } from 'react'
import { fetchHazmatList } from '../api/hazmat'
import './Dashboard.css'

// Color map for severity levels — matches the project's CSS palette
const SEVERITY_COLOR = {
  Low:      '#34d399',   // green
  Medium:   '#fbbf24',   // yellow
  High:     '#f97316',   // orange
  Critical: '#ef4444',   // red
}

export default function Dashboard() {
  // ── Form state ─────────────────────────────────────────────────────────────
  const [taskDescription, setTaskDescription] = useState('')
  const [severity, setSeverity] = useState('Medium')

  // ── Hazmat list state ───────────────────────────────────────────────────────
  const [hazmatList, setHazmatList] = useState([])
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState(null)

  // Fetch hazmat list once on mount; cancelled flag prevents setState after unmount
  useEffect(() => {
    let cancelled = false

    fetchHazmatList()
      .then((data) => {
        if (!cancelled) {
          setHazmatList(data)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          const msg = err.response
            ? `API error ${err.response.status}: ${err.response.statusText}`
            : 'Could not reach the API. Is the backend running on port 8000?'
          setError(msg)
          setLoading(false)
        }
      })

    return () => { cancelled = true }
  }, [])

  // ── Form submit ─────────────────────────────────────────────────────────────
  const handleSubmit = (e) => {
    e.preventDefault()
    // Future: POST to /api/v1/ppe/recommend with { task_description, severity }
  }

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="dashboard">

      {/* ── Section 1: Task input form ─────────────────────────────────────── */}
      <div className="dashboard-intro">
        <h2>Task Hazard Analysis</h2>
        <p>Describe the work task below. The system will identify hazards and recommend required PPE.</p>
      </div>

      <form className="input-card" onSubmit={handleSubmit}>
        <label className="input-label" htmlFor="task-input">Task Description</label>
        <textarea
          id="task-input"
          className="task-textarea"
          rows={4}
          placeholder="e.g. Welding steel beams on the second floor with grinding and cutting operations in building 3..."
          value={taskDescription}
          onChange={(e) => setTaskDescription(e.target.value)}
        />

        <div className="input-row">
          <div className="select-group">
            <label className="input-label" htmlFor="severity-select">Severity</label>
            <select
              id="severity-select"
              className="severity-select"
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
            >
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </select>
          </div>

          <button type="submit" className="submit-btn" disabled={!taskDescription.trim()}>
            Analyze Task
          </button>
        </div>
      </form>

      {/* ── Section 2: Hazardous Materials Database ────────────────────────── */}
      <div className="hazmat-section">
        <div className="hazmat-section-header">
          <h3>Hazardous Materials Database</h3>
          {!loading && !error && (
            <span className="hazmat-count">{hazmatList.length} materials</span>
          )}
        </div>

        {/* Loading */}
        {loading && (
          <div className="loading-card">
            <span className="loading-spinner" />
            Loading hazardous materials…
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div className="error-card">
            <span className="error-icon">!</span>
            {error}
          </div>
        )}

        {/* Empty */}
        {!loading && !error && hazmatList.length === 0 && (
          <div className="empty-card">No hazardous materials found in the database.</div>
        )}

        {/* Data */}
        {!loading && !error && hazmatList.length > 0 && (
          <div className="results">
            {hazmatList.map((mat) => (
              <div key={mat.id} className="hazard-card">

                <div className="hazard-card-header">
                  <span className="hazard-code">{mat.code}</span>
                  <span className="hazard-name">{mat.name}</span>
                  <span
                    className="severity-badge"
                    style={{ color: SEVERITY_COLOR[mat.severity] ?? '#e0e0e0' }}
                  >
                    {mat.severity}
                  </span>
                </div>

                <div className="hazard-meta">
                  <span className="hazard-category">{mat.category}</span>
                  <span className="hazard-class">{mat.hazard_class}</span>
                </div>

                <div className="hazard-keywords">
                  {mat.exposure_routes.map((route) => (
                    <span key={route} className="keyword-tag">{route}</span>
                  ))}
                </div>

                <div className="hazard-ppe-list">
                  {mat.ppe_required.map((ppe, idx) => (
                    <div key={idx} className="hazard-ppe-item">
                      <span className="ppe-name">{ppe.name}</span>
                      <span className="ppe-rationale">{ppe.rationale}</span>
                    </div>
                  ))}
                </div>

              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  )
}
