import type { Bundle } from '../api/types'
import './views.css'

export function StrengthView({ bundle }: { bundle: Bundle }) {
  const yogas = bundle.yogas ?? []
  const doshas = bundle.doshas
  const av = bundle.ashtakavarga

  return (
    <div className="stack-lg">
      {/* ------------------------------------------------------------ yogas */}
      <section>
        <h3 className="section__title">Yogas</h3>
        <p className="section__note">
          Named combinations the classical texts single out. Each one shows the
          rule that fired it, so you can check the reasoning rather than take the
          label on trust. Detection is deliberately strict — a missing note is
          better than a yoga you do not have.
        </p>

        {yogas.length === 0 ? (
          <div className="notice">
            <span>
              No classical yoga from the detected set is present. That is
              unremarkable — most charts carry two or three, and their absence
              says nothing on its own.
            </span>
          </div>
        ) : (
          <div>
            {yogas.map((y) => (
              <article key={y.key} className={`yoga yoga--${y.strength}`}>
                <div className="yoga__head">
                  <span className="yoga__name">{y.name}</span>
                  <span className="cluster">
                    <span className={`pill ${
                      y.strength === 'major' ? 'pill--positive'
                      : y.strength === 'caution' ? 'pill--caution'
                      : y.strength === 'weak' ? 'pill--neutral' : 'pill--info'}`}>
                      {y.strength}
                    </span>
                    <span className="yoga__planets">
                      {y.planets.map((p) => (
                        <span key={p} className="pill pill--neutral">{p}</span>
                      ))}
                    </span>
                  </span>
                </div>
                <p className="yoga__summary">{y.summary}</p>
                <p className="yoga__detail">{y.detail}</p>
              </article>
            ))}
          </div>
        )}
      </section>

      {/* ----------------------------------------------------------- doshas */}
      {doshas && (
        <section>
          <h3 className="section__title">Doshas</h3>
          <p className="section__note">
            These carry real social weight, so each states its rule and lists any
            cancellation it found. Where traditions disagree — and on Manglik
            they disagree a great deal — the disagreement is reported rather than
            resolved silently.
          </p>

          <div className="stack">
            <DoshaCard
              title="Manglik (Kuja) dosha"
              present={doshas.manglik.present}
              severity={doshas.manglik.severity}
              rule={doshas.manglik.rule}
              note={doshas.manglik.note}
              cancellations={doshas.manglik.cancellations}
            >
              {doshas.manglik.present && doshas.manglik.hits && (
                <ul className="small muted" style={{ margin: '0 0 var(--s2)', paddingLeft: '1.1rem' }}>
                  {doshas.manglik.hits.map((h, i) => (
                    <li key={i}>
                      Mars falls in the {ord(h.house)} house from the {h.reference}
                      {!h.counted_in_south_india && (
                        <span className="dim"> — not counted in southern practice</span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </DoshaCard>

            <DoshaCard
              title="Kaal Sarp dosha"
              present={doshas.kaal_sarp.present}
              severity={doshas.kaal_sarp.present ? doshas.kaal_sarp.type ?? undefined : undefined}
              rule={doshas.kaal_sarp.rule}
              note={doshas.kaal_sarp.note}
            >
              {!doshas.kaal_sarp.present && doshas.kaal_sarp.partial && (
                <p className="small muted" style={{ margin: 0 }}>
                  Partial only: every planet except{' '}
                  <strong>{doshas.kaal_sarp.breaking_planet?.join(', ')}</strong>{' '}
                  lies on one side of the Rahu–Ketu axis, which breaks the full dosha.
                </p>
              )}
            </DoshaCard>

            <DoshaCard
              title="Pitra dosha"
              present={doshas.pitra.present}
              rule={doshas.pitra.rule}
              note={doshas.pitra.note}
            >
              {(doshas.pitra.indicators?.length ?? 0) > 0 && (
                <ul className="small muted" style={{ margin: '0 0 var(--s2)', paddingLeft: '1.1rem' }}>
                  {doshas.pitra.indicators!.map((s, i) => <li key={i}>{s}</li>)}
                </ul>
              )}
              {doshas.pitra.weak_indication && (
                <p className="tiny dim" style={{ margin: 0 }}>
                  Only one indicator found — two are required before this is
                  reported as present.
                </p>
              )}
            </DoshaCard>

            {doshas.sade_sati && <SadeSati data={doshas.sade_sati} />}
          </div>
        </section>
      )}

      {/* ---------------------------------------------------- ashtakavarga */}
      {av && (
        <section>
          <h3 className="section__title">Ashtakavarga</h3>
          <p className="section__note">
            Eight contributors vote on every sign: the seven planets and the
            lagna. {av.note}
          </p>

          <div className="card">
            <div className="scroll-x">
              <table className="av-table">
                <thead>
                  <tr>
                    <th>Sign</th>
                    {av.signs.map((s) => (
                      <th key={s.sign} title={s.sign_name}>{s.sign_name.slice(0, 3)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {Object.keys(av.bav).map((planet) => (
                    <tr key={planet}>
                      <td>{planet}</td>
                      {av.bav[planet].map((b, i) => (
                        <td key={i}>
                          <span
                            className="av-cell"
                            style={{
                              background: bavShade(b),
                              color: b >= 6 ? 'var(--text-inverse)' : 'var(--text-muted)',
                            }}
                          >
                            {b}
                          </span>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <td>Sarva</td>
                    {av.sav.map((v, i) => (
                      <td key={i} style={{ color: savColor(v) }}>{v}</td>
                    ))}
                  </tr>
                  {bundle.chart.time_known && (
                    <tr>
                      <td className="dim tiny">House</td>
                      {av.signs.map((s) => (
                        <td key={s.sign} className="dim tiny">{s.house}</td>
                      ))}
                    </tr>
                  )}
                </tfoot>
              </table>
            </div>

            <p className="tiny dim" style={{ marginTop: 'var(--s3)', marginBottom: 0 }}>
              Sarvashtakavarga totals {av.sav_total} — it always does, across
              every chart. Strongest sign: <strong>{av.signs[av.strongest_sign]?.sign_name}</strong>{' '}
              ({av.sav[av.strongest_sign]}). Weakest:{' '}
              <strong>{av.signs[av.weakest_sign]?.sign_name}</strong> ({av.sav[av.weakest_sign]}).
            </p>
          </div>
        </section>
      )}
    </div>
  )
}

/* ------------------------------------------------------------- fragments */
function DoshaCard({
  title, present, severity, rule, note, cancellations, children,
}: {
  title: string
  present: boolean
  severity?: string
  rule?: string
  note?: string
  cancellations?: string[]
  children?: React.ReactNode
}) {
  const cancelled = severity === 'cancelled'
  return (
    <article className={`yoga yoga--${present ? (cancelled ? 'moderate' : 'caution') : 'weak'}`}>
      <div className="yoga__head">
        <span className="yoga__name">{title}</span>
        <span className={`pill ${
          !present ? 'pill--positive' : cancelled ? 'pill--info' : 'pill--caution'}`}>
          {!present ? 'not present' : cancelled ? 'present but cancelled' : severity ?? 'present'}
        </span>
      </div>
      {children}
      {cancellations && cancellations.length > 0 && (
        <ul className="small" style={{ margin: '0 0 var(--s2)', paddingLeft: '1.1rem', color: 'var(--positive)' }}>
          {cancellations.map((c, i) => <li key={i}>{c}</li>)}
        </ul>
      )}
      {rule && <p className="tiny dim" style={{ margin: '0 0 var(--s1)' }}><strong>Rule:</strong> {rule}</p>}
      {note && <p className="yoga__detail">{note}</p>}
    </article>
  )
}

function SadeSati({ data }: { data: NonNullable<Bundle['doshas']>['sade_sati'] }) {
  if (!data) return null
  const upcoming = data.phases.filter((p) => new Date(p.end) >= new Date()).slice(0, 6)
  return (
    <article className={`yoga yoga--${data.currently_active ? 'caution' : 'weak'}`}>
      <div className="yoga__head">
        <span className="yoga__name">Sade Sati</span>
        <span className={`pill ${data.currently_active ? 'pill--caution' : 'pill--positive'}`}>
          {data.currently_active ? `running · ${data.current_phase?.phase}` : 'not running'}
        </span>
      </div>

      {data.current_phase && (
        <p className="yoga__summary">
          {data.current_phase.description}{' '}
          <span className="mono small dim">
            {data.current_phase.start} → {data.current_phase.end}
          </span>
        </p>
      )}

      {upcoming.length > 0 && (
        <div style={{ margin: 'var(--s3) 0' }}>
          <p className="eyebrow">Upcoming windows</p>
          {upcoming.map((p, i) => (
            <div key={i} className={`timing${p.current ? ' timing--bad' : ''}`}>
              <span>
                {p.phase} <span className="dim small">· Saturn in {p.sign_name}</span>
              </span>
              <span className="timing__value">{p.start} → {p.end}</span>
            </div>
          ))}
        </div>
      )}

      <p className="tiny dim" style={{ margin: '0 0 var(--s1)' }}><strong>Rule:</strong> {data.rule}</p>
      <p className="yoga__detail">{data.note}</p>
    </article>
  )
}

function bavShade(b: number): string {
  if (b === 0) return 'transparent'
  const t = b / 8
  return `color-mix(in srgb, var(--accent) ${Math.round(t * 90)}%, transparent)`
}

function savColor(v: number): string {
  if (v >= 32) return 'var(--positive)'
  if (v >= 28) return 'var(--text)'
  if (v >= 25) return 'var(--caution)'
  return 'var(--negative)'
}

function ord(n: number): string {
  return ({ 1: '1st', 2: '2nd', 3: '3rd' } as Record<number, string>)[n] ?? `${n}th`
}
