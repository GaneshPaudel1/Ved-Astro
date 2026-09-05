import { useState } from 'react'
import { KundliChart, type ChartStyle } from '../components/charts/KundliChart'
import type { Bundle, Planet } from '../api/types'
import './views.css'

export function ChartView({ bundle, signNames }: { bundle: Bundle; signNames: string[] }) {
  const [style, setStyle] = useState<ChartStyle>('north')
  const [selected, setSelected] = useState<string | null>(null)
  const c = bundle.chart

  const placements = Object.values(c.planets).map((p) => ({
    name: p.name,
    abbr: p.abbr,
    sign: p.sign,
    sign_name: p.sign_name,
    house: p.house,
    degree_str: p.degree_str,
    dignity: p.dignity,
    retrograde: p.retrograde,
    combust: p.combust,
    vargottama: bundle.vargottama?.includes(p.name),
  }))

  const active = selected ? c.planets[selected] : null

  return (
    <div className="grid2">
      <div className="stack">
        <div className="section__head">
          <span className="section__title">Rashi chart</span>
          <div className="segmented" role="group" aria-label="Chart style">
            <button aria-pressed={style === 'north'} onClick={() => setStyle('north')}>
              North Indian
            </button>
            <button aria-pressed={style === 'south'} onClick={() => setStyle('south')}>
              South Indian
            </button>
          </div>
        </div>

        <KundliChart
          style={style}
          placements={placements}
          ascendantSign={c.ascendant_sign}
          signNames={signNames}
          centreLabel={c.ascendant_sign_name ? `${c.ascendant_sign_name} lagna` : undefined}
          centreSub={c.ascendant_degree_str ?? undefined}
          selected={selected}
          onSelect={setSelected}
          size={440}
        />

        <p className="section__note">
          {style === 'north'
            ? 'Houses stay fixed and the signs move through them. The diamond at the top is the 1st house; the number in each region is its sign. Houses run anticlockwise.'
            : 'Signs stay fixed and the houses move. Aries is second along the top row and the signs run clockwise. The corner stroke marks the ascendant.'}{' '}
          Select a planet to see its detail.
        </p>

        <ChartLegend />

        {active && <PlanetDetail planet={active} bundle={bundle} onClose={() => setSelected(null)} />}
      </div>

      <div className="stack">
        <PlanetTable
          planets={c.planets}
          selected={selected}
          onSelect={setSelected}
          timeKnown={c.time_known}
          vargottama={bundle.vargottama ?? []}
        />
        {c.time_known && <HouseTable bundle={bundle} />}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ table */
function PlanetTable({
  planets, selected, onSelect, timeKnown, vargottama,
}: {
  planets: Record<string, Planet>
  selected: string | null
  onSelect: (n: string | null) => void
  timeKnown: boolean
  vargottama: string[]
}) {
  return (
    <div className="card card--flush">
      <div className="card__head">
        <h3 className="section__title">Planetary positions</h3>
        <span className="tiny dim">Sidereal longitudes</span>
      </div>
      <div className="scroll-x">
        <table className="table">
          <thead>
            <tr>
              <th>Graha</th>
              <th>Sign</th>
              <th className="num">Degree</th>
              {timeKnown && <th className="num">House</th>}
              <th>Nakshatra</th>
              <th className="num">Pada</th>
              <th>State</th>
            </tr>
          </thead>
          <tbody>
            {Object.values(planets).map((p) => (
              <tr
                key={p.name}
                data-active={selected === p.name}
                onClick={() => onSelect(selected === p.name ? null : p.name)}
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    onSelect(selected === p.name ? null : p.name)
                  }
                }}
              >
                <td>
                  <span className="planetcell">
                    <span className="planetcell__glyph" aria-hidden="true">{p.glyph}</span>
                    <span>
                      <span className="planetcell__name">{p.name}</span>
                      <span className="planetcell__sanskrit sanskrit tiny"> {p.sanskrit}</span>
                    </span>
                  </span>
                </td>
                <td>{p.sign_name}</td>
                <td className="num">{p.degree_str}</td>
                {timeKnown && <td className="num">{p.house}</td>}
                <td className="small">{p.nakshatra_name}</td>
                <td className="num">{p.pada}</td>
                <td>
                  <span className="cluster" style={{ gap: '4px' }}>
                    <DignityPill dignity={p.dignity} />
                    {p.retrograde && p.name !== 'Rahu' && p.name !== 'Ketu' && (
                      <span className="pill pill--retro" title="Retrograde">℞</span>
                    )}
                    {p.combust && (
                      <span className="pill pill--combust" title="Combust — too close to the Sun">
                        combust
                      </span>
                    )}
                    {vargottama.includes(p.name) && (
                      <span className="pill pill--own" title="Same sign in D1 and D9">
                        vargottama
                      </span>
                    )}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function HouseTable({ bundle }: { bundle: Bundle }) {
  return (
    <div className="card card--flush">
      <div className="card__head">
        <h3 className="section__title">Houses (Bhava)</h3>
        <span className="tiny dim">{labelHouseSystem(bundle.chart.house_system)}</span>
      </div>
      <div className="scroll-x">
        <table className="table">
          <thead>
            <tr>
              <th className="num">#</th>
              <th>Sign</th>
              <th>Lord</th>
              <th>Occupants</th>
              <th>Signifies</th>
            </tr>
          </thead>
          <tbody>
            {bundle.chart.houses.map((h) => (
              <tr key={h.number} style={{ cursor: 'default' }}>
                <td className="num">{h.number}</td>
                <td>
                  {h.sign_name}
                  <span className="sanskrit tiny"> {h.sign_sanskrit}</span>
                </td>
                <td>{h.lord}</td>
                <td className="mono small">
                  {h.planets.length ? h.planets.map((p) => p.slice(0, 2)).join(' ') : <span className="dim">—</span>}
                </td>
                <td className="small muted">{h.meaning}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------ detail card */
function PlanetDetail({
  planet, bundle, onClose,
}: {
  planet: Planet
  bundle: Bundle
  onClose: () => void
}) {
  const nak = bundle.nakshatra_detail?.[planet.name]
  const strength = bundle.varga_strength?.[planet.name]
  const bav = bundle.ashtakavarga?.bav?.[planet.name]

  return (
    <aside className="detail card" aria-live="polite">
      <div className="between">
        <div>
          <p className="eyebrow">Graha detail</p>
          <h3 className="detail__name">
            <span aria-hidden="true">{planet.glyph}</span> {planet.name}
            <span className="sanskrit"> · {planet.sanskrit}</span>
          </h3>
        </div>
        <button className="btn btn--ghost btn--sm" onClick={onClose} aria-label="Close detail">
          ✕
        </button>
      </div>

      <dl className="detail__grid">
        <div>
          <dt>Position</dt>
          <dd className="mono">
            {planet.degree_str} {planet.sign_name}
          </dd>
        </div>
        {planet.house > 0 && (
          <div>
            <dt>House</dt>
            <dd>
              {planet.house}
              <span className="dim small"> · {bundle.chart.houses[planet.house - 1]?.meaning.split(',')[0]}</span>
            </dd>
          </div>
        )}
        <div>
          <dt>Nakshatra</dt>
          <dd>
            {planet.nakshatra_name} <span className="dim">pada {planet.pada}</span>
          </dd>
        </div>
        <div>
          <dt>Star lord</dt>
          <dd>{planet.nakshatra_lord}</dd>
        </div>
        <div>
          <dt>Dignity</dt>
          <dd><DignityPill dignity={planet.dignity} /></dd>
        </div>
        <div>
          <dt>Motion</dt>
          <dd className="mono small">
            {planet.retrograde ? 'retrograde' : 'direct'} · {planet.speed.toFixed(4)}°/day
          </dd>
        </div>
      </dl>

      {nak && (
        <div className="detail__block">
          <p className="eyebrow">Nakshatra detail</p>
          <p className="small muted">
            Deity <strong className="detail__strong">{nak.deity}</strong> · Symbol{' '}
            <strong className="detail__strong">{nak.symbol}</strong> · Gana{' '}
            <strong className="detail__strong">{nak.gana}</strong> · Nadi{' '}
            <strong className="detail__strong">{nak.nadi}</strong> · Yoni{' '}
            <strong className="detail__strong">{nak.yoni}</strong>
          </p>
          <div className="progress" title={`${nak.percent_through.toFixed(1)}% through ${nak.name}`}>
            <div className="progress__fill" style={{ width: `${nak.percent_through}%` }} />
          </div>
          <p className="tiny dim">
            {nak.percent_through.toFixed(1)}% through {nak.name}
          </p>
        </div>
      )}

      {strength && (
        <div className="detail__block">
          <p className="eyebrow">Strength across the 16 divisions</p>
          <p className="small muted">
            Well placed in{' '}
            <strong className="detail__strong">
              {strength.favourable_vargas} of {strength.total_vargas}
            </strong>{' '}
            vargas
            {strength.vargottama && ' · vargottama (same sign in D1 and D9)'}
          </p>
          <div className="progress">
            <div
              className="progress__fill"
              style={{ width: `${(strength.favourable_vargas / strength.total_vargas) * 100}%` }}
            />
          </div>
        </div>
      )}

      {bav && (
        <div className="detail__block">
          <p className="eyebrow">Its own Ashtakavarga bindus</p>
          <div className="bindurow">
            {bav.map((b, i) => (
              <span
                key={i}
                className={`bindurow__cell${i === planet.sign ? ' is-here' : ''}`}
                title={`${b} bindus`}
              >
                {b}
              </span>
            ))}
          </div>
          <p className="tiny dim">
            Aries to Pisces. Highlighted is the sign {planet.name} occupies —{' '}
            {bav[planet.sign]} of a possible 8.
          </p>
        </div>
      )}
    </aside>
  )
}

/* ----------------------------------------------------------------- shared */
export function DignityPill({ dignity }: { dignity: string }) {
  const cls =
    dignity === 'exalted' ? 'pill--exalted'
    : dignity === 'debilitated' ? 'pill--debilitated'
    : dignity === 'own sign' || dignity === 'moolatrikona' ? 'pill--own'
    : 'pill--neutral'
  return <span className={`pill ${cls}`}>{dignity}</span>
}

function ChartLegend() {
  return (
    <div className="legend">
      <span className="legend__item">
        <span className="legend__swatch" style={{ background: 'var(--exalted)' }} /> exalted ↑
      </span>
      <span className="legend__item">
        <span className="legend__swatch" style={{ background: 'var(--debilitated)' }} /> debilitated ↓
      </span>
      <span className="legend__item">
        <span className="legend__swatch" style={{ background: 'var(--accent-bright)' }} /> own sign •
      </span>
      <span className="legend__item">
        <span className="legend__swatch" style={{ background: 'var(--retro)' }} /> ℞ retrograde
      </span>
    </div>
  )
}

function labelHouseSystem(key: string): string {
  const map: Record<string, string> = {
    whole_sign: 'Whole sign', placidus: 'Placidus', koch: 'Koch',
    equal: 'Equal', sripati: 'Sripati / Porphyry',
  }
  return map[key] ?? key
}
