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
import { fetchSafetyRecords, analyzeTask, submitAIFeedback } from '../api/hazmat'
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
  const [severity, setSeverity] = useState('Moderate')

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

  // ── Analysis state ────────────────────────────────────────────────────────────
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [analysisError, setAnalysisError] = useState(null)

  // ── Feedback state (AI Response box) ────────────────────────────────────────
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false)
  const [feedbackError, setFeedbackError] = useState(null)
  const [feedbackSuccess, setFeedbackSuccess] = useState(null)
  const [reportOpen, setReportOpen] = useState(false)
  const [reportComment, setReportComment] = useState('')

  // ── Form submit ─────────────────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault()
    setAnalysisError(null)
    setAnalysisResult(null)
    setAnalysisLoading(true)
    setFeedbackError(null)
    setFeedbackSuccess(null)
    setReportOpen(false)
    setReportComment('')

    try {
      const result = await analyzeTask(taskDescription, severity)
      setAnalysisResult(result)
    } catch (err) {
      const msg = err.response?.data?.detail 
        || (err.response ? `API error ${err.response.status}` : 'Could not reach the backend API.')
      setAnalysisError(msg)
    } finally {
      setAnalysisLoading(false)
    }
  }

  const handleFeedback = async ({ feedbackType, comment }) => {
    const assessmentId = analysisResult?.assessment_id
    if (!assessmentId || feedbackSubmitting) return

    setFeedbackSubmitting(true)
    setFeedbackError(null)
    setFeedbackSuccess(null)

    try {
      await submitAIFeedback({
        assessmentId,
        feedbackType,
        comment,
      })

      if (feedbackType === 'thumbs_up') setFeedbackSuccess('Feedback saved: thumbs up.')
      if (feedbackType === 'thumbs_down') setFeedbackSuccess('Feedback saved: thumbs down.')
      if (feedbackType === 'report_inaccuracy') setFeedbackSuccess('Report submitted. Thanks for the correction.')
      if (feedbackType !== 'report_inaccuracy') setReportOpen(false)
      if (feedbackType === 'report_inaccuracy') setReportComment('')
    } catch (err) {
      const msg = err.response?.data?.detail
        || (err.response ? `API error ${err.response.status}` : 'Could not reach the backend API.')
      setFeedbackError(msg)
    } finally {
      setFeedbackSubmitting(false)
    }
  }

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="dashboard">

      {/* ── Section 1: Task input form ─────────────────────────────────────── */}
      <div className="dashboard-intro">
        <h2>Task Hazard Analysis</h2>
        <p>Describe the work task below. The system will identify hazards and recommend required PPE.</p>
      </div>

      <form className="input-card" onSubmit={handleSubmit} aria-label="Task hazard analysis form">
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
              <option value="Moderate">Moderate</option>
              <option value="High">High</option>
              <option value="Severe">Severe</option>
            </select>
          </div>

          <button type="submit" className="submit-btn" disabled={!taskDescription.trim()}>
            Analyze Task
          </button>
        </div>
      </form>

      {/* ── Section 1.5: Task Analysis Results ─────────────────────────────── */}
      {analysisLoading && <div className="loading-card" role="status" aria-live="polite"><span className="loading-spinner" aria-hidden="true" />Analyzing intent and matching hazards...</div>}
      {analysisError && <div className="error-card" role="alert"><span className="error-icon" aria-hidden="true">!</span>{analysisError}</div>}
      
      {analysisResult && (
        <div className="analysis-result-card" role="region" aria-label="AI analysis recommendation">
          <div className="analysis-header">
            <h3>AI Analysis Recommendation</h3>
            <span className="severity-badge" style={{ color: EXPOSURE_COLOR[analysisResult.severity_basis] }}>
              Severity Basis: {analysisResult.severity_basis}
            </span>
          </div>

          <div className="ai-feedback-row">
            <button
              type="button"
              className="ai-feedback-btn"
              disabled={feedbackSubmitting || !analysisResult.assessment_id}
              onClick={() => handleFeedback({ feedbackType: 'thumbs_up' })}
            >
              Thumbs Up
            </button>
            <button
              type="button"
              className="ai-feedback-btn"
              disabled={feedbackSubmitting || !analysisResult.assessment_id}
              onClick={() => handleFeedback({ feedbackType: 'thumbs_down' })}
            >
              Thumbs Down
            </button>
            <button
              type="button"
              className="ai-feedback-btn"
              disabled={feedbackSubmitting || !analysisResult.assessment_id}
              onClick={() => {
                setFeedbackError(null)
                setFeedbackSuccess(null)
                setReportOpen((v) => !v)
              }}
            >
              Report Inaccuracy
            </button>
          </div>

          {feedbackSuccess && <div className="ai-feedback-status success">{feedbackSuccess}</div>}
          {feedbackError && <div className="ai-feedback-status error">{feedbackError}</div>}

          {reportOpen && (
            <div className="ai-report-box">
              <label className="input-label" htmlFor="ai-report-comment">What is inaccurate or missing?</label>
              <textarea
                id="ai-report-comment"
                className="task-textarea"
                rows={3}
                value={reportComment}
                onChange={(e) => setReportComment(e.target.value)}
                placeholder="Example: The AI response is missing hearing protection due to grinding noise exposure..."
              />
              <div className="ai-report-actions">
                <button
                  type="button"
                  className="submit-btn"
                  disabled={feedbackSubmitting || !reportComment.trim()}
                  onClick={() => handleFeedback({ feedbackType: 'report_inaccuracy', comment: reportComment })}
                >
                  Submit Report
                </button>
                <button
                  type="button"
                  className="ai-feedback-btn secondary"
                  disabled={feedbackSubmitting}
                  onClick={() => setReportOpen(false)}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
          
          <div className="analysis-grid">
            <div className="analysis-col">
              <h4>Required Personal Protective Equipment</h4>
              {analysisResult.ppe_recommendations.length > 0 ? (
                <ul className="recommendations-list">
                  {analysisResult.ppe_recommendations.map(ppe => (
                    <li key={ppe.ppe_id}>
                      <strong>{ppe.ppe_type}</strong> <span className="cat-chip">({ppe.ppe_category})</span>
                      <p className="rationale-text">{ppe.rationale}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="empty-text">No PPE required for this task.</p>
              )}
            </div>

            <div className="analysis-col">
              <h4>Engineering Controls &amp; Protocols</h4>
              {analysisResult.engineering_controls.length > 0 ? (
                <ul className="recommendations-list">
                  {analysisResult.engineering_controls.map(ec => (
                    <li key={ec.control_type} className={ec.source === 'TINKER' ? 'tinker-control-item' : ''}>
                      <div className="control-header">
                        <strong>{ec.control_type}</strong>
                        {ec.source === 'TINKER' && (
                          <span className="tinker-badge" title="Required by Tinker AFB Risk Assessment Form">TINKER AFB FORM</span>
                        )}
                      </div>
                      <p className="rationale-text">{ec.rationale}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="empty-text">No specific physical controls required.</p>
              )}
            </div>
          </div>
        </div>
      )}


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
