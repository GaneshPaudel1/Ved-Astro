import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import type { BirthInput, Bundle, DashaPeriod, DashaTree } from '../api/types'
import './views.css'

const LORD_HUE: Record<string, number> = {
  Sun: 32, Moon: 205, Mars: 8, Mercury: 140, Jupiter: 45,
  Venus: 320, Saturn: 250, Rahu: 275, Ketu: 18,
}

function lordColor(lord: string, alpha = 1): string {
  const h = LORD_HUE[lord] ?? 210
  return `hsl(${h} 45% 52% / ${alpha})`
}

export function DashaView({ bundle, birth }: { bundle: Bundle; birth: BirthInput }) {
  const [system, setSystem] = useState<'vimshottari' | 'yogini' | 'ashtottari'>('vimshottari')
  const [tree, setTree] = useState<DashaTree | null>(bundle.dasha ?? null)
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (system === 'vimshottari') {
      setTree(bundle.dasha ?? null)
      return
    }
    const alt = bundle.dasha_alternates
    if (alt && system === 'yogini') return setTree(alt.yogini)
    if (alt && system === 'ashtottari') return setTree(alt.ashtottari)
    setLoading(true)
    api.dasha({ ...birth, system })
      .then(setTree)
      .finally(() => setLoading(false))
  }, [system, bundle, birth])

  const path = bundle.dasha_path ?? []
  const today = new Date().toISOString().slice(0, 10)

  const span = useMemo(() => {
    if (!tree?.periods.length) return null
    return {
      start: tree.periods[0].start_jd,
      end: tree.periods[tree.periods.length - 1].end_jd,
    }
  }, [tree])

  const toggle = (id: string) =>
    setOpen((s) => {
      const n = new Set(s)
      n.has(id) ? n.delete(id) : n.add(id)
      return n
    })

  return (
    <div className="stack-lg">
      {/* ---- what is running now ---- */}
      {path.length > 0 && (
        <section>
          <h3 className="section__title">Running now</h3>
          <p className="section__note">
            Five nested levels. Each divides its parent in the same proportion —
            a lord&rsquo;s share of 120 years — so the sub-period colours the
            larger one rather than replacing it.
          </p>
          <div className="dasha-now">
            {path.map((p, i) => (
              <div key={p.level} className={`dasha-now__cell${i === 0 ? ' is-lead' : ''}`}>
                <div className="dasha-now__level">{p.level_name}</div>
                <div className="dasha-now__lord" style={{ color: lordColor(p.lord) }}>
                  {p.lord}
                </div>
                <div className="dasha-now__dates">
                  {p.start} → {p.end}
                </div>
                <div className="progress" style={{ marginTop: 6 }}>
                  <div className="progress__fill" style={{ width: `${p.elapsed_percent}%` }} />
                </div>
                <div className="tiny dim" style={{ marginTop: 2 }}>
                  {p.elapsed_percent.toFixed(0)}% elapsed · {p.remaining} left
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ---- system switch ---- */}
      <section>
        <div className="section__head">
          <span className="section__title">Timeline</span>
          <div className="segmented" role="group" aria-label="Dasha system">
            <button aria-pressed={system === 'vimshottari'} onClick={() => setSystem('vimshottari')}>
              Vimshottari
            </button>
            <button aria-pressed={system === 'yogini'} onClick={() => setSystem('yogini')}>
              Yogini
            </button>
            <button aria-pressed={system === 'ashtottari'} onClick={() => setSystem('ashtottari')}>
              Ashtottari
            </button>
          </div>
        </div>

        {loading && <p className="muted small"><span className="spin" /> Loading…</p>}

        {tree && (
          <>
            <div className="stat-strip" style={{ marginBottom: 'var(--s4)' }}>
              <div className="stat">
                <div className="stat__label">Cycle</div>
                <div className="stat__value">{tree.total_years} years</div>
              </div>
              <div className="stat">
                <div className="stat__label">Birth star</div>
                <div className="stat__value" style={{ fontSize: '0.95rem' }}>
                  {tree.birth_nakshatra}
                </div>
              </div>
              <div className="stat">
                <div className="stat__label">First lord</div>
                <div className="stat__value" style={{ color: lordColor(tree.starting_lord) }}>
                  {tree.starting_lord}
                </div>
              </div>
              <div className="stat">
                <div className="stat__label">Balance at birth</div>
                <div className="stat__value" style={{ fontSize: '0.95rem' }}>
                  {tree.balance_at_birth.readable}
                </div>
              </div>
            </div>

            {/* proportional bar */}
            {span && (
              <div className="dasha-bar" role="img" aria-label="Full dasha cycle">
                {tree.periods.map((p) => {
                  const width = ((p.end_jd - p.start_jd) / (span.end - span.start)) * 100
                  return (
                    <button
                      key={`${p.lord}-${p.start_jd}`}
                      className={`dasha-bar__seg${p.current ? ' is-current' : ''}`}
                      style={{ width: `${width}%`, background: lordColor(p.lord, 0.85) }}
                      title={`${p.lord}: ${p.start} → ${p.end}`}
                      onClick={() => toggle(`${p.lord}-${p.start_jd}`)}
                    >
                      {width > 6 ? p.lord.slice(0, 2) : ''}
                    </button>
                  )
                })}
              </div>
            )}
            <p className="tiny dim" style={{ marginBottom: 'var(--s4)' }}>
              {tree.periods[0]?.start} to {tree.periods[tree.periods.length - 1]?.end} ·
              today is {today}
            </p>

            <div className="card card--flush">
              <ul className="dasha-tree">
                {tree.periods.map((p) => (
                  <PeriodRow
                    key={`${p.lord}-${p.start_jd}`}
                    period={p}
                    open={open}
                    toggle={toggle}
                  />
                ))}
              </ul>
            </div>
          </>
        )}
      </section>
    </div>
  )
}

function PeriodRow({
  period, open, toggle,
}: {
  period: DashaPeriod
  open: Set<string>
  toggle: (id: string) => void
}) {
  const id = `${period.lord}-${period.start_jd}`
  const kids = period.children ?? []
  const isOpen = open.has(id)

  return (
    <li>
      <button
        className={`dasha-row${period.current ? ' is-current' : ''}`}
        onClick={() => kids.length && toggle(id)}
        aria-expanded={kids.length ? isOpen : undefined}
        style={{ cursor: kids.length ? 'pointer' : 'default' }}
      >
        <span className="dasha-row__lord">
          {kids.length > 0 && (
            <span className="dim mono" aria-hidden="true">{isOpen ? '−' : '+'}</span>
          )}
          <span
            style={{
              width: 8, height: 8, borderRadius: 2,
              background: lordColor(period.lord), display: 'inline-block',
            }}
            aria-hidden="true"
          />
          {period.lord}
          {period.graha && <span className="dim small"> ({period.graha})</span>}
          {period.current && <span className="pill pill--own">now</span>}
          {period.partial_at_birth && (
            <span className="pill pill--neutral" title="Already running at birth">
              partial
            </span>
          )}
        </span>
        <span className="dasha-row__span">
          {period.start} → {period.end}
          <span className="dim"> · {period.duration_years.toFixed(2)}y</span>
        </span>
      </button>

      {isOpen && kids.length > 0 && (
        <ul>
          {kids.map((k) => (
            <PeriodRow key={`${k.lord}-${k.start_jd}`} period={k} open={open} toggle={toggle} />
          ))}
        </ul>
      )}
    </li>
  )
}
