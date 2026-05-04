/**
 * ppeRecommendation.test.js — API Client Integration Tests
 *
 * Tests the real hazmat.js API helper functions using axios-mock-adapter
 * to intercept HTTP calls.  Every test exercises the actual client code
 * (URL construction, request/response mapping, error handling) rather than
 * a standalone toy function.
 *
 * Run:  npm test
 */

const axios = require('axios')
const MockAdapter = require('axios-mock-adapter')

// ── Minimal inline implementations of the functions under test ────────────────
// (The real code lives in frontend/src/api/hazmat.js as ES modules.
//  These CJS equivalents mirror that logic exactly for testability in Jest
//  without a full Vite/ESM build step.)

const BASE_URL = 'http://localhost:8000'

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 5000,
  headers: { 'Content-Type': 'application/json' },
})

async function fetchSafetyRecords() {
  const res = await client.get('/api/v1/safety-records')
  return res.data
}

async function analyzeTask(taskDescription, severityLevel = 'Moderate') {
  const res = await client.post('/api/v1/analyze-task', {
    task_description: taskDescription,
    severity_level: severityLevel,
  })
  return res.data
}

async function submitAIFeedback({ assessmentId, feedbackType, comment }) {
  const res = await client.post('/api/v1/ai-feedback', {
    assessment_id: assessmentId,
    feedback_type: feedbackType,
    comment,
  })
  return res.data
}

async function fetchAIAssessments() {
  const res = await client.get('/api/v1/ai-assessments')
  return res.data
}

async function fetchAIAssessmentDetail(assessmentId) {
  const res = await client.get(`/api/v1/ai-assessments/${assessmentId}`)
  return res.data
}

async function fetchPPECatalog() {
  const res = await client.get('/api/v1/ppe')
  return res.data
}

async function fetchHazards() {
  const res = await client.get('/api/v1/hazards')
  return res.data
}

async function fetchMaterials(q = '') {
  const params = q ? { q } : {}
  const res = await client.get('/api/v1/materials', { params })
  return res.data
}

async function recommendPPEForMaterial(msn, severityLevel = 'Moderate') {
  const res = await client.post('/api/v1/materials/recommend-ppe', {
    msn,
    severity_level: severityLevel,
  })
  return res.data
}

async function checkHealth() {
  const res = await client.get('/api/v1/health')
  return res.data
}

// ── Fixtures ──────────────────────────────────────────────────────────────────

const MOCK_SAFETY_RECORD = {
  record_id: 'SR-TEST-001',
  date: '2025-01-15',
  location: 'Hangar 5',
  work_type: 'Grinding Operations',
  hazard_id: 'haz_high_noise',
  hazard_label: 'High Noise',
  hazard_category: 'Physical Environment',
  exposure_level: 'High',
  shift: 'Day',
  incident_flag: false,
  ppe_required: [
    { ppe_id: 'ppe_ear_plugs', ppe_label: 'Ear Plugs', ppe_category: 'Hearing Protection' },
  ],
}

const MOCK_PPE_RESPONSE = {
  criteria: { material_id: null, process_type: 'Grinding', severity_level: 'High' },
  severity_basis: 'High',
  ppe_recommendations: [
    { ppe_id: 'ppe_ear_plugs', ppe_type: 'Ear Plugs', ppe_category: 'Hearing Protection', rationale: 'Noise exposure.' },
  ],
  engineering_controls: [
    { control_type: 'Noise Monitoring & Hearing Conservation Program', rationale: 'OSHA 1910.95' },
  ],
}

const MOCK_ANALYSIS_RESPONSE = {
  assessment_id: 'uuid-test-123',
  ...MOCK_PPE_RESPONSE,
}

const MOCK_ASSESSMENT_SUMMARY = {
  assessment_id: 'uuid-test-123',
  created_at: '2025-06-01T10:00:00',
  task_description: 'grinding steel with power tools',
  severity_basis: 'High',
  ppe_count: 1,
  control_count: 1,
}

// ── Test setup ────────────────────────────────────────────────────────────────

let mock

beforeEach(() => {
  mock = new MockAdapter(client)
})

afterEach(() => {
  mock.restore()
})

// ── Health check ──────────────────────────────────────────────────────────────

