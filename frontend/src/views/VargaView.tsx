import { useState } from 'react'
import { KundliChart, type ChartStyle } from '../components/charts/KundliChart'
import type { Bundle } from '../api/types'
import './views.css'

const ORDER = ['D1', 'D2', 'D3', 'D4', 'D7', 'D9', 'D10', 'D12',
               'D16', 'D20', 'D24', 'D27', 'D30', 'D40', 'D45', 'D60']

export function VargaView({ bundle, signNames }: { bundle: Bundle; signNames: string[] }) {
  const [style, setStyle] = useState<ChartStyle>('north')
  const [focus, setFocus] = useState<string | null>('D9')
  const vargas = bundle.vargas

  if (!bundle.chart.time_known || !vargas) {
    return (
      <div className="notice notice--warn">
        <span className="notice__mark">!</span>
        <span>
          Divisional charts are built from the ascendant, which needs a birth
          time. Without one they would be guesswork, so they are switched off.
        </span>
      </div>
    )
  }

  const focused = focus ? vargas[focus] : null

  return (
    <div className="stack-lg">
      <section>
        <div className="section__head">
          <span className="section__title">The sixteen divisions</span>
          <div className="segmented" role="group" aria-label="Chart style">
            <button aria-pressed={style === 'north'} onClick={() => setStyle('north')}>North</button>
            <button aria-pressed={style === 'south'} onClick={() => setStyle('south')}>South</button>
          </div>
        </div>
        <p className="section__note">
          Each varga divides every sign into D parts and maps each part to a sign
          by its own rule — the rules genuinely differ, so these are sixteen
          separate charts, not sixteen views of one. Select any chart to enlarge
          it. The navamsa (D9) is the one most readings lean on after the rashi.
        </p>

        {focused && (
          <div className="grid2" style={{ marginBottom: 'var(--s5)' }}>
            <KundliChart
              style={style}
              placements={Object.values(focused.planets).map((p) => ({
                ...p, degree_str: undefined,
                vargottama: p.vargottama,
              }))}
              ascendantSign={focused.ascendant_sign}
              signNames={signNames}
              title={`${focused.varga} · ${focused.name}`}
              subtitle={`${focused.divisions} division${focused.divisions > 1 ? 's' : ''} per sign`}
              centreLabel={focused.ascendant_sign_name ?? undefined}
              centreSub={focused.varga}
              size={420}
            />
            <div className="card">
              <p className="eyebrow">{focused.varga} · {focused.name}</p>
              <h3 className="section__title" style={{ marginBottom: 'var(--s2)' }}>
                {focused.signifies}
              </h3>
              <div className="scroll-x">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Graha</th><th>Sign</th><th className="num">House</th><th>Dignity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.values(focused.planets).map((p) => (
                      <tr key={p.name} style={{ cursor: 'default' }}>
                        <td>{p.name}</td>
                        <td>
                          {p.sign_name}
                          {p.vargottama && (
                            <span className="pill pill--own" style={{ marginLeft: 6 }}>
                              vargottama
                            </span>
                          )}
                        </td>
                        <td className="num">{p.house}</td>
                        <td>
                          <span className={`pill ${
                            p.dignity === 'exalted' ? 'pill--exalted'
                            : p.dignity === 'debilitated' ? 'pill--debilitated'
                            : p.dignity === 'own sign' ? 'pill--own' : 'pill--neutral'}`}>
                            {p.dignity}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        <div className="varga-grid">
          {ORDER.filter((k) => vargas[k]).map((key) => {
            const v = vargas[key]
            return (
              <button
                key={key}
                className="varga-card"
                onClick={() => setFocus(key === focus ? null : key)}
                aria-pressed={key === focus}
                style={{
                  cursor: 'pointer', textAlign: 'left', width: '100%',
                  borderColor: key === focus ? 'var(--accent)' : undefined,
                }}
              >
                <div className="varga-card__head">
                  <span className="varga-card__key">{v.varga}</span>
                  <span className="varga-card__name">{v.name}</span>
                </div>
                <KundliChart
                  style={style}
                  placements={Object.values(v.planets).map((p) => ({ ...p }))}
                  ascendantSign={v.ascendant_sign}
                  signNames={signNames}
                  size={200}
                />
                <p className="varga-card__sig">{v.signifies}</p>
              </button>
            )
          })}
        </div>
      </section>

      {bundle.varga_strength && (
        <section>
          <h3 className="section__title">Strength across the divisions</h3>
          <p className="section__note">
            A planet that holds up across many vargas delivers its results more
            reliably than one strong only in the rashi chart. This counts how
            many of the sixteen place it in its own, exaltation or a friendly
            sign.
          </p>
          <div className="card card--flush">
            <div className="scroll-x">
              <table className="table">
                <thead>
                  <tr>
                    <th>Graha</th>
                    <th className="num">Favourable</th>
                    <th>Spread</th>
                    <th className="num">Exalted</th>
                    <th className="num">Own</th>
                    <th className="num">Debilitated</th>
                    <th>Vargottama</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(bundle.varga_strength).map(([name, s]) => (
                    <tr key={name} style={{ cursor: 'default' }}>
                      <td>{name}</td>
                      <td className="num">{s.favourable_vargas}/{s.total_vargas}</td>
                      <td style={{ minWidth: 120 }}>
                        <div className="progress" style={{ margin: 0 }}>
                          <div
                            className="progress__fill"
                            style={{ width: `${(s.favourable_vargas / s.total_vargas) * 100}%` }}
                          />
                        </div>
                      </td>
                      <td className="num">{s.counts.exalted}</td>
                      <td className="num">{s.counts['own sign']}</td>
                      <td className="num">{s.counts.debilitated}</td>
                      <td>{s.vargottama ? <span className="pill pill--own">yes</span> : <span className="dim">—</span>}</td>
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
