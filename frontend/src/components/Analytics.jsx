import { useEffect, useMemo, useRef, useState } from 'react'
import { fetchSafetyRecords } from '../api/hazmat'
import './Analytics.css'

const CHART_JS_CDN = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js'

const DATE_FILTERS = [
  { id: 'all', label: 'All Time' },
  { id: '180', label: 'Last 180 Days' },
  { id: '90', label: 'Last 90 Days' },
]

let chartLoaderPromise = null

function ensureChartJs() {
  if (window.Chart) return Promise.resolve(window.Chart)

  if (!chartLoaderPromise) {
    chartLoaderPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script')
      script.src = CHART_JS_CDN
      script.async = true
      script.onload = () => resolve(window.Chart)
      script.onerror = () => reject(new Error('Failed to load Chart.js from CDN.'))
      document.head.appendChild(script)
    })
  }

  return chartLoaderPromise
}

function toDate(value) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function getCutoffDate(filterId) {
  if (filterId === 'all') return null
  const days = Number(filterId)
  if (!Number.isFinite(days)) return null

  const cutoff = new Date()
  cutoff.setDate(cutoff.getDate() - days)
  return cutoff
}

export default function Analytics() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [dateFilter, setDateFilter] = useState('180')
  const [lastUpdated, setLastUpdated] = useState(null)

  const incidentChartRef = useRef(null)
  const hazardChartRef = useRef(null)
  const complianceChartRef = useRef(null)

  const chartInstances = useRef({
    incident: null,
    hazard: null,
    compliance: null,
  })

  const loadRecords = async () => {
    setError(null)
    setLoading(true)

    try {
      const data = await fetchSafetyRecords()
      setRecords(Array.isArray(data) ? data : [])
      setLastUpdated(new Date())
    } catch (err) {
      const message = err.response
        ? `API error ${err.response.status}: ${err.response.statusText}`
        : 'Could not reach API for analytics data. Confirm backend on port 8000.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRecords()

    const interval = setInterval(loadRecords, 60000)
    return () => clearInterval(interval)
  }, [])

  const filteredRecords = useMemo(() => {
    const cutoff = getCutoffDate(dateFilter)
    if (!cutoff) return records

    return records.filter((record) => {
      const recordDate = toDate(record.date)
      return recordDate ? recordDate >= cutoff : false
    })
  }, [records, dateFilter])

  const incidentTrend = useMemo(() => {
    const monthBuckets = new Map()

    filteredRecords.forEach((record) => {
      const recordDate = toDate(record.date)
      if (!recordDate) return

      const bucketLabel = recordDate.toLocaleString('en-US', {
        month: 'short',
        year: '2-digit',
      })

      if (!monthBuckets.has(bucketLabel)) {
        monthBuckets.set(bucketLabel, { label: bucketLabel, incidents: 0, total: 0, sortKey: new Date(recordDate.getFullYear(), recordDate.getMonth(), 1) })
      }

      const bucket = monthBuckets.get(bucketLabel)
      bucket.total += 1
      if (record.incident_flag) bucket.incidents += 1
    })

    return Array.from(monthBuckets.values())
      .sort((a, b) => a.sortKey - b.sortKey)
      .map(({ label, incidents, total }) => ({ label, incidents, total }))
  }, [filteredRecords])

  const hazardDistribution = useMemo(() => {
    const hazardCount = new Map()

    filteredRecords.forEach((record) => {
      const key = record.hazard_label || 'Unspecified Hazard'
      hazardCount.set(key, (hazardCount.get(key) || 0) + 1)
    })

    return Array.from(hazardCount.entries())
      .map(([hazard, count]) => ({ hazard, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8)
  }, [filteredRecords])

  const complianceMetrics = useMemo(() => {
    if (filteredRecords.length === 0) {
      return { compliant: 0, incidentFlagged: 0, missingPpe: 0, complianceRate: 0 }
    }

    const incidentFlagged = filteredRecords.filter((record) => record.incident_flag).length
    const missingPpe = filteredRecords.filter((record) => !record.ppe_required || record.ppe_required.length === 0).length
    const compliant = Math.max(filteredRecords.length - incidentFlagged - missingPpe, 0)
    const complianceRate = Math.round((compliant / filteredRecords.length) * 100)

    return { compliant, incidentFlagged, missingPpe, complianceRate }
  }, [filteredRecords])

  useEffect(() => {
    let mounted = true

    const drawCharts = async () => {
      try {
        const Chart = await ensureChartJs()
        if (!mounted) return

        Object.values(chartInstances.current).forEach((chart) => {
          if (chart) chart.destroy()
        })

        if (incidentChartRef.current) {
          chartInstances.current.incident = new Chart(incidentChartRef.current, {
            type: 'line',
            data: {
              labels: incidentTrend.map((entry) => entry.label),
              datasets: [
                {
                  label: 'Incidents',
                  data: incidentTrend.map((entry) => entry.incidents),
                  borderColor: '#f97316',
                  backgroundColor: 'rgba(249, 115, 22, 0.25)',
                  fill: true,
                  tension: 0.25,
                },
                {
                  label: 'Total Records',
                  data: incidentTrend.map((entry) => entry.total),
                  borderColor: '#93c5fd',
                  backgroundColor: 'rgba(147, 197, 253, 0.2)',
                  fill: false,
                  tension: 0.2,
                },
              ],
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              interaction: { mode: 'index', intersect: false },
              plugins: { legend: { labels: { color: '#d1d5db' } } },
              scales: {
                x: { ticks: { color: '#9ca3af' }, grid: { color: '#2a2d35' } },
                y: { ticks: { color: '#9ca3af' }, grid: { color: '#2a2d35' }, beginAtZero: true },
              },
            },
          })
        }

        if (hazardChartRef.current) {
          chartInstances.current.hazard = new Chart(hazardChartRef.current, {
            type: 'bar',
            data: {
              labels: hazardDistribution.map((entry) => entry.hazard),
              datasets: [
                {
                  label: 'Occurrences',
                  data: hazardDistribution.map((entry) => entry.count),
                  backgroundColor: ['#fb7185', '#f97316', '#facc15', '#4ade80', '#22d3ee', '#60a5fa', '#a78bfa', '#f472b6'],
                  borderRadius: 6,
                },
              ],
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: (ctx) => `${ctx.parsed.y} records` } },
              },
              scales: {
                x: {
                  ticks: {
                    color: '#9ca3af',
                    callback(value) {
                      const label = this.getLabelForValue(value)
                      return label.length > 18 ? `${label.slice(0, 18)}…` : label
                    },
                  },
                  grid: { color: '#2a2d35' },
                },
                y: { ticks: { color: '#9ca3af' }, grid: { color: '#2a2d35' }, beginAtZero: true },
              },
            },
          })
        }

        if (complianceChartRef.current) {
          chartInstances.current.compliance = new Chart(complianceChartRef.current, {
            type: 'doughnut',
            data: {
              labels: ['Compliant', 'Incident Flagged', 'Missing PPE'],
              datasets: [
                {
                  data: [
                    complianceMetrics.compliant,
                    complianceMetrics.incidentFlagged,
                    complianceMetrics.missingPpe,
                  ],
                  backgroundColor: ['#34d399', '#f97316', '#ef4444'],
                  borderColor: '#1f2937',
                },
              ],
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { position: 'bottom', labels: { color: '#d1d5db' } },
              },
              cutout: '65%',
            },
          })
        }
      } catch (chartError) {
        if (mounted) {
          setError(chartError.message || 'Failed to render analytics charts.')
        }
      }
    }

    drawCharts()

    return () => {
      mounted = false
      Object.values(chartInstances.current).forEach((chart) => {
        if (chart) chart.destroy()
      })
      chartInstances.current = { incident: null, hazard: null, compliance: null }
    }
  }, [incidentTrend, hazardDistribution, complianceMetrics])

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <div>
          <h2>Analytics</h2>
          <p>Live risk insights for incident history, hazard frequency, and compliance posture.</p>
        </div>

        <div className="analytics-controls">
          <select value={dateFilter} onChange={(event) => setDateFilter(event.target.value)}>
            {DATE_FILTERS.map((filter) => (
              <option key={filter.id} value={filter.id}>{filter.label}</option>
            ))}
          </select>
          <button type="button" onClick={loadRecords}>Refresh Data</button>
        </div>
      </div>

      {lastUpdated && (
        <div className="analytics-updated">Last updated: {lastUpdated.toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' })}</div>
      )}

      {loading && <div className="analytics-card status-card">Loading analytics dataset…</div>}
      {error && <div className="analytics-card status-card error">{error}</div>}

      {!loading && !error && (
        <>
          <div className="analytics-kpis">
            <div className="analytics-card kpi-card">
              <span>Total Records</span>
              <strong>{filteredRecords.length}</strong>
            </div>
            <div className="analytics-card kpi-card">
              <span>Incident Rate</span>
              <strong>
                {filteredRecords.length
                  ? `${Math.round((complianceMetrics.incidentFlagged / filteredRecords.length) * 100)}%`
                  : '0%'}
              </strong>
            </div>
            <div className="analytics-card kpi-card">
              <span>Compliance Score</span>
              <strong>{complianceMetrics.complianceRate}%</strong>
            </div>
          </div>

          <div className="analytics-grid">
            <section className="analytics-card chart-card">
              <h3>Historical Incident Trends</h3>
              <p>Compare monthly incident counts against total submitted records.</p>
              <div className="chart-wrap"><canvas ref={incidentChartRef} /></div>
            </section>

            <section className="analytics-card chart-card">
              <h3>Most Common Hazards</h3>
              <p>Top hazard labels by occurrence across the selected timeframe.</p>
              <div className="chart-wrap"><canvas ref={hazardChartRef} /></div>
            </section>

            <section className="analytics-card chart-card full-width">
              <h3>Facility Compliance Metrics</h3>
              <p>Distribution of compliant records, incident-flagged events, and missing PPE documentation.</p>
              <div className="compliance-layout">
                <div className="chart-wrap donut"><canvas ref={complianceChartRef} /></div>
                <ul className="compliance-legend">
                  <li><span className="swatch compliant" />Compliant Records: {complianceMetrics.compliant}</li>
                  <li><span className="swatch incident" />Incident Flagged: {complianceMetrics.incidentFlagged}</li>
                  <li><span className="swatch missing" />Missing PPE Mapping: {complianceMetrics.missingPpe}</li>
                </ul>
              </div>
            </section>
          </div>
        </>
      )}
    </div>
  )
}
