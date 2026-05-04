/**
 * AIFeedbackPanel.jsx — Admin: AI Feedback Loop
 *
 * Sprint 3 placeholder for Ticket 2: AI Feedback Loop.
 * Sections:
 *   1. Recent Analysis Requests — pulls from /api/v1/safety-records
 *   2. Model Feedback Queue    — stub
 *   3. Retraining Log          — stub
 */

import { useState, useEffect } from 'react'
import { fetchSafetyRecords } from '../api/hazmat'
import './AIFeedbackPanel.css'

export default function AIFeedbackPanel() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchSafetyRecords()
      .then((data) => setRecords(data))
      .catch(() => setError('Failed to load safety records.'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="ai-feedback-panel">
      <div className="afp-header">
        <h2 className="afp-title">AI Feedback Loop</h2>
        <span className="afp-badge">Sprint 3 — In Development</span>
      </div>

      {/* Section 1: Recent Analysis Requests */}
      <section className="afp-section">
        <h3 className="afp-section-title">Recent Analysis Requests</h3>
        <p className="afp-section-desc">Live data from <code>/api/v1/safety-records</code></p>
        {loading && <p className="afp-loading">Loading records…</p>}
        {error && <p className="afp-error">{error}</p>}
        {!loading && !error && (
          <div className="afp-table-wrapper">
            <table className="afp-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Task</th>
                  <th>Hazard Level</th>
                  <th>PPE Required</th>
                </tr>
              </thead>
              <tbody>
                {records.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="afp-empty">No records found.</td>
                  </tr>
                ) : (
                  records.slice(0, 10).map((r) => (
                    <tr key={r.id}>
                      <td>{r.id}</td>
                      <td>{r.task_description ?? r.task ?? '—'}</td>
                      <td>{r.hazard_level ?? r.risk_level ?? '—'}</td>
                      <td>{r.ppe_required ?? r.ppe ?? '—'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Section 2: Model Feedback Queue (stub) */}
      <section className="afp-section">
        <h3 className="afp-section-title">Model Feedback Queue</h3>
        <p className="afp-section-desc">
          Analyst corrections and confidence flags will appear here for model retraining review.
        </p>
        <div className="afp-stub">
          <span className="afp-stub-icon">◈</span>
          <span>Coming in Sprint 3 — Ticket 2</span>
        </div>
      </section>

      {/* Section 3: Retraining Log (stub) */}
      <section className="afp-section">
        <h3 className="afp-section-title">Retraining Log</h3>
        <p className="afp-section-desc">
          A history of model retraining runs, accuracy deltas, and deployment timestamps.
        </p>
        <div className="afp-stub">
          <span className="afp-stub-icon">◈</span>
          <span>Coming in Sprint 3 — Ticket 2</span>
        </div>
      </section>
    </div>
  )
}
