/**
 * RiskAssessments.jsx — AI Assessment History & Safety Record Logging
 *
 * Sections:
 *   1. Assessment history — fetched from GET /api/v1/ai-assessments.
 *      Searchable + filterable by severity.  Each card is expandable to show
 *      the full PPE list and engineering controls.
 *   2. Log Safety Record modal — POST /api/v1/safety-records lets supervisors
 *      add new historical records that feed the recommendation engine.
 */

import { useState, useEffect, useMemo } from 'react'
import {
  fetchAIAssessments,
  fetchAIAssessmentDetail,
  fetchHazards,
  fetchPPECatalog,
  createSafetyRecord,
} from '../api/hazmat'
import './RiskAssessments.css'

const SEVERITY_COLOR = {
  Low: '#34d399',
  Moderate: '#fbbf24',
  High: '#f97316',
  Severe: '#ef4444',
  Unknown: '#9ca3af',
}

const SEVERITY_OPTIONS = ['All', 'Low', 'Moderate', 'High', 'Severe']
const SHIFT_OPTIONS = ['Day', 'Swing', 'Night']

// ─── Assessment Card ──────────────────────────────────────────────────────────

function AssessmentCard({ summary, onNavigate }) {
  const [expanded, setExpanded] = useState(false)
  const [detail, setDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [feedbackSent, setFeedbackSent] = useState(false)

  const handleExpand = async () => {
    if (!expanded && !detail) {
      setDetailLoading(true)
      try {
        const d = await fetchAIAssessmentDetail(summary.assessment_id)
        setDetail(d)
      } catch {
        setDetail(null)
      } finally {
        setDetailLoading(false)
      }
    }
    setExpanded((v) => !v)
  }

  const date = summary.created_at
    ? new Date(summary.created_at).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '—'

  return (
    <div className="assessment-card">
      <div className="assessment-card-header" onClick={handleExpand} role="button" tabIndex={0}
           onKeyDown={(e) => e.key === 'Enter' && handleExpand()}>
        <div className="assessment-meta">
          <span className="assessment-date">{date}</span>
          <span
            className="assessment-severity-badge"
            style={{ color: SEVERITY_COLOR[summary.severity_basis] ?? SEVERITY_COLOR.Unknown }}
          >
            {summary.severity_basis}
          </span>
        </div>
        <p className="assessment-description">{summary.task_description}</p>
        <div className="assessment-counts">
          <span className="count-chip ppe-chip-count">{summary.ppe_count} PPE item{summary.ppe_count !== 1 ? 's' : ''}</span>
          <span className="count-chip ctrl-chip-count">{summary.control_count} control{summary.control_count !== 1 ? 's' : ''}</span>
          <span className="expand-toggle">{expanded ? '▲ Collapse' : '▼ View Details'}</span>
        </div>
      </div>

      {expanded && (
        <div className="assessment-detail">
          {detailLoading && (
            <div className="detail-loading">
              <span className="loading-spinner" />Loading detail…
            </div>
          )}
          {!detailLoading && detail && (
            <div className="detail-grid">
              <div className="detail-col">
                <h4>Required PPE</h4>
                {detail.ppe_recommendations.length > 0 ? (
                  <ul className="detail-list">
                    {detail.ppe_recommendations.map((p) => (
                      <li key={p.ppe_id}>
                        <strong>{p.ppe_type}</strong>
                        <span className="cat-badge">{p.ppe_category}</span>
                        <p className="detail-rationale">{p.rationale}</p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="detail-empty">No PPE required.</p>
                )}
              </div>
              <div className="detail-col">
                <h4>Engineering Controls</h4>
                {detail.engineering_controls.length > 0 ? (
                  <ul className="detail-list">
                    {detail.engineering_controls.map((c) => (
                      <li key={c.control_type} className={c.source === 'TINKER' ? 'tinker-control-item' : ''}>
                        <div className="control-header">
                          <strong>{c.control_type}</strong>
                          {c.source === 'TINKER' && (
                            <span className="tinker-badge" title="Required by Tinker AFB Risk Assessment Form">TINKER AFB FORM</span>
                          )}
                        </div>
                        <p className="detail-rationale">{c.rationale}</p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="detail-empty">No specific physical controls required.</p>
                )}
              </div>
            </div>
          )}
          {!detailLoading && !detail && (
            <p className="detail-empty">Could not load detail for this assessment.</p>
          )}
        </div>
      )}
    </div>
  )
}

// ─── Log Safety Record Modal ──────────────────────────────────────────────────

function LogRecordModal({ hazards, ppeItems, onClose, onSaved }) {
  const emptyForm = {
    date: new Date().toISOString().slice(0, 10),
    location: '',
    work_type: '',
    hazard_id: '',
    exposure_level: 'Moderate',
    supervisor: '',
    shift: 'Day',
    incident_flag: false,
    temperature_f: '',
    noise_db: '',
    ppe_ids: [],
  }

  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState(null)

  const set = (field, value) => setForm((f) => ({ ...f, [field]: value }))

  const togglePPE = (id) =>
    setForm((f) => ({
      ...f,
      ppe_ids: f.ppe_ids.includes(id) ? f.ppe_ids.filter((x) => x !== id) : [...f.ppe_ids, id],
    }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setSaveError(null)
    try {
      const payload = {
        ...form,
        temperature_f: form.temperature_f ? Number(form.temperature_f) : null,
        noise_db: form.noise_db ? Number(form.noise_db) : null,
        supervisor: form.supervisor || null,
      }
      await createSafetyRecord(payload)
      onSaved()
    } catch (err) {
      setSaveError(err.response?.data?.detail || 'Failed to save record.')
    } finally {
      setSaving(false)
    }
  }

  // Group PPE by category for display
  const ppeByCategory = useMemo(() => {
    const map = {}
    ppeItems.forEach((p) => {
      ;(map[p.ppe_category] = map[p.ppe_category] || []).push(p)
    })
    return map
  }, [ppeItems])

  return (
    <div className="modal-backdrop" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-panel">
        <div className="modal-header">
          <h3>Log Safety Record</h3>
          <button className="modal-close-btn" onClick={onClose}>✕</button>
        </div>

        <form className="modal-form" onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Date *</label>
              <input
                type="date"
                className="form-input"
                value={form.date}
                onChange={(e) => set('date', e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Shift</label>
              <select className="form-input" value={form.shift} onChange={(e) => set('shift', e.target.value)}>
                {SHIFT_OPTIONS.map((s) => <option key={s}>{s}</option>)}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Location *</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Hangar 5"
                value={form.location}
                onChange={(e) => set('location', e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Work Type *</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Welding Operations"
                value={form.work_type}
                onChange={(e) => set('work_type', e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Hazard *</label>
              <select
                className="form-input"
                value={form.hazard_id}
                onChange={(e) => set('hazard_id', e.target.value)}
                required
              >
                <option value="">— Select hazard —</option>
                {hazards.map((h) => (
                  <option key={h.hazard_id} value={h.hazard_id}>
                    {h.hazard_label}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Exposure Level *</label>
              <select
                className="form-input"
                value={form.exposure_level}
                onChange={(e) => set('exposure_level', e.target.value)}
              >
                {['Low', 'Moderate', 'High', 'Severe'].map((l) => <option key={l}>{l}</option>)}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Supervisor</label>
              <input
                type="text"
                className="form-input"
                placeholder="optional"
                value={form.supervisor}
                onChange={(e) => set('supervisor', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Temp (°F)</label>
              <input
                type="number"
                className="form-input"
                placeholder="optional"
                value={form.temperature_f}
                onChange={(e) => set('temperature_f', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Noise (dB)</label>
              <input
                type="number"
                className="form-input"
                placeholder="optional"
                value={form.noise_db}
                onChange={(e) => set('noise_db', e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label incident-label">
              <input
                type="checkbox"
                checked={form.incident_flag}
                onChange={(e) => set('incident_flag', e.target.checked)}
              />
              Mark as Incident
            </label>
          </div>

          <div className="form-group ppe-select-group">
            <label className="form-label">PPE Required</label>
            <div className="ppe-grid">
              {Object.entries(ppeByCategory).map(([cat, items]) => (
                <div key={cat} className="ppe-cat-block">
                  <span className="ppe-cat-label">{cat}</span>
                  {items.map((p) => (
                    <label key={p.ppe_id} className="ppe-checkbox-label">
                      <input
                        type="checkbox"
                        checked={form.ppe_ids.includes(p.ppe_id)}
                        onChange={() => togglePPE(p.ppe_id)}
                      />
                      {p.ppe_label}
                    </label>
                  ))}
                </div>
              ))}
            </div>
          </div>

          {saveError && <div className="save-error">{saveError}</div>}

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={saving}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={saving || !form.location || !form.work_type || !form.hazard_id}>
              {saving ? 'Saving…' : 'Save Record'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function RiskAssessments({ onNavigate }) {
  const [assessments, setAssessments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [search, setSearch] = useState('')
  const [severityFilter, setSeverityFilter] = useState('All')

  const [showModal, setShowModal] = useState(false)
  const [hazards, setHazards] = useState([])
  const [ppeItems, setPpeItems] = useState([])
  const [refLoading, setRefLoading] = useState(false)

  const loadAssessments = () => {
    setLoading(true)
    setError(null)
    fetchAIAssessments()
      .then((data) => { setAssessments(data); setLoading(false) })
      .catch((err) => {
        const msg = err.response
          ? `API error ${err.response.status}: ${err.response.statusText}`
          : 'Could not reach the API. Is the backend running?'
        setError(msg)
        setLoading(false)
      })
  }

  useEffect(() => { loadAssessments() }, [])

  const handleOpenModal = async () => {
    if (!hazards.length) {
      setRefLoading(true)
      try {
        const [h, p] = await Promise.all([fetchHazards(), fetchPPECatalog()])
        setHazards(h)
        setPpeItems(p)
      } catch { /* non-fatal */ }
      setRefLoading(false)
    }
    setShowModal(true)
  }

  const handleRecordSaved = () => {
    setShowModal(false)
    loadAssessments()
  }

  // Stats
  const stats = useMemo(() => {
    const counts = { Low: 0, Moderate: 0, High: 0, Severe: 0 }
    assessments.forEach((a) => { if (a.severity_basis in counts) counts[a.severity_basis]++ })
    return counts
  }, [assessments])

  // Filtered list
  const filtered = useMemo(() => {
    let list = assessments
    if (severityFilter !== 'All') list = list.filter((a) => a.severity_basis === severityFilter)
    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter((a) => a.task_description.toLowerCase().includes(q))
    }
    return list
  }, [assessments, severityFilter, search])

  return (
    <div className="assessments-page">
      {/* Header */}
      <div className="assessments-page-header">
        <div>
          <h2>Risk Assessments</h2>
          <p>AI-generated hazard analysis history.  Use the Dashboard to run a new assessment.</p>
        </div>
        <div className="header-actions">
          <button className="btn-secondary" onClick={handleOpenModal} disabled={refLoading}>
            {refLoading ? 'Loading…' : '+ Log Safety Record'}
          </button>
          <button className="btn-primary" onClick={() => onNavigate('dashboard')}>
            New Assessment →
          </button>
        </div>
      </div>

      {/* Stats strip */}
      {!loading && !error && assessments.length > 0 && (
        <div className="assessments-stats">
          <div className="stat-chip">
            <span className="stat-value">{assessments.length}</span>
            <span className="stat-label">Total</span>
          </div>
          {Object.entries(stats).map(([sev, count]) => (
            <div key={sev} className="stat-chip">
              <span className="stat-value" style={{ color: SEVERITY_COLOR[sev] }}>{count}</span>
              <span className="stat-label">{sev}</span>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="assessments-filters">
        <input
          type="text"
          className="filter-search"
          placeholder="Search task descriptions…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <div className="severity-filter-group">
          {SEVERITY_OPTIONS.map((s) => (
            <button
              key={s}
              className={`severity-filter-btn ${severityFilter === s ? 'active' : ''}`}
              onClick={() => setSeverityFilter(s)}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {loading && (
        <div className="loading-card">
          <span className="loading-spinner" />Loading assessment history…
        </div>
      )}

      {!loading && error && (
        <div className="error-card">
          <span className="error-icon">!</span>{error}
        </div>
      )}

      {!loading && !error && assessments.length === 0 && (
        <div className="empty-card">
          <h3>No risk assessments yet</h3>
          <p>Run an analysis first so completed assessments appear here.</p>
          <button className="inline-link" onClick={() => onNavigate('dashboard')}>
            Run an analysis first
          </button>
        </div>
      )}

      {!loading && !error && assessments.length > 0 && filtered.length === 0 && (
        <div className="empty-card">
          <h3>No matches found</h3>
          <p>No assessments match the current search and severity filters.</p>
          <button
            className="inline-link"
            onClick={() => {
              setSearch('')
              setSeverityFilter('All')
            }}
          >
            Clear filters
          </button>
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="assessments-list">
          {filtered.map((a) => (
            <AssessmentCard key={a.assessment_id} summary={a} onNavigate={onNavigate} />
          ))}
        </div>
      )}

      {showModal && (
        <LogRecordModal
          hazards={hazards}
          ppeItems={ppeItems}
          onClose={() => setShowModal(false)}
          onSaved={handleRecordSaved}
        />
      )}
    </div>
  )
}
