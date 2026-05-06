import { useEffect, useState } from 'react'
import { fetchRiskPrediction } from '../api/hazmat'
import './RiskPrediction.css'

const LEVEL_CLASS = {
  Low: 'level-low',
  Moderate: 'level-moderate',
  High: 'level-high',
  Severe: 'level-severe',
}

function GaugeBar({ score }) {
  // Simple horizontal bar 0–100
  const color =
    score < 25 ? '#4caf50' : score < 50 ? '#ff9800' : score < 75 ? '#f44336' : '#b71c1c'
  return (
    <div className="gauge-wrap" aria-label={`Risk score ${score} out of 100`}>
      <div className="gauge-track">
        <div
          className="gauge-fill"
          style={{ width: `${score}%`, background: color }}
        />
      </div>
      <span className="gauge-label">{score} / 100</span>
    </div>
  )
}

function TrendChart({ trend }) {
  if (!trend || trend.length === 0) return null
  const maxRate = Math.max(...trend.map((t) => t.incident_rate), 0.01)
  return (
    <div className="trend-chart" role="img" aria-label="Monthly incident rate trend chart">
      <div className="trend-bars">
        {trend.map((pt) => {
          const pct = (pt.incident_rate / maxRate) * 100
          const colorClass =
            pt.incident_rate < 0.2
              ? 'bar-low'
              : pt.incident_rate < 0.4
              ? 'bar-mod'
              : 'bar-high'
          return (
            <div key={pt.month} className="trend-col">
              <div className="trend-bar-wrap">
                <div
                  className={`trend-bar ${colorClass}`}
                  style={{ height: `${pct}%` }}
                  title={`${pt.month}: ${(pt.incident_rate * 100).toFixed(0)}% incident rate (${pt.incidents}/${pt.total})`}
                />
              </div>
              <span className="trend-month-label">{pt.month.slice(5)}</span>
            </div>
          )
        })}
      </div>
      <div className="trend-x-label">Month (incident rate %)</div>
    </div>
  )
}

export default function RiskPrediction() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filterLocation, setFilterLocation] = useState('')
  const [filterWork, setFilterWork] = useState('')
  const [applied, setApplied] = useState({ location: null, work: null })

  const load = (loc, work) => {
    setLoading(true)
    setError(null)
    fetchRiskPrediction(loc || null, work || null)
      .then((d) => { setData(d); setLoading(false) })
      .catch((err) => {
        setError(err?.response?.data?.detail || err?.message || 'Failed to load prediction')
        setLoading(false)
      })
  }

  useEffect(() => { load(null, null) }, [])

  const handleApply = () => {
    setApplied({ location: filterLocation, work: filterWork })
    load(filterLocation, filterWork)
  }

  const handleReset = () => {
    setFilterLocation('')
    setFilterWork('')
    setApplied({ location: null, work: null })
    load(null, null)
  }

  return (
    <main className="rp-page" aria-labelledby="rp-title">
      <h1 id="rp-title">Risk Prediction</h1>
      <p className="rp-subtitle">
        Predicted risk level based on weighted historical incident data.
        The score factors in exposure severity and recent trend signals.
      </p>

      {/* Filters */}
      <section className="rp-filters" aria-label="Filter prediction">
        <div className="rp-filter-row">
          <label htmlFor="rp-location">Location</label>
          <input
            id="rp-location"
            type="text"
            placeholder="e.g. Engine Shop"
            value={filterLocation}
            onChange={(e) => setFilterLocation(e.target.value)}
          />
          <label htmlFor="rp-work">Work Type</label>
          <input
            id="rp-work"
            type="text"
            placeholder="e.g. Welding Task"
            value={filterWork}
            onChange={(e) => setFilterWork(e.target.value)}
          />
          <button className="btn-apply" onClick={handleApply}>Apply</button>
          {(applied.location || applied.work) && (
            <button className="btn-reset" onClick={handleReset}>Reset</button>
          )}
        </div>
        {(applied.location || applied.work) && (
          <p className="rp-filter-note">
            Showing prediction for{applied.location ? ` location: "${applied.location}"` : ''}
            {applied.work ? ` work type: "${applied.work}"` : ''}
          </p>
        )}
      </section>

      {loading && <p className="rp-loading" aria-live="polite">Loading prediction…</p>}
      {error && <p className="rp-error" role="alert">{error}</p>}

      {data && !loading && (
        <>
          {/* Score card */}
          <section className="rp-score-card" aria-label="Overall risk score">
            <div className={`rp-level-badge ${LEVEL_CLASS[data.risk_level]}`}>
              {data.risk_level} Risk
            </div>
            <GaugeBar score={data.overall_risk_score} />
            <div className="rp-stats-row">
              <div className="rp-stat">
                <span className="rp-stat-val">{(data.overall_incident_rate * 100).toFixed(1)}%</span>
                <span className="rp-stat-label">Historical Incident Rate</span>
              </div>
              <div className="rp-stat">
                <span className="rp-stat-val">{data.total_incidents}</span>
                <span className="rp-stat-label">Total Incidents</span>
              </div>
              <div className="rp-stat">
                <span className="rp-stat-val">{data.total_records}</span>
                <span className="rp-stat-label">Records Analyzed</span>
              </div>
            </div>
            <p className="rp-note">{data.prediction_note}</p>
          </section>

          <div className="rp-two-col">
            {/* Top hazards */}
            <section className="rp-card" aria-labelledby="rp-hazards-title">
              <h2 id="rp-hazards-title">Top Risk Hazards</h2>
              {data.top_hazards.length === 0 ? (
                <p>No hazards with enough data.</p>
              ) : (
                <table className="rp-table">
                  <thead>
                    <tr>
                      <th>Hazard</th>
                      <th>Incidents</th>
                      <th>Records</th>
                      <th>Weighted Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.top_hazards.map((h) => (
                      <tr key={h.label}>
                        <td>{h.label}</td>
                        <td>{h.incident_count}</td>
                        <td>{h.total_records}</td>
                        <td>
                          <span
                            className={`rate-pill ${
                              h.incident_rate > 0.5
                                ? 'rate-high'
                                : h.incident_rate > 0.25
                                ? 'rate-mod'
                                : 'rate-low'
                            }`}
                          >
                            {(h.incident_rate * 100).toFixed(0)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>

            {/* Top locations */}
            <section className="rp-card" aria-labelledby="rp-locs-title">
              <h2 id="rp-locs-title">Highest-Risk Locations</h2>
              {data.top_locations.length === 0 ? (
                <p>No location data available.</p>
              ) : (
                <table className="rp-table">
                  <thead>
                    <tr>
                      <th>Location</th>
                      <th>Incidents</th>
                      <th>Records</th>
                      <th>Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.top_locations.map((l) => (
                      <tr key={l.label}>
                        <td>{l.label}</td>
                        <td>{l.incident_count}</td>
                        <td>{l.total_records}</td>
                        <td>
                          <span
                            className={`rate-pill ${
                              l.incident_rate > 0.5
                                ? 'rate-high'
                                : l.incident_rate > 0.25
                                ? 'rate-mod'
                                : 'rate-low'
                            }`}
                          >
                            {(l.incident_rate * 100).toFixed(0)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          </div>

          {/* Trend chart */}
          <section className="rp-card rp-trend-section" aria-labelledby="rp-trend-title">
            <h2 id="rp-trend-title">12-Month Incident Rate Trend</h2>
            <TrendChart trend={data.monthly_trend} />
          </section>
        </>
      )}
    </main>
  )
}
