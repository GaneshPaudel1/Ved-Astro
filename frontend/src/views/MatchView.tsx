import { useState } from 'react'
import { api, ApiError } from '../api/client'
import { BirthForm } from '../components/BirthForm'
import type { BirthInput, MatchResult, Reference } from '../api/types'
import './views.css'

export function MatchView({
  primary, reference,
}: {
  primary: BirthInput
  reference: Reference | null
}) {
  const [a, setA] = useState<BirthInput>({ ...primary, name: primary.name || 'First person' })
  const [b, setB] = useState<BirthInput>({
    ...primary,
    name: 'Second person',
    date: '1992-11-17',
    time: '04:15:00',
    place: 'Mumbai, Maharashtra, India',
    latitude: 19.076,
    longitude: 72.8777,
  })
  const [result, setResult] = useState<MatchResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState<'a' | 'b' | null>(null)

  const run = async () => {
    setBusy(true)
    setError(null)
    try {
      setResult(await api.match(a, b, a.ayanamsa))
      setEditing(null)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not compute the match.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="stack-lg">
      <section>
        <h3 className="section__title">Kundli Milan — Ashtakoot Guna Milan</h3>
        <p className="section__note">
          Eight kootas weighted one through eight, thirty-six points in total.
          Every one of them is computed from the two Moons alone, which is why
          this works even when a birth time is unknown.
        </p>

        <div className="grid2" style={{ gridTemplateColumns: '1fr 1fr' }}>
          <PersonCard
            label="First person"
            person={a}
            open={editing === 'a'}
            onToggle={() => setEditing(editing === 'a' ? null : 'a')}
            onChange={setA}
            onSubmit={run}
            reference={reference}
            busy={busy}
          />
          <PersonCard
            label="Second person"
            person={b}
            open={editing === 'b'}
            onToggle={() => setEditing(editing === 'b' ? null : 'b')}
            onChange={setB}
            onSubmit={run}
            reference={reference}
            busy={busy}
          />
        </div>

        <button className="btn btn--primary" onClick={run} disabled={busy} style={{ marginTop: 'var(--s4)' }}>
          {busy ? <><span className="spin" /> Matching…</> : 'Compare charts'}
        </button>

        {error && (
          <div className="notice notice--warn" style={{ marginTop: 'var(--s4)' }}>
            <span className="notice__mark">!</span><span>{error}</span>
          </div>
        )}
      </section>

      {result && (
        <>
          <section className="card">
            <div className="score-hero">
              <div>
                <p className="eyebrow">Total</p>
                <div className="score-hero__number" style={{ color: bandColor(result.band) }}>
                  {result.total}
                  <span className="score-hero__of"> / 36</span>
                </div>
                <span className={`pill ${bandPill(result.band)}`}>{result.band}</span>
              </div>
              <div style={{ flex: 1, minWidth: 240 }}>
                <p style={{ marginBottom: 'var(--s3)' }}>{result.summary}</p>
                <div className="progress" style={{ height: 8 }}>
                  <div
                    className="progress__fill"
                    style={{ width: `${result.percent}%`, background: bandColor(result.band) }}
                  />
                </div>
              </div>
            </div>

            {result.time_note && (
              <div className="notice notice--warn" style={{ marginTop: 'var(--s4)' }}>
                <span className="notice__mark">!</span><span>{result.time_note}</span>
              </div>
            )}
          </section>

          <section>
            <h3 className="section__title">The eight kootas</h3>
            <div className="card">
              {result.kootas.map((k) => (
                <div className="koota" key={k.koota}>
                  <span className="koota__name">
                    {k.koota}
                    <span className="sanskrit small"> · {k.sanskrit}</span>
                  </span>
                  <span className="koota__score" style={{ color: kootaColor(k.score, k.max) }}>
                    {k.score}<span className="dim">/{k.max}</span>
                  </span>
                  <div className="koota__bar">
                    <div
                      className="koota__fill"
                      style={{
                        width: `${(k.score / k.max) * 100}%`,
                        background: kootaColor(k.score, k.max),
                      }}
                    />
                  </div>
                  <p className="koota__why">{k.explanation}</p>
                  {k.detail && <p className="koota__detail">{k.detail}</p>}
                  {k.cancellations && k.cancellations.length > 0 && (
                    <ul className="koota__detail" style={{ paddingLeft: '1.1rem', color: 'var(--positive)' }}>
                      {k.cancellations.map((c, i) => <li key={i}>{c}</li>)}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </section>

          <section>
            <h3 className="section__title">Manglik cross-check</h3>
            <div className={`yoga yoga--${result.manglik.verdict === 'mismatched' ? 'caution' : 'moderate'}`}>
              <div className="yoga__head">
                <span className="yoga__name">Manglik status</span>
                <span className={`pill ${
                  result.manglik.verdict === 'clear' ? 'pill--positive'
                  : result.manglik.verdict === 'balanced' ? 'pill--info' : 'pill--caution'}`}>
                  {result.manglik.verdict}
                </span>
              </div>
              <p className="yoga__summary">{result.manglik.note}</p>
              <div className="row row--2">
                {(['first', 'second'] as const).map((side) => (
                  <div key={side}>
                    <p className="eyebrow">{side === 'first' ? a.name : b.name}</p>
                    <p className="small muted" style={{ margin: 0 }}>
                      {result.manglik[side].present ? 'Manglik' : 'Not Manglik'}
                      {result.manglik[side].severity && ` · ${result.manglik[side].severity}`}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section>
            <h3 className="section__title">Both charts</h3>
            <div className="card card--flush">
              <div className="scroll-x">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Person</th><th>Moon sign</th><th>Nakshatra</th>
                      <th className="num">Pada</th><th>Gana</th><th>Nadi</th>
                      <th>Yoni</th><th>Varna</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(result.people).map(([label, p]: [string, any]) => (
                      <tr key={label} style={{ cursor: 'default' }}>
                        <td>{label}</td>
                        <td>{p.moon_sign}</td>
                        <td>{p.nakshatra}</td>
                        <td className="num">{p.pada}</td>
                        <td>{p.gana}</td>
                        <td>{p.nadi}</td>
                        <td>{p.yoni}</td>
                        <td>{p.varna}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          <div className="notice notice--info">
            <span className="notice__mark" style={{ color: 'var(--info)' }}>i</span>
            <span>{result.caveat}</span>
          </div>
        </>
      )}
    </div>
  )
}

function PersonCard({
  label, person, open, onToggle, onChange, onSubmit, reference, busy,
}: any) {
  return (
    <div className="card">
      <div className="between" style={{ marginBottom: open ? 'var(--s4)' : 0 }}>
        <div>
          <p className="eyebrow">{label}</p>
          <p style={{ margin: 0, fontWeight: 600 }}>{person.name || '—'}</p>
          <p className="tiny dim" style={{ margin: 0 }}>
            <span className="mono">{person.date}</span>
            {person.time ? <> · <span className="mono">{person.time.slice(0, 5)}</span></> : ' · time unknown'}
            {person.place && <> · {person.place}</>}
          </p>
        </div>
        <button className="btn btn--ghost btn--sm" onClick={onToggle} aria-expanded={open}>
          {open ? 'Done' : 'Edit'}
        </button>
      </div>

      {open && (
        <BirthForm
          value={person}
          onChange={onChange}
          onSubmit={onSubmit}
          reference={reference}
          busy={busy}
          compact
          submitLabel="Compare charts"
        />
      )}
    </div>
  )
}

function bandColor(band: string): string {
  if (band === 'excellent' || band === 'very good') return 'var(--positive)'
  if (band === 'acceptable') return 'var(--accent-bright)'
  if (band === 'marginal') return 'var(--caution)'
  return 'var(--negative)'
}

function bandPill(band: string): string {
  if (band === 'excellent' || band === 'very good') return 'pill--positive'
  if (band === 'acceptable') return 'pill--own'
  if (band === 'marginal') return 'pill--caution'
  return 'pill--negative'
}

function kootaColor(score: number, max: number): string {
  const r = score / max
  if (r >= 0.99) return 'var(--positive)'
  if (r >= 0.66) return 'var(--accent-bright)'
  if (r >= 0.34) return 'var(--caution)'
  if (r > 0) return 'var(--caution)'
  return 'var(--negative)'
}