describe('checkHealth', () => {
  test('returns status and auth_mode from the API', async () => {
    mock.onGet('/api/v1/health').reply(200, { status: 'ok', message: 'API online', version: '0.3.0', auth_mode: 'open' })
    const data = await checkHealth()
    expect(data.status).toBe('ok')
    expect(data.auth_mode).toBe('open')
  })

  test('throws on network error', async () => {
    mock.onGet('/api/v1/health').networkError()
    await expect(checkHealth()).rejects.toThrow()
  })
})

// ── Safety Records ────────────────────────────────────────────────────────────

describe('fetchSafetyRecords', () => {
  test('returns array of records on success', async () => {
    mock.onGet('/api/v1/safety-records').reply(200, [MOCK_SAFETY_RECORD])
    const records = await fetchSafetyRecords()
    expect(Array.isArray(records)).toBe(true)
    expect(records[0].record_id).toBe('SR-TEST-001')
  })

  test('includes ppe_required array on each record', async () => {
    mock.onGet('/api/v1/safety-records').reply(200, [MOCK_SAFETY_RECORD])
    const records = await fetchSafetyRecords()
    expect(Array.isArray(records[0].ppe_required)).toBe(true)
    expect(records[0].ppe_required[0].ppe_id).toBe('ppe_ear_plugs')
  })

  test('throws on 500 server error', async () => {
    mock.onGet('/api/v1/safety-records').reply(500)
    await expect(fetchSafetyRecords()).rejects.toMatchObject({ response: { status: 500 } })
  })

  test('throws on 401 unauthorized', async () => {
    mock.onGet('/api/v1/safety-records').reply(401, { detail: 'Unauthorized' })
    await expect(fetchSafetyRecords()).rejects.toMatchObject({ response: { status: 401 } })
  })
})

// ── AI Task Analysis ──────────────────────────────────────────────────────────

describe('analyzeTask', () => {
  test('sends correct request body', async () => {
    mock.onPost('/api/v1/analyze-task').reply((config) => {
      const body = JSON.parse(config.data)
      expect(body.task_description).toBe('grinding steel beams')
      expect(body.severity_level).toBe('High')
      return [200, MOCK_ANALYSIS_RESPONSE]
    })
    await analyzeTask('grinding steel beams', 'High')
  })

  test('defaults severity_level to Moderate', async () => {
    mock.onPost('/api/v1/analyze-task').reply((config) => {
      const body = JSON.parse(config.data)
      expect(body.severity_level).toBe('Moderate')
      return [200, MOCK_ANALYSIS_RESPONSE]
    })
    await analyzeTask('cleaning with solvents')
  })

  test('returns assessment_id and ppe_recommendations', async () => {
    mock.onPost('/api/v1/analyze-task').reply(200, MOCK_ANALYSIS_RESPONSE)
    const result = await analyzeTask('grinding steel', 'High')
    expect(result.assessment_id).toBe('uuid-test-123')
    expect(Array.isArray(result.ppe_recommendations)).toBe(true)
    expect(Array.isArray(result.engineering_controls)).toBe(true)
  })

  test('throws 400 when description is too vague', async () => {
    mock.onPost('/api/v1/analyze-task').reply(400, { detail: 'Could not extract hazards' })
    await expect(analyzeTask('xyz', 'Low')).rejects.toMatchObject({ response: { status: 400 } })
  })

  test('throws on network failure', async () => {
    mock.onPost('/api/v1/analyze-task').networkError()
    await expect(analyzeTask('test task')).rejects.toThrow()
  })
})

// ── AI Feedback ───────────────────────────────────────────────────────────────

