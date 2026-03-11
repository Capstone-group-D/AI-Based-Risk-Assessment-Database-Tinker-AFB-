/**
 * hazmat.js — Safety Records API functions
 *
 * All functions return a Promise that resolves with the response data,
 * or rejects with an Axios error if the request fails.
 */

import client from './client'

/**
 * Fetches the full list of safety records (joined with hazard and PPE data).
 * Maps to GET /api/v1/safety-records → safety_records JOIN hazards JOIN ppe
 * @returns {Promise<Array>}
 */
export async function fetchSafetyRecords() {
  const response = await client.get('/api/v1/safety-records')
  return response.data
}

/**
 * Pings the health endpoint to verify the backend is reachable.
 * @returns {Promise<Object>}  e.g. { status: "ok", message: "API online" }
 */
export async function checkHealth() {
  const response = await client.get('/api/v1/health')
  return response.data
}
