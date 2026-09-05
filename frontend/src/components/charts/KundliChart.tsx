import { useId, useMemo, useState } from 'react'
import {
  NORTH_HOUSES, NORTH_LINES, SOUTH_CELLS, SOUTH_ORDER,
  polygonPoints, dignityColor, dignityShort,
} from './geometry'
import './chart.css'

export type ChartStyle = 'north' | 'south'

export interface ChartPlacement {
  name: string
  abbr: string
  sign: number
  /** used only for the accessible label */
  sign_name?: string
  house: number
  degree_str?: string
  dignity: string
  retrograde: boolean
  combust?: boolean
  vargottama?: boolean
}

interface Props {
  style: ChartStyle
  placements: ChartPlacement[]
  ascendantSign: number | null
  signNames: string[]
  title?: string
  subtitle?: string
  /** shown in the middle of the figure */
  centreLabel?: string
  centreSub?: string
  selected?: string | null
  onSelect?: (planet: string | null) => void
  size?: number
}

/**
 * One component draws both layouts because they share everything except where
 * a region sits: the placement logic, hit targets, keyboard handling and label
 * stacking are identical.
 */
export function KundliChart({
  style, placements, ascendantSign, signNames, title, subtitle,
  centreLabel, centreSub, selected, onSelect, size = 400,
}: Props) {
  const uid = useId()
  const [hovered, setHovered] = useState<string | null>(null)
  const active = selected ?? hovered

  /** planets grouped by the sign they occupy */
  const bySign = useMemo(() => {
    const map: Record<number, ChartPlacement[]> = {}
    for (const p of placements) (map[p.sign] ||= []).push(p)
    return map
  }, [placements])

  const houseToSign = (house: number) =>
    ascendantSign === null ? null : (ascendantSign + house - 1) % 12

  if (ascendantSign === null) {
    return (
      <figure className="kundli kundli--empty" style={{ maxWidth: size }}>
        <div className="kundli__placeholder">
          <p className="eyebrow">Chart unavailable</p>
          <p className="small muted">
            The birth time is unknown, so there is no ascendant and the houses
            cannot be drawn. Planetary signs and nakshatras are still available
            in the table below.
          </p>
        </div>
      </figure>
    )
  }

  return (
    <figure className="kundli" style={{ maxWidth: size }}>
      {(title || subtitle) && (
        <figcaption className="kundli__head">
          {title && <span className="kundli__title">{title}</span>}
          {subtitle && <span className="kundli__sub">{subtitle}</span>}
        </figcaption>
      )}

      <svg
        viewBox={`0 0 ${size} ${size}`}
        className="kundli__svg"
        role="img"
        aria-labelledby={`${uid}-t`}
        preserveAspectRatio="xMidYMid meet"
      >
        <title id={`${uid}-t`}>
          {title || 'Birth chart'} in the{' '}
          {style === 'north' ? 'North Indian' : 'South Indian'} style
        </title>

        <rect x="0" y="0" width={size} height={size} className="kundli__ground" />

        {style === 'north'
          ? <NorthFigure
              size={size} bySign={bySign} houseToSign={houseToSign}
              signNames={signNames} active={active}
              onSelect={onSelect} setHovered={setHovered}
              centreLabel={centreLabel} centreSub={centreSub}
            />
          : <SouthFigure
              size={size} bySign={bySign} ascendantSign={ascendantSign}
              signNames={signNames} active={active}
              onSelect={onSelect} setHovered={setHovered}
              centreLabel={centreLabel} centreSub={centreSub}
            />}
      </svg>
    </figure>
  )
}

/* ------------------------------------------------------------------ north */
function NorthFigure({
  size, bySign, houseToSign, signNames, active, onSelect, setHovered,
  centreLabel, centreSub,
}: any) {
  return (
    <>
      <rect
        x="0.5" y="0.5" width={size - 1} height={size - 1}
        className="kundli__frame"
      />
      {NORTH_LINES.map(([a, b], i) => (
        <line
          key={i}
          x1={a[0] * size} y1={a[1] * size}
          x2={b[0] * size} y2={b[1] * size}
          className="kundli__rule"
        />
      ))}

      {NORTH_HOUSES.map((poly) => {
        const sign = houseToSign(poly.house)
        if (sign === null) return null
        const planets = bySign[sign] || []
        return (
          <g key={poly.house} className="kundli__cell">
            <polygon
              points={polygonPoints(poly, size)}
              className="kundli__hit"
              aria-hidden="true"
            />
            {/* Sign number, the way it is written on a paper kundli */}
            <text
              x={poly.signAnchor[0] * size}
              y={poly.signAnchor[1] * size}
              className="kundli__signnum"
              textAnchor="middle"
              dominantBaseline="middle"
            >
              {sign + 1}
            </text>
            {poly.house === 1 && (
              <text
                x={poly.anchor[0] * size}
                y={poly.anchor[1] * size - 26}
                className="kundli__asc"
                textAnchor="middle"
              >
                Asc
              </text>
            )}
            <PlanetStack
              planets={planets}
              x={poly.anchor[0] * size}
              y={poly.anchor[1] * size}
              active={active}
              onSelect={onSelect}
              setHovered={setHovered}
            />
          </g>
        )
      })}

      {centreLabel && (
        <g className="kundli__centre" aria-hidden="true">
          <text x={size / 2} y={size / 2 - 4} textAnchor="middle" className="kundli__centre-main">
            {centreLabel}
          </text>
          {centreSub && (
            <text x={size / 2} y={size / 2 + 13} textAnchor="middle" className="kundli__centre-sub">
              {centreSub}
            </text>
          )}
        </g>
      )}
    </>
  )
}

