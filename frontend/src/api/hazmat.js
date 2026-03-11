/**
 * hazmat.js — Hazardous Materials API functions
 *
 * All functions return a Promise that resolves with the response data,
 * or rejects with an Axios error if the request fails.
 */

import client from './client'

/**
 * Fetches the full list of hazardous materials.
 * @returns {Promise<Array>}
 */
export async function fetchHazmatList() {
  const response = await client.get('/api/v1/hazmat')
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