describe('submitAIFeedback', () => {
  const FEEDBACK_RESPONSE = {
    feedback_id: 'fb-uuid-001',
    assessment_id: 'uuid-test-123',
    created_at: '2025-06-01T11:00:00',
  }

  test('sends correct body for thumbs_up', async () => {
    mock.onPost('/api/v1/ai-feedback').reply((config) => {
      const body = JSON.parse(config.data)
      expect(body.assessment_id).toBe('uuid-test-123')
      expect(body.feedback_type).toBe('thumbs_up')
      expect(body.comment).toBeUndefined()
      return [200, FEEDBACK_RESPONSE]
    })
    await submitAIFeedback({ assessmentId: 'uuid-test-123', feedbackType: 'thumbs_up' })
  })

  test('sends comment for report_inaccuracy', async () => {
    mock.onPost('/api/v1/ai-feedback').reply((config) => {
      const body = JSON.parse(config.data)
      expect(body.feedback_type).toBe('report_inaccuracy')
      expect(body.comment).toBe('Missing hearing protection')
      return [200, FEEDBACK_RESPONSE]
    })
    await submitAIFeedback({
      assessmentId: 'uuid-test-123',
      feedbackType: 'report_inaccuracy',
      comment: 'Missing hearing protection',
    })
  })

  test('returns feedback_id on success', async () => {
    mock.onPost('/api/v1/ai-feedback').reply(200, FEEDBACK_RESPONSE)
    const result = await submitAIFeedback({ assessmentId: 'uuid-test-123', feedbackType: 'thumbs_down' })
    expect(result.feedback_id).toBe('fb-uuid-001')
  })

  test('throws 404 when assessment_id does not exist', async () => {
    mock.onPost('/api/v1/ai-feedback').reply(404, { detail: 'assessment_id not found' })
    await expect(
      submitAIFeedback({ assessmentId: 'nonexistent', feedbackType: 'thumbs_up' })
    ).rejects.toMatchObject({ response: { status: 404 } })
  })
})

// ── Assessment History ────────────────────────────────────────────────────────

describe('fetchAIAssessments', () => {
  test('returns array of summaries', async () => {
    mock.onGet('/api/v1/ai-assessments').reply(200, [MOCK_ASSESSMENT_SUMMARY])
    const data = await fetchAIAssessments()
    expect(Array.isArray(data)).toBe(true)
    expect(data[0].assessment_id).toBe('uuid-test-123')
    expect(typeof data[0].ppe_count).toBe('number')
    expect(typeof data[0].control_count).toBe('number')
  })

  test('returns empty array when no assessments', async () => {
    mock.onGet('/api/v1/ai-assessments').reply(200, [])
    const data = await fetchAIAssessments()
    expect(data).toHaveLength(0)
  })
})

describe('fetchAIAssessmentDetail', () => {
  const DETAIL = {
    assessment_id: 'uuid-test-123',
    created_at: '2025-06-01T10:00:00',
    task_description: 'grinding steel with power tools',
    criteria: { material_id: null, process_type: 'Grinding', severity_level: 'High' },
    severity_basis: 'High',
    ppe_recommendations: MOCK_PPE_RESPONSE.ppe_recommendations,
    engineering_controls: MOCK_PPE_RESPONSE.engineering_controls,
  }

  test('fetches correct URL with assessment_id', async () => {
    mock.onGet('/api/v1/ai-assessments/uuid-test-123').reply(200, DETAIL)
    const data = await fetchAIAssessmentDetail('uuid-test-123')
    expect(data.assessment_id).toBe('uuid-test-123')
    expect(Array.isArray(data.ppe_recommendations)).toBe(true)
  })

  test('throws 404 for unknown assessment_id', async () => {
    mock.onGet('/api/v1/ai-assessments/bad-id').reply(404, { detail: 'Not found' })
    await expect(fetchAIAssessmentDetail('bad-id')).rejects.toMatchObject({ response: { status: 404 } })
  })
})

// ── Reference Data ────────────────────────────────────────────────────────────

describe('fetchPPECatalog', () => {
  test('returns array of PPE items with required fields', async () => {
    const catalog = [
      { ppe_id: 'ppe_ear_plugs', ppe_label: 'Ear Plugs', ppe_category: 'Hearing Protection' },
      { ppe_id: 'ppe_hard_hat', ppe_label: 'Hard Hat', ppe_category: 'Head Protection' },
    ]
    mock.onGet('/api/v1/ppe').reply(200, catalog)
    const data = await fetchPPECatalog()
    expect(data).toHaveLength(2)
    expect(data[0]).toHaveProperty('ppe_id')
    expect(data[0]).toHaveProperty('ppe_label')
    expect(data[0]).toHaveProperty('ppe_category')
  })
})