/* ------------------------------------------------------------------ south */
function SouthFigure({
  size, bySign, ascendantSign, signNames, active, onSelect, setHovered,
  centreLabel, centreSub,
}: any) {
  const cell = size / 4
  return (
    <>
      <rect x="0.5" y="0.5" width={size - 1} height={size - 1} className="kundli__frame" />

      {SOUTH_ORDER.map((sign) => {
        const [row, col] = SOUTH_CELLS[sign]
        const x = col * cell
        const y = row * cell
        const planets = bySign[sign] || []
        const isAsc = sign === ascendantSign
        return (
          <g key={sign} className="kundli__cell">
            <rect
              x={x} y={y} width={cell} height={cell}
              className={`kundli__hit kundli__box${isAsc ? ' is-asc' : ''}`}
            />
            {/* The ascendant is marked with a corner stroke, as on a printed chart */}
            {isAsc && (
              <line
                x1={x + 2} y1={y + cell * 0.34}
                x2={x + cell * 0.34} y2={y + 2}
                className="kundli__ascmark"
              />
            )}
            <text
              x={x + cell - 6} y={y + 14}
              className="kundli__signname"
              textAnchor="end"
            >
              {signNames[sign]?.slice(0, 3)}
            </text>
            <PlanetStack
              planets={planets}
              x={x + cell / 2}
              y={y + cell / 2 + 4}
              active={active}
              onSelect={onSelect}
              setHovered={setHovered}
            />
          </g>
        )
      })}

      {/* The 2×2 middle is empty on a South Indian chart; use it for the label */}
      <rect
        x={cell} y={cell} width={cell * 2} height={cell * 2}
        className="kundli__centrebox"
      />
      {centreLabel && (
        <g className="kundli__centre" aria-hidden="true">
          <text x={size / 2} y={size / 2 - 4} textAnchor="middle" className="kundli__centre-main">
            {centreLabel}
          </text>
          {centreSub && (
            <text x={size / 2} y={size / 2 + 13} textAnchor="middle" className="kundli__centre-sub">
              {centreSub}
            </text>
          )}
        </g>
      )}
    </>
  )
}

/* ------------------------------------------------------------- planet text */
function PlanetStack({ planets, x, y, active, onSelect, setHovered }: any) {
  if (!planets.length) return null
  const lineHeight = 15
  const startY = y - ((planets.length - 1) * lineHeight) / 2

  return (
    <>
      {planets.map((p: ChartPlacement, i: number) => {
        const isActive = active === p.name
        return (
          <text
            key={p.name}
            x={x}
            y={startY + i * lineHeight}
            textAnchor="middle"
            dominantBaseline="middle"
            className={`kundli__planet${isActive ? ' is-active' : ''}`}
            style={{ fill: dignityColor(p.dignity) }}
            tabIndex={0}
            role="button"
            aria-label={
              `${p.name} in ${p.sign_name ?? ''} house ${p.house}` +
              `${p.degree_str ? `, ${p.degree_str}` : ''}` +
              `${p.dignity !== 'neutral' ? `, ${p.dignity}` : ''}` +
              `${p.retrograde ? ', retrograde' : ''}`
            }
            onClick={() => onSelect?.(isActive ? null : p.name)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                onSelect?.(isActive ? null : p.name)
              }
              if (e.key === 'Escape') onSelect?.(null)
            }}
            onMouseEnter={() => setHovered(p.name)}
            onMouseLeave={() => setHovered(null)}
          >
            {p.abbr}
            {p.retrograde && <tspan className="kundli__retro"> ℞</tspan>}
            {dignityShort(p.dignity) && (
              <tspan className="kundli__dignity">{dignityShort(p.dignity)}</tspan>
            )}
          </text>
        )
      })}
    </>
  )
}
