/**
 * hazmat.js — Safety Records & AI Assessment API Functions
 *
 * All functions return a Promise that resolves with the response data,
 * or rejects with an Axios error if the request fails.
 */

import client from './client'

// ── Health ────────────────────────────────────────────────────────────────────

export async function checkHealth() {
  const response = await client.get('/api/v1/health')
  return response.data
}

// ── Safety Records ────────────────────────────────────────────────────────────

export async function fetchSafetyRecords() {
  const response = await client.get('/api/v1/safety-records')
  return response.data
}

/**
 * Creates a new safety record.
 * @param {Object} data  Matches SafetyRecordCreate schema:
 *   { date, location, work_type, hazard_id, exposure_level,
 *     temperature_f?, noise_db?, airborne_particles_ppm?,
 *     supervisor?, shift?, incident_flag?, ppe_ids? }
 */
export async function createSafetyRecord(data) {
  const response = await client.post('/api/v1/safety-records', data)
  return response.data
}

// ── Admin ─────────────────────────────────────────────────────────────────────

/**
 * Submits a password to the admin login endpoint.
 * Resolves on success, rejects with an error on 401.
 */
export async function adminLogin(password) {
  const response = await client.post('/api/v1/admin/login', { password })
  return response.data
}

// ── AI Task Analysis ──────────────────────────────────────────────────────────

/**
 * Submits a task description for AI hazard analysis.
 * severity must be one of: Low | Moderate | High | Severe
 */
export async function analyzeTask(taskDescription, severityLevel = 'Moderate') {
  const response = await client.post('/api/v1/analyze-task', {
    task_description: taskDescription,
    severity_level: severityLevel,
  })
  return response.data
}

// ── AI Feedback ───────────────────────────────────────────────────────────────

export async function submitAIFeedback({ assessmentId, feedbackType, comment }) {
  const response = await client.post('/api/v1/ai-feedback', {
    assessment_id: assessmentId,
    feedback_type: feedbackType,
    comment,
  })
  return response.data
}

// ── AI Assessment History ─────────────────────────────────────────────────────

export async function fetchAIAssessments() {
  const response = await client.get('/api/v1/ai-assessments')
  return response.data
}

export async function fetchAIAssessmentDetail(assessmentId) {
  const response = await client.get(`/api/v1/ai-assessments/${assessmentId}`)
  return response.data
}

// ── Reference Data ────────────────────────────────────────────────────────────

export async function fetchPPECatalog() {
  const response = await client.get('/api/v1/ppe')
  return response.data
}

export async function fetchHazards() {
  const response = await client.get('/api/v1/hazards')
  return response.data
}

// ── AUL Materials ─────────────────────────────────────────────────────────────

export async function fetchMaterials(q = '') {
  const params = q ? { q } : {}
  const response = await client.get('/api/v1/materials', { params })
  return response.data
}

export async function fetchMaterialAuthorizations(msn) {
  const response = await client.get(`/api/v1/materials/${encodeURIComponent(msn)}/authorizations`)
  return response.data
}

export async function fetchShops() {
  const response = await client.get('/api/v1/shops')
  return response.data
}

/**
 * Recommends PPE for a specific AUL material by MSN.
 * @param {string} msn  Material Stock Number
 * @param {string} severityLevel  Low | Moderate | High | Severe
 */
export async function recommendPPEForMaterial(msn, severityLevel = 'Moderate') {
  const response = await client.post('/api/v1/materials/recommend-ppe', {
    msn,
    severity_level: severityLevel,
  })
  return response.data
}
