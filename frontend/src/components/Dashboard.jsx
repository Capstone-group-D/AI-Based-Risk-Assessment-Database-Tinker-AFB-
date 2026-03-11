/**
 * Dashboard.jsx — Main Task Hazard Analysis Page
 *
 * Sections:
 *   1. Task input form  — describe a task, pick severity, submit for analysis
 *   2. Safety Records   — fetched from GET /api/v1/safety-records on mount,
 *      with loading spinner, error card, and per-record detail cards.
 *
 * Field mapping from the database (db/schema.sql):
 *   record.record_id        → safety_records.record_id
 *   record.hazard_label     → hazards.hazard_label
 *   record.hazard_category  → hazards.hazard_category
 *   record.exposure_level   → safety_records.exposure_level
 *   record.work_type        → safety_records.work_type
 *   record.location         → safety_records.location
 *   record.shift            → safety_records.shift
 *   record.incident_flag    → safety_records.incident_flag
 *   record.ppe_required[]   → JOIN safety_record_ppe → ppe
 */

import { useState, useEffect } from 'react'
import { fetchSafetyRecords } from '../api/hazmat'
import './Dashboard.css'

// Exposure level colors — matches db/schema.sql CHECK constraint values
const EXPOSURE_COLOR = {
  Low:      '#34d399',   // green
  Moderate: '#fbbf24',   // yellow
  High:     '#f97316',   // orange
  Severe:   '#ef4444',   // red
}

export default function Dashboard() {
  // ── Form state ─────────────────────────────────────────────────────────────
  const [taskDescription, setTaskDescription] = useState('')
  const [severity, setSeverity] = useState('Medium')

  // ── Safety records state ────────────────────────────────────────────────────
  const [records, setRecords]   = useState([])
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState(null)

  // Fetch safety records once on mount; cancelled flag prevents setState after unmount
  useEffect(() => {
    let cancelled = false

    fetchSafetyRecords()
      .then((data) => {
        if (!cancelled) {
          setRecords(data)
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
    // Future: POST to /api/v1/recommend-ppe with { task_description, severity }
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

      {/* ── Section 2: Safety Records ──────────────────────────────────────── */}
      <div className="hazmat-section">
        <div className="hazmat-section-header">
          <h3>Safety Records</h3>
          {!loading && !error && (
            <span className="hazmat-count">{records.length} records</span>
          )}
        </div>

        {/* Loading */}
        {loading && (
          <div className="loading-card">
            <span className="loading-spinner" />
            Loading safety records…
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
        {!loading && !error && records.length === 0 && (
          <div className="empty-card">No safety records found in the database.</div>
        )}

        {/* Data */}
        {!loading && !error && records.length > 0 && (
          <div className="results">
            {records.map((record) => (
              <div key={record.record_id} className="hazard-card">

                <div className="hazard-card-header">
                  <span className="hazard-code">{record.record_id}</span>
                  <span className="hazard-name">{record.hazard_label}</span>
                  <span
                    className="severity-badge"
                    style={{ color: EXPOSURE_COLOR[record.exposure_level] ?? '#e0e0e0' }}
                  >
                    {record.exposure_level}
                  </span>
                </div>

                {/* hazard_category (from hazards table) + work_type (from safety_records) */}
                <div className="hazard-meta">
                  <span className="hazard-category">{record.hazard_category}</span>
                  <span className="hazard-class">{record.work_type}</span>
                </div>

                {/* location, shift, and incident flag as keyword chips */}
                <div className="hazard-keywords">
                  <span className="keyword-tag">{record.location}</span>
                  <span className="keyword-tag">{record.shift} Shift</span>
                  {record.incident_flag && (
                    <span className="keyword-tag incident-tag">Incident</span>
                  )}
                </div>

                {/* ppe_required — joined from safety_record_ppe + ppe tables */}
                <div className="hazard-ppe-list">
                  {record.ppe_required.map((ppe) => (
                    <div key={ppe.ppe_id} className="hazard-ppe-item">
                      <span className="ppe-name">{ppe.ppe_label}</span>
                      <span className="ppe-rationale">{ppe.ppe_category}</span>
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
