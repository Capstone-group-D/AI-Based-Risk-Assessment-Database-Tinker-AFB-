import { useState, useEffect } from 'react'
import './PollutionPrevention.css'

export default function PollutionPrevention() {
  const [opportunities, setOpportunities] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filterPriority, setFilterPriority] = useState('')
  const [filterStatus, setFilterStatus] = useState('')

  useEffect(() => {
    fetchOpportunities()
  }, [filterPriority, filterStatus])

  const fetchOpportunities = async () => {
    try {
      setLoading(true)
      // Need to change later
      //let url = 'http://localhost:8000/api/v1/pollution-prevention'
      let url = 'http://localhost:8000/pollution-prevention'

      const params = new URLSearchParams()
      if (filterPriority) params.append('priority_level', filterPriority)
      if (filterStatus) params.append('status', filterStatus)

      if (params.toString()) {
        url += '?' + params.toString()
      }

      const response = await fetch(url)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setOpportunities(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'Critical': return '#dc3545'
      case 'High': return '#fd7e14'
      case 'Medium': return '#ffc107'
      case 'Low': return '#28a745'
      default: return '#6c757d'
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'Completed': return '#28a745'
      case 'Implementing': return '#007bff'
      case 'Planned': return '#ffc107'
      case 'Identified': return '#6c757d'
      default: return '#6c757d'
    }
  }

  if (loading) {
    return (
      <div className="pollution-prevention">
        <div className="loading">Loading pollution prevention opportunities...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="pollution-prevention">
        <div className="error">Error loading data: {error}</div>
      </div>
    )
  }

  return (
    <div className="pollution-prevention">
      <div className="page-header">
        <h1>♻ Pollution Prevention Opportunities</h1>
        <p>Identify and track opportunities to reduce hazardous waste generation in depot operations</p>
      </div>

      <div className="filters-section">
        <div className="filter-group">
          <label htmlFor="priority-filter">Priority Level:</label>
          <select
            id="priority-filter"
            value={filterPriority}
            onChange={(e) => setFilterPriority(e.target.value)}
          >
            <option value="">All Priorities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="status-filter">Status:</label>
          <select
            id="status-filter"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="Identified">Identified</option>
            <option value="Planned">Planned</option>
            <option value="Implementing">Implementing</option>
            <option value="Completed">Completed</option>
          </select>
        </div>
      </div>

      <div className="opportunities-grid">
        {opportunities.map((opportunity) => (
          <div key={opportunity.opportunity_id} className="opportunity-card">
            <div className="card-header">
              <h3>{opportunity.task_name}</h3>
              <div className="priority-badge" style={{ backgroundColor: getPriorityColor(opportunity.priority_level) }}>
                {opportunity.priority_level}
              </div>
            </div>

            <div className="card-body">
              <p className="task-description">{opportunity.task_description}</p>

              <div className="prevention-details">
                <h4>Prevention Method:</h4>
                <p>{opportunity.prevention_method}</p>

                <div className="metrics">
                  <div className="metric">
                    <span className="metric-label">Expected Reduction:</span>
                    <span className="metric-value">{opportunity.expected_reduction_percent}%</span>
                  </div>

                  {opportunity.implementation_cost_usd && (
                    <div className="metric">
                      <span className="metric-label">Implementation Cost:</span>
                      <span className="metric-value">${opportunity.implementation_cost_usd.toLocaleString()}</span>
                    </div>
                  )}

                  {opportunity.payback_period_months && (
                    <div className="metric">
                      <span className="metric-label">Payback Period:</span>
                      <span className="metric-value">{opportunity.payback_period_months} months</span>
                    </div>
                  )}
                </div>

                <div className="status-section">
                  <span className="status-label">Status:</span>
                  <span className="status-badge" style={{ backgroundColor: getStatusColor(opportunity.status) }}>
                    {opportunity.status}
                  </span>
                </div>

                {opportunity.responsible_party && (
                  <div className="responsible-party">
                    <span className="responsible-label">Responsible:</span>
                    <span className="responsible-value">{opportunity.responsible_party}</span>
                  </div>
                )}

                {opportunity.notes && (
                  <div className="notes-section">
                    <h4>Notes:</h4>
                    <p>{opportunity.notes}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {opportunities.length === 0 && (
        <div className="no-results">
          <p>No pollution prevention opportunities found matching the current filters.</p>
        </div>
      )}
    </div>
  )
}