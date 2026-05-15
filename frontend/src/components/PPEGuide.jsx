/**
 * PPEGuide.jsx — PPE Catalog, Hazard Reference & AUL Materials
 *
 * Three tabs:
 *   1. PPE Catalog  — all ppe rows from GET /api/v1/ppe, grouped by category + searchable
 *   2. Hazard Reference — all hazards from GET /api/v1/hazards, grouped by category + searchable
 *   3. AUL Materials — materials + shop authorizations from GET /api/v1/materials
 */

import { useState, useEffect, useMemo } from 'react'
import {
  fetchPPECatalog,
  fetchHazards,
  fetchMaterials,
  fetchMaterialAuthorizations,
  recommendPPEForMaterial,
} from '../api/hazmat'
import './PPEGuide.css'

const PPE_CATEGORY_ICON = {
  'Eye/Face Protection': '👁',
  'Hearing Protection': '🔇',
  'Hand Protection': '🧤',
  'Foot Protection': '🥾',
  'Head Protection': '⛑',
  'Respiratory Protection': '😷',
  'Arc Flash Protection': '⚡',
  'Fall Protection': '🪢',
}

// ─── PPE Catalog Tab ──────────────────────────────────────────────────────────

function PPECatalogTab({ items }) {
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    if (!search.trim()) return items
    const q = search.toLowerCase()
    return items.filter(
      (p) => p.ppe_label.toLowerCase().includes(q) || p.ppe_category.toLowerCase().includes(q)
    )
  }, [items, search])

  const byCategory = useMemo(() => {
    const map = {}
    filtered.forEach((p) => {
      ;(map[p.ppe_category] = map[p.ppe_category] || []).push(p)
    })
    return map
  }, [filtered])

  return (
    <div className="tab-content">
      <input
        type="text"
        className="guide-search"
        placeholder="Search PPE items or categories…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <p className="guide-count">{filtered.length} item{filtered.length !== 1 ? 's' : ''}</p>

      {Object.entries(byCategory).map(([cat, catItems]) => (
        <div key={cat} className="guide-category-block">
          <div className="guide-category-header">
            <span className="guide-category-icon">{PPE_CATEGORY_ICON[cat] || '🛡'}</span>
            <span className="guide-category-name">{cat}</span>
            <span className="guide-category-count">{catItems.length}</span>
          </div>
          <div className="guide-item-grid">
            {catItems.map((p) => (
              <div key={p.ppe_id} className="guide-item-card">
                <span className="guide-item-id">{p.ppe_id}</span>
                <span className="guide-item-label">{p.ppe_label}</span>
              </div>
            ))}
          </div>
        </div>
      ))}

      {filtered.length === 0 && (
        <div className="guide-empty">No PPE items match your search.</div>
      )}
    </div>
  )
}

// ─── Hazard Reference Tab ─────────────────────────────────────────────────────

function HazardReferenceTab({ hazards }) {
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    if (!search.trim()) return hazards
    const q = search.toLowerCase()
    return hazards.filter(
      (h) => h.hazard_label.toLowerCase().includes(q) || h.hazard_category.toLowerCase().includes(q)
    )
  }, [hazards, search])

  const byCategory = useMemo(() => {
    const map = {}
    filtered.forEach((h) => {
      ;(map[h.hazard_category] = map[h.hazard_category] || []).push(h)
    })
    return map
  }, [filtered])

  return (
    <div className="tab-content">
      <input
        type="text"
        className="guide-search"
        placeholder="Search hazards or categories…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <p className="guide-count">{filtered.length} hazard{filtered.length !== 1 ? 's' : ''}</p>

      {Object.entries(byCategory).map(([cat, catHazards]) => (
        <div key={cat} className="guide-category-block">
          <div className="guide-category-header">
            <span className="guide-category-icon">⚠</span>
            <span className="guide-category-name">{cat}</span>
            <span className="guide-category-count">{catHazards.length}</span>
          </div>
          <div className="guide-item-grid">
            {catHazards.map((h) => (
              <div key={h.hazard_id} className="guide-item-card hazard-card-item">
                <span className="guide-item-id">{h.hazard_id}</span>
                <span className="guide-item-label">{h.hazard_label}</span>
              </div>
            ))}
          </div>
        </div>
      ))}

      {filtered.length === 0 && (
        <div className="guide-empty">No hazards match your search.</div>
      )}
    </div>
  )
}

// ─── AUL Materials Tab ────────────────────────────────────────────────────────

