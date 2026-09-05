import { useState } from 'react'
import type { BirthInput, Bundle } from '../api/types'

export interface SavedChart {
  id: string
  birth: BirthInput
  bundle: Bundle
  savedAt: string
}
const STORAGE_KEY = 'jyotish_chart_library_v1'

export function readLibrary(): { charts: SavedChart[]; error: string | null } {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { charts: [], error: null }
    const data = JSON.parse(raw)
    if (!Array.isArray(data) || !data.every(c => typeof c.id === 'string' && typeof c.birth?.name === 'string' && typeof c.birth?.date === 'string' && c.bundle?.chart?.planets?.Sun && c.bundle?.chart?.planets?.Moon && Array.isArray(c.bundle?.chart?.warnings))) throw new Error('Invalid library')
    return { charts: data, error: null }
  } catch {
    return { charts: [], error: 'Your saved charts could not be read. Existing browser data has not been overwritten.' }
  }
}

export function writeLibrary(charts: SavedChart[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(charts))
}

export function ChartLibrary({ charts, activeId, busy, onNew, onLoad, onRename, onRemove }: {
  charts: SavedChart[]; activeId: string | null; busy: boolean
  onNew: () => void; onLoad: (chart: SavedChart) => void
  onRename: (id: string, name: string) => void; onRemove: (id: string) => void
}) {
  const [query, setQuery] = useState('')
  const [editing, setEditing] = useState<string | null>(null)
  const [name, setName] = useState('')
  const filtered = charts.filter(c => `${c.birth.name} ${c.birth.place} ${c.birth.date}`.toLowerCase().includes(query.toLowerCase()))
  return <section className="chart-library wrap no-print" id="chart-library" aria-labelledby="library-title">
    <div className="library-heading">
      <div><p className="eyebrow">A constellation of your people</p><h2 id="library-title">My chart collection <span>{charts.length}</span></h2><p className="small muted">Saved on this browser. Return to any chart, whenever you like.</p></div>
      <button className="btn btn--primary" onClick={onNew} disabled={busy}>＋ New chart</button>
    </div>
    {charts.length > 0 && <div className="library-search"><label htmlFor="chart-search" className="sr-only">Search saved charts</label><input id="chart-search" type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search by name, place, or birth date…" /></div>}
    <div className="library-grid">
      {filtered.map((chart, i) => <article key={chart.id} className={`saved-chart saved-chart--${i % 3}${activeId === chart.id ? ' is-active' : ''}`}>
        <div className="saved-chart__top"><span className="saved-chart__avatar" aria-hidden="true">{chart.birth.name.charAt(0).toUpperCase() || '✦'}</span><span className="saved-chart__badge">{activeId === chart.id ? 'Viewing now' : 'Saved chart'}</span></div>
        {editing === chart.id ? <form className="saved-chart__rename" onSubmit={e => { e.preventDefault(); if (name.trim()) { onRename(chart.id, name.trim()); setEditing(null) } }}>
          <label htmlFor={`rename-${chart.id}`}>Chart name</label><input id={`rename-${chart.id}`} value={name} onChange={e => setName(e.target.value)} maxLength={80} autoFocus required />
          <div className="cluster"><button className="btn btn--sm" disabled={busy || !name.trim()}>Save name</button><button type="button" className="btn btn--ghost btn--sm" onClick={() => setEditing(null)}>Cancel</button></div>
        </form> : <><h3>{chart.birth.name || 'Untitled chart'}</h3><p className="saved-chart__birth">{chart.birth.date} · {chart.birth.time?.slice(0, 5) || 'Time unknown'}</p><p className="saved-chart__place">{chart.birth.place}</p><div className="saved-chart__signs"><span>☾ {chart.bundle.chart.planets.Moon.sign_name}</span><span>✧ {chart.bundle.chart.ascendant_sign_name || 'Time unknown'}</span></div>
          <div className="saved-chart__actions"><button className="btn btn--sm" onClick={() => onLoad(chart)} disabled={busy} aria-label={`Load ${chart.birth.name}`}>Open chart ↗</button><button className="btn btn--ghost btn--sm" disabled={busy} onClick={() => { setEditing(chart.id); setName(chart.birth.name) }} aria-label={`Rename ${chart.birth.name}`}>Rename</button><button className="btn btn--ghost btn--sm" disabled={busy} onClick={() => onRemove(chart.id)} aria-label={`Remove ${chart.birth.name}`}>×</button></div></>}
      </article>)}
      {!charts.length && <div className="library-empty"><span aria-hidden="true">✧</span><div><h3>Your people, written in the stars.</h3><p>Create a chart for yourself, a friend, or family. Each chart you reveal is saved here automatically.</p><p className="tiny dim">Local storage only — no account or cloud sync. Clearing browser data removes this collection.</p></div></div>}
      {charts.length > 0 && !filtered.length && <p className="muted">No charts match “{query}”. Try another name or place.</p>}
    </div>
  </section>
}
