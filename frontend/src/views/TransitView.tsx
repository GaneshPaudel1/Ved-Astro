import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { KundliChart } from '../components/charts/KundliChart'
import type { BirthInput, Bundle } from '../api/types'
import './views.css'

export function TransitView({
  bundle, birth, signNames,
}: {
  bundle: Bundle
  birth: BirthInput
  signNames: string[]
}) {
  const [data, setData] = useState<any>(null)
  const [when, setWhen] = useState<string>(new Date().toISOString().slice(0, 10))
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    api.transits({ ...birth, at: `${when}T12:00:00Z` })
      .then(setData)
      .finally(() => setLoading(false))
  }, [birth, when])

  if (!data) {
    return <p className="muted"><span className="spin" /> Loading transits…</p>
  }

  const planets = Object.values(data.transits.planets) as any[]
  const natalSign = bundle.chart.ascendant_sign

  return (
    <div className="stack-lg">
      <section>
        <div className="section__head">
          <span className="section__title">Gochar — transits</span>
          <div style={{ maxWidth: 190 }}>
            <input
              type="date"
              value={when}
              onChange={(e) => setWhen(e.target.value)}
              aria-label="Transit date"
            />
          </div>
        </div>
        <p className="section__note">{data.transits.read_from}</p>

        <div className="grid2">
          <div className="stack">
            <KundliChart
              style="north"
              placements={planets.map((p) => ({
                name: p.name, abbr: p.abbr, sign: p.sign, sign_name: p.sign_name,
                house: p.house_from_lagna ?? 0, degree_str: p.degree_str,
                dignity: 'neutral', retrograde: p.retrograde,
              }))}
              ascendantSign={natalSign}
              signNames={signNames}
              title="Transits on the natal frame"
              subtitle={when}
              centreLabel="Gochar"
              centreSub={when}
              size={400}
            />
            <p className="tiny dim">
              Houses are the natal ones; the planets shown are where they stand
              today. {loading && <><span className="spin" /> updating…</>}
            </p>
          </div>

          <div className="card card--flush">
            <div className="card__head">
              <h3 className="section__title">Positions and effect</h3>
              <span className="tiny dim">
                counted from the natal Moon in {data.transits.natal_moon_sign}
              </span>
            </div>
            <div className="scroll-x">
              <table className="table">
                <thead>
                  <tr>
                    <th>Graha</th>
                    <th>Now in</th>
                    <th className="num">From Moon</th>
                    <th className="num">Bindus</th>
                    <th>Reading</th>
                  </tr>
                </thead>
                <tbody>
                  {planets.map((p) => (
                    <tr key={p.name} style={{ cursor: 'default' }}>
                      <td>
                        {p.name}
                        {p.retrograde && p.name !== 'Rahu' && p.name !== 'Ketu' && (
                          <span className="pill pill--retro" style={{ marginLeft: 4 }}>℞</span>
                        )}
                      </td>
                      <td className="small">
                        {p.sign_name} <span className="mono dim">{p.degree_str}</span>
                      </td>
                      <td className="num">{p.house_from_moon}</td>
                      <td className="num">
                        {p.bindus_in_sign !== undefined ? (
                          <span style={{ color: p.bindus_in_sign >= 5 ? 'var(--positive)' : p.bindus_in_sign <= 2 ? 'var(--negative)' : undefined }}>
                            {p.bindus_in_sign}
                          </span>
                        ) : <span className="dim">—</span>}
                      </td>
                      <td className="small muted">
                        {p.favourable !== null && (
                          <span className={`pill ${p.favourable ? 'pill--positive' : 'pill--neutral'}`}
                                style={{ marginRight: 6 }}>
                            {p.favourable ? 'favourable' : 'mixed'}
                          </span>
                        )}
                        {p.note}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      {data.alerts?.length > 0 && (
        <section>
          <h3 className="section__title">Coming up</h3>
          <p className="section__note">
            Sign changes by the slow planets, described against your natal Moon.
            These are the shifts that mark a change of chapter rather than a
            passing mood.
          </p>
          <div className="stack-sm">
            {data.alerts.map((a: any, i: number) => (
              <div
                key={i}
                className={`notice ${
                  a.severity === 'major' ? 'notice--warn'
                  : a.severity === 'favourable' ? 'notice--info' : ''}`}
              >
                <span className="notice__mark" style={{
                  color: a.severity === 'favourable' ? 'var(--positive)'
                       : a.severity === 'major' ? 'var(--caution)' : 'var(--info)',
                }}>
                  {a.severity === 'favourable' ? '↑' : a.severity === 'major' ? '!' : '·'}
                </span>
                <span>
                  {a.message}
                  <span className="dim tiny"> ({Math.round(a.days_away)} days away)</span>
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {data.ingresses?.length > 0 && (
        <section>
          <h3 className="section__title">Next sign changes</h3>
          <div className="card card--flush">
            <div className="scroll-x">
              <table className="table">
                <thead>
                  <tr><th>Graha</th><th>Leaves</th><th>Enters</th><th>Date</th><th className="num">Days</th></tr>
                </thead>
                <tbody>
                  {data.ingresses.map((g: any) => (
                    <tr key={g.planet} style={{ cursor: 'default' }}>
                      <td>{g.planet}</td>
                      <td>{g.from_sign}</td>
                      <td>{g.to_sign}</td>
                      <td className="mono small">{g.date}</td>
                      <td className="num">{Math.round(g.days_away)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}