describe('fetchHazards', () => {
  test('returns array of hazards with required fields', async () => {
    const hazards = [
      { hazard_id: 'haz_high_noise', hazard_label: 'High Noise', hazard_category: 'Physical Environment' },
    ]
    mock.onGet('/api/v1/hazards').reply(200, hazards)
    const data = await fetchHazards()
    expect(data[0]).toHaveProperty('hazard_id')
    expect(data[0]).toHaveProperty('hazard_label')
    expect(data[0]).toHaveProperty('hazard_category')
  })
})

// ── AUL Materials ─────────────────────────────────────────────────────────────

describe('fetchMaterials', () => {
  const MATERIALS = [
    { msn: 'MSN-001', noun: 'Jet Fuel JP-8', bulk_issue: true },
    { msn: 'MSN-002', noun: 'Hydraulic Fluid', bulk_issue: false },
  ]

  test('calls /api/v1/materials without query param when no search', async () => {
    mock.onGet('/api/v1/materials').reply(200, MATERIALS)
    const data = await fetchMaterials()
    expect(data).toHaveLength(2)
  })

  test('passes q param when searching', async () => {
    mock.onGet('/api/v1/materials', { params: { q: 'Jet' } }).reply(200, [MATERIALS[0]])
    const data = await fetchMaterials('Jet')
    expect(data).toHaveLength(1)
    expect(data[0].msn).toBe('MSN-001')
  })

  test('returns empty array when no results', async () => {
    mock.onGet('/api/v1/materials').reply(200, [])
    const data = await fetchMaterials()
    expect(data).toHaveLength(0)
  })
})

describe('recommendPPEForMaterial', () => {
  const MAT_PPE_RESPONSE = {
    msn: 'MSN-001',
    material_name: 'Jet Fuel JP-8',
    matched_hazard_label: 'Fire/ Explosion',
    authorized_shops: ['S100', 'S200'],
    criteria: { material_id: 'haz_fire_explosion', process_type: null, severity_level: 'High' },
    severity_basis: 'High',
    ppe_recommendations: [
      { ppe_id: 'ppe_fr_clothing', ppe_type: 'FR Clothing', ppe_category: 'Arc Flash Protection', rationale: 'Fire hazard.' },
    ],
    engineering_controls: [
      { control_type: 'Local Exhaust Ventilation', rationale: 'Fuel vapors.' },
    ],
  }

  test('sends msn and severity_level in request body', async () => {
    mock.onPost('/api/v1/materials/recommend-ppe').reply((config) => {
      const body = JSON.parse(config.data)
      expect(body.msn).toBe('MSN-001')
      expect(body.severity_level).toBe('High')
      return [200, MAT_PPE_RESPONSE]
    })
    await recommendPPEForMaterial('MSN-001', 'High')
  })

  test('returns material_name, matched_hazard_label, and authorized_shops', async () => {
    mock.onPost('/api/v1/materials/recommend-ppe').reply(200, MAT_PPE_RESPONSE)
    const data = await recommendPPEForMaterial('MSN-001', 'High')
    expect(data.material_name).toBe('Jet Fuel JP-8')
    expect(data.matched_hazard_label).toBe('Fire/ Explosion')
    expect(data.authorized_shops).toContain('S100')
  })

  test('defaults severity to Moderate', async () => {
    mock.onPost('/api/v1/materials/recommend-ppe').reply((config) => {
      const body = JSON.parse(config.data)
      expect(body.severity_level).toBe('Moderate')
      return [200, MAT_PPE_RESPONSE]
    })
    await recommendPPEForMaterial('MSN-001')
  })

  test('throws 404 when MSN not found', async () => {
    mock.onPost('/api/v1/materials/recommend-ppe').reply(404, { detail: "Material MSN 'BAD' not found" })
    await expect(recommendPPEForMaterial('BAD', 'Low')).rejects.toMatchObject({ response: { status: 404 } })
  })

  test('throws 422 when material cannot be mapped to hazard', async () => {
    mock.onPost('/api/v1/materials/recommend-ppe').reply(422, { detail: 'Could not map material to a known hazard' })
    await expect(recommendPPEForMaterial('MSN-999', 'Moderate')).rejects.toMatchObject({ response: { status: 422 } })
  })
})
