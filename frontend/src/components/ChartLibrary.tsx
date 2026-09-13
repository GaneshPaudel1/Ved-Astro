import { useEffect, useRef, useState } from 'react'
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

export function ChartLibrary({ accountEmail, charts, activeId, busy, onNew, onLoad, onRename, onRemove }: {
  accountEmail?: string; charts: SavedChart[]; activeId: string | null; busy: boolean
  onNew: () => void; onLoad: (chart: SavedChart) => void
  onRename: (id: string, name: string) => void; onRemove: (id: string) => Promise<boolean>
}) {
  const [query, setQuery] = useState('')
  const [editing, setEditing] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [deleting, setDeleting] = useState<SavedChart | null>(null)
  const [deleteError, setDeleteError] = useState('')
  const dialog = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    if (deleting && !dialog.current?.open) dialog.current?.showModal()
    else if (!deleting) dialog.current?.close()
  }, [deleting])
  const filtered = charts.filter(c => `${c.birth.name} ${c.birth.place} ${c.birth.date}`.toLowerCase().includes(query.toLowerCase()))
  return <section className="chart-library wrap no-print" id="chart-library" aria-labelledby="library-title">
    <div className="library-heading">
      <div><p className="eyebrow">A constellation of your people</p><h2 id="library-title">My chart collection <span>{charts.length}</span></h2><p className="small muted">{accountEmail ? `Saved to ${accountEmail}. Sign in on another device to open your charts.` : 'Sign in with Google to create charts and save them across devices. Existing browser charts remain available below.'}</p></div>
      <button className="btn btn--primary" onClick={onNew} disabled={busy}>＋ New chart</button>
    </div>
    {charts.length > 0 && <div className="library-search"><label htmlFor="chart-search" className="sr-only">Search saved charts</label><input id="chart-search" type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search by name, place, or birth date…" /></div>}
    <div className="library-grid">
      {filtered.map((chart, i) => <article key={chart.id} className={`saved-chart saved-chart--${i % 3}${activeId === chart.id ? ' is-active' : ''}`}>
        <div className="saved-chart__top"><span className="saved-chart__avatar" aria-hidden="true">{chart.birth.name.charAt(0).toUpperCase() || '✦'}</span><span className="saved-chart__badge">{activeId === chart.id ? 'Last opened' : 'Saved chart'}</span></div>
        {editing === chart.id ? <form className="saved-chart__rename" onSubmit={e => { e.preventDefault(); if (name.trim()) { onRename(chart.id, name.trim()); setEditing(null) } }}>
          <label htmlFor={`rename-${chart.id}`}>Chart name</label><input id={`rename-${chart.id}`} value={name} onChange={e => setName(e.target.value)} maxLength={80} autoFocus required />
          <div className="cluster"><button className="btn btn--sm" disabled={busy || !name.trim()}>Save name</button><button type="button" className="btn btn--ghost btn--sm" onClick={() => setEditing(null)}>Cancel</button></div>
        </form> : <><h3>{chart.birth.name || 'Untitled chart'}</h3><p className="saved-chart__birth">{chart.birth.date} · {chart.birth.time?.slice(0, 5) || 'Time unknown'}</p><p className="saved-chart__place">{chart.birth.place}</p><div className="saved-chart__signs"><span>☾ {chart.bundle.chart.planets.Moon.sign_name}</span><span>✧ {chart.bundle.chart.ascendant_sign_name || 'Time unknown'}</span></div>
          <div className="saved-chart__actions"><button className="btn btn--sm" onClick={() => onLoad(chart)} disabled={busy} aria-label={`Load ${chart.birth.name}`}>Open & edit ↗</button><button className="btn btn--ghost btn--sm" disabled={busy} onClick={() => { setEditing(chart.id); setName(chart.birth.name) }} aria-label={`Rename ${chart.birth.name}`}>Rename</button><button className="btn btn--ghost btn--sm" disabled={busy} onClick={() => { setDeleteError(''); setDeleting(chart) }} aria-label={`Remove ${chart.birth.name}`}>×</button></div></>}
      </article>)}
      {!charts.length && <div className="library-empty"><span aria-hidden="true">✧</span><div><h3>Your people, written in the stars.</h3><p><strong>{accountEmail ? 'Create your first birth chart.' : 'Sign in with Google to create a birth chart.'}</strong> Keep your own chart and those of the people you love in one place.</p><p className="tiny dim">{accountEmail ? 'New charts save to your account. Use Import browser charts to copy an existing local collection.' : 'Already have browser charts? Sign in, then choose Import browser charts to keep them in your account.'}</p></div></div>}
      {charts.length > 0 && !filtered.length && <p className="muted">No charts match “{query}”. Try another name or place.</p>}
    </div>
    <dialog ref={dialog} className="delete-dialog" aria-labelledby="delete-title" aria-describedby="delete-description" onCancel={e => { if (busy) e.preventDefault(); else setDeleting(null) }}>
      <p className="eyebrow">YOUR CHART COLLECTION</p><h2 id="delete-title">Remove this chart?</h2>
      <p id="delete-description">“{deleting?.birth.name}” will be removed from {accountEmail ? 'your account on all devices' : 'this browser’s collection'}. You can keep it by choosing Cancel.</p>
      {deleteError && <p role="alert">{deleteError}</p>}
      <div className="cluster"><button className="btn" autoFocus disabled={busy} onClick={() => setDeleting(null)}>Cancel</button><button className="btn btn--danger" disabled={busy} onClick={async () => { if (deleting && await onRemove(deleting.id)) setDeleting(null); else setDeleteError('Could not remove this chart. Close this dialog and check the collection status before retrying.') }}>{busy ? 'Removing…' : 'Remove chart'}</button></div>
    </dialog>
  </section>
}