function AULMaterialsTab() {
  const [materials, setMaterials] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')

  const [shopCode, setShopCode] = useState('')
  const [shopCodeInput, setShopCodeInput] = useState('')

  const [expanded, setExpanded] = useState(null)
  const [auths, setAuths] = useState([])
  const [authsLoading, setAuthsLoading] = useState(false)

  const [ppeRec, setPpeRec] = useState(null)
  const [ppeRecLoading, setPpeRecLoading] = useState(false)
  const [ppeRecError, setPpeRecError] = useState(null)
  const [ppeRecMsn, setPpeRecMsn] = useState(null)
  const [ppeRecSeverity, setPpeRecSeverity] = useState('Moderate')

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetchMaterials(search, shopCode)
      .then((data) => { setMaterials(data); setLoading(false) })
      .catch(() => { setError('Could not load AUL materials.'); setLoading(false) })
  }, [search, shopCode])

  const handleSearch = (e) => {
    e.preventDefault()
    setSearch(searchInput)
    setShopCode(shopCodeInput.trim().toUpperCase())
    setExpanded(null)
  }

  const handleClearShop = () => {
    setShopCodeInput('')
    setShopCode('')
    setExpanded(null)
  }

  const handleExpand = async (msn) => {
    if (expanded === msn) { setExpanded(null); return }
    setExpanded(msn)
    setPpeRec(null)
    setPpeRecError(null)
    setPpeRecMsn(null)
    setAuthsLoading(true)
    try {
      const data = await fetchMaterialAuthorizations(msn)
      setAuths(data)
    } catch {
      setAuths([])
    }
    setAuthsLoading(false)
  }

  const handleGetPPERec = async (msn) => {
    setPpeRecLoading(true)
    setPpeRec(null)
    setPpeRecError(null)
    setPpeRecMsn(msn)
    try {
      const data = await recommendPPEForMaterial(msn, ppeRecSeverity)
      setPpeRec(data)
    } catch (err) {
      setPpeRecError(err.response?.data?.detail || 'Could not generate PPE recommendation for this material.')
    }
    setPpeRecLoading(false)
  }

  return (
    <div className="tab-content">
      <form className="materials-search-form" onSubmit={handleSearch}>
        <div className="materials-search-row">
          <input
            type="text"
            className="guide-search"
            placeholder="Search by material name or MSN…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          <div className="shop-code-search-group">
            <span className="shop-code-search-icon">🏭</span>
            <input
              type="text"
              className="guide-search shop-code-input"
              placeholder="Filter by shop code (e.g. 553)"
              value={shopCodeInput}
              onChange={(e) => setShopCodeInput(e.target.value.toUpperCase())}
              maxLength={10}
              id="shop-code-filter-input"
            />
            {shopCode && (
              <button
                type="button"
                className="shop-code-clear-btn"
                onClick={handleClearShop}
                title="Clear shop code filter"
                aria-label="Clear shop code filter"
              >
                ✕
              </button>
            )}
          </div>
          <button type="submit" className="search-btn">Search</button>
        </div>

        {shopCode && (
          <div className="active-shop-filter">
            <span className="active-filter-badge">
              🏭 Shop: <strong>{shopCode}</strong>
            </span>
            <span className="active-filter-hint">Showing materials authorized for this shop</span>
          </div>
        )}
      </form>

      {loading && (
        <div className="guide-loading">
          <span className="loading-spinner" />Loading AUL materials…
        </div>
      )}

      {error && <div className="guide-error">{error}</div>}

      {!loading && !error && materials.length === 0 && (
        <div className="guide-empty">
          {search || shopCode
            ? `No materials match your search${shopCode ? ` for shop "${shopCode}"` : ''}.`
            : 'No AUL data available. Import the CSV to populate this section.'}
        </div>
      )}

      {!loading && !error && materials.length > 0 && (
        <>
          <p className="guide-count">{materials.length} material{materials.length !== 1 ? 's' : ''}{materials.length === 200 ? ' (capped at 200 — use search to narrow)' : ''}</p>
          <div className="materials-table">
            <div className="mat-table-header">
              <span>MSN</span>
              <span>Material Name</span>
              <span>Bulk Issue</span>
              <span></span>
            </div>
            {materials.map((m) => (
              <div key={m.msn} className="mat-row-group">
                <div
                  className={`mat-row ${expanded === m.msn ? 'expanded' : ''}`}
                  onClick={() => handleExpand(m.msn)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && handleExpand(m.msn)}
                >
                  <span className="mat-msn">{m.msn}</span>
                  <span className="mat-noun">{m.noun}</span>
                  <span className={`mat-bulk ${m.bulk_issue ? 'yes' : 'no'}`}>
                    {m.bulk_issue ? 'Yes' : 'No'}
                  </span>
                  <span className="mat-expand">{expanded === m.msn ? '▲' : '▼'}</span>
                </div>

                {expanded === m.msn && (
                  <div className="mat-auths">
                    {/* PPE Recommendation row */}
                    <div className="mat-ppe-rec-bar">
                      <span className="mat-ppe-rec-label">PPE Recommendation for this material:</span>
                      <select
                        className="mat-severity-select"
                        value={ppeRecSeverity}
                        onChange={(e) => setPpeRecSeverity(e.target.value)}
                        aria-label="Severity level for PPE recommendation"
                      >
                        {['Low', 'Moderate', 'High', 'Severe'].map((s) => <option key={s}>{s}</option>)}
                      </select>
                      <button
                        className="mat-ppe-btn"
                        onClick={() => handleGetPPERec(m.msn)}
                        disabled={ppeRecLoading && ppeRecMsn === m.msn}
                      >
                        {ppeRecLoading && ppeRecMsn === m.msn ? 'Loading…' : 'Recommend PPE →'}
                      </button>
                    </div>

                    {ppeRecError && ppeRecMsn === m.msn && (
                      <p className="mat-ppe-error">{ppeRecError}</p>
                    )}

                    {ppeRec && ppeRecMsn === m.msn && (
                      <div className="mat-ppe-result">
                        <div className="mat-ppe-result-header">
                          <span>Matched hazard: <strong>{ppeRec.matched_hazard_label || 'N/A'}</strong></span>
                          <span className="mat-severity-basis">Severity: <strong>{ppeRec.severity_basis}</strong></span>
                          {ppeRec.authorized_shops.length > 0 && (
                            <span>Authorized shops:{ppeRec.authorized_shops.map(s => (
                              <span key={s} className="shop-code-tag" style={{marginLeft: 4}}>{s}</span>
                            ))}</span>
                          )}
                        </div>
                        <div className="mat-ppe-cols">
                          <div>
                            <h5>Required PPE</h5>
                            {ppeRec.ppe_recommendations.length === 0
                              ? <p className="auth-empty">No specific PPE required.</p>
                              : <ul className="mat-ppe-list">
                                  {ppeRec.ppe_recommendations.map(p => (
                                    <li key={p.ppe_id}><strong>{p.ppe_type}</strong> <span className="mat-ppe-cat">({p.ppe_category})</span></li>
                                  ))}
                                </ul>
                            }
                          </div>
                          <div>
                            <h5>Engineering Controls</h5>
                            {ppeRec.engineering_controls.length === 0
                              ? <p className="auth-empty">No specific controls required.</p>
                              : <ul className="mat-ppe-list">
                                  {ppeRec.engineering_controls.map(c => (
                                    <li key={c.control_type} className={c.source === 'TINKER' ? 'tinker-control-item' : ''}>
                                      <div className="control-header">
                                        <strong>{c.control_type}</strong>
                                        {c.source === 'TINKER' && (
                                          <span className="tinker-badge" title="Required by Tinker AFB Risk Assessment Form">TINKER AFB FORM</span>
                                        )}
                                      </div>
                                      {c.rationale && <p className="auth-empty" style={{marginTop:'0.3rem',marginBottom:0}}>{c.rationale}</p>}
                                    </li>
                                  ))}
                                </ul>
                            }
                          </div>
                        </div>
                      </div>
                    )}

                    {authsLoading && (
                      <div className="auth-loading">
                        <span className="loading-spinner" />Loading authorizations…
                      </div>
                    )}
                    {!authsLoading && auths.length === 0 && (
                      <p className="auth-empty">No shop authorizations found for this material.</p>
                    )}
                    {!authsLoading && auths.length > 0 && (
                      <table className="auth-table">
                        <thead>
                          <tr>
                            <th>Shop Code</th>
                            <th>Process</th>
                            <th>Local Process</th>
                            <th>Dist %</th>
                            <th>Max On Hand</th>
                          </tr>
                        </thead>
                        <tbody>
                          {auths.map((a) => (
                            <tr key={a.id}>
                              <td><span className={`shop-code-tag${shopCode && a.shop_code === shopCode ? ' highlighted' : ''}`}>{a.shop_code}</span></td>
                              <td>{a.process_name || '—'}</td>
                              <td>{a.local_process_name || '—'}</td>
                              <td>{a.dist_pct != null ? `${a.dist_pct}%` : '—'}</td>
                              <td>{a.max_on_hand ?? '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function PPEGuide() {
  const [activeTab, setActiveTab] = useState('ppe')

  const [ppeItems, setPpeItems] = useState([])
  const [hazards, setHazards] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([fetchPPECatalog(), fetchHazards()])
      .then(([p, h]) => { setPpeItems(p); setHazards(h); setLoading(false) })
      .catch((err) => {
        const detail = err?.response?.data?.detail || err?.message || 'unknown error'
        setError(`Could not load reference data: ${detail}`)
        setLoading(false)
      })
  }, [])

  return (
    <div className="ppe-guide-page">
      <div className="ppe-guide-header">
        <h2>PPE & Reference Guide</h2>
        <p>Personal protective equipment catalog, hazard taxonomy, and AUL material authorizations.</p>
      </div>

      <div className="guide-tabs">
        {[
          { id: 'ppe', label: 'PPE Catalog' },
          { id: 'hazards', label: 'Hazard Reference' },
          { id: 'materials', label: 'AUL Materials' },
        ].map((tab) => (
          <button
            key={tab.id}
            className={`guide-tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading && (
        <div className="guide-loading">
          <span className="loading-spinner" />Loading reference data…
        </div>
      )}

      {error && <div className="guide-error">{error}</div>}

      {!loading && !error && activeTab === 'ppe' && <PPECatalogTab items={ppeItems} />}
      {!loading && !error && activeTab === 'hazards' && <HazardReferenceTab hazards={hazards} />}
      {activeTab === 'materials' && <AULMaterialsTab />}
    </div>
  )
}
