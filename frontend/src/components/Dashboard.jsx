/**
 * Dashboard.jsx — Main Task Hazard Analysis Page
 *
 * This is the primary page of the application. It provides:
 *   - A textarea where the user describes a work task in plain text
 *   - A severity dropdown (Low / Medium / High / Critical)
 *   - A submit button to trigger hazard analysis
 *
 * Current state (Sprint 1):
 *   The form elements are wired up with React state but the submit
 *   handler is a no-op — there is no backend to call yet. A placeholder
 *   message is shown where results will eventually appear.
 *
 * Future integration (when backend is ready):
 *   - Import axios
 *   - In handleSubmit, POST to /api/v1/ppe/recommend with:
 *       { task_description: taskDescription, severity: severity }
 *   - Display the response: matched hazards and recommended PPE items
 *   - See Dashboard.css for result card styles (.results, .hazard-card,
 *     .ppe-summary-card, .ppe-chip, etc.) which are already defined
 */

import { useState } from 'react'
import './Dashboard.css'

export default function Dashboard() {
  // Controlled form state for the task description textarea
  const [taskDescription, setTaskDescription] = useState('')
  // Controlled form state for the severity dropdown
  const [severity, setSeverity] = useState('Medium')

  /**
   * Form submit handler.
   * Currently prevents default form behavior only.
   * Will be updated to call the backend API when it's available.
   */
  const handleSubmit = (e) => {
    e.preventDefault()
  }

  return (
    <div className="dashboard">
      {/* Page header — title and instructions */}
      <div className="dashboard-intro">
        <h2>Task Hazard Analysis</h2>
        <p>Describe the work task below. The system will identify hazards and recommend required PPE.</p>
      </div>

      {/* Input form — task description textarea + severity select + submit button */}
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
          {/* Severity selector — affects which PPE rules are triggered by the backend */}
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

          {/* Submit button — disabled when textarea is empty */}
          <button type="submit" className="submit-btn" disabled={!taskDescription.trim()}>
            Analyze Task
          </button>
        </div>
      </form>

      {/* Placeholder message — will be replaced with results when backend is connected */}
      <div className="empty-card">
        Backend not yet connected. The UI is ready — PPE recommendations will appear here once the API and database are configured.
      </div>
    </div>
  )
}
