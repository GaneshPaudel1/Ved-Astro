import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { BirthInput, Panchang } from '../api/types'
import './views.css'

export function PanchangView({ birth }: { birth: BirthInput }) {
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [data, setData] = useState<Panchang | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    api
      .panchang({
        date,
        latitude: birth.latitude,
        longitude: birth.longitude,
        ayanamsa: birth.ayanamsa,
      })
      .then(setData)
      .catch(() => setError('Could not calculate the Panchang for that date.'))
      .finally(() => setLoading(false))
  }, [date, birth.latitude, birth.longitude, birth.ayanamsa])

  const shift = (days: number) => {
    const d = new Date(date)
    d.setDate(d.getDate() + days)
    setDate(d.toISOString().slice(0, 10))
  }

  return (
    <div className="stack-lg">
      <section>
        <div className="section__head">
          <span className="section__title">Panchang</span>
          <div className="cluster">
            <button className="btn btn--sm" onClick={() => shift(-1)} aria-label="Previous day">←</button>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              style={{ width: 165 }}
              aria-label="Panchang date"
            />
            <button className="btn btn--sm" onClick={() => shift(1)} aria-label="Next day">→</button>
            <button
              className="btn btn--sm"
              onClick={() => setDate(new Date().toISOString().slice(0, 10))}
            >
              Today
            </button>
          </div>
        </div>

        {error && <div className="notice notice--warn"><span className="notice__mark">!</span><span>{error}</span></div>}
        {loading && !data && <p className="muted"><span className="spin" /> Calculating…</p>}

        {data && (
          <>
            <p className="section__note">
              For {data.location.tz_name} at{' '}
              <span className="mono">
                {data.location.latitude.toFixed(3)}, {data.location.longitude.toFixed(3)}
              </span>
              . {data.note}
            </p>

            <div className="limbs" style={{ marginBottom: 'var(--s5)' }}>
              <div className="limb">
                <div className="limb__label">Vara · weekday</div>
                <div className="limb__value">{data.vara.name}</div>
                <div className="limb__meta">
                  <span className="sanskrit">{data.vara.sanskrit}</span> · ruled by {data.vara.lord}
                </div>
              </div>

              <div className="limb">
                <div className="limb__label">Tithi · lunar day</div>
                <div className="limb__value">{data.tithi.name}</div>
                <div className="limb__meta">
                  {data.tithi.paksha} paksha · {data.tithi.percent_complete.toFixed(0)}% done
                  {data.tithi.ends && <><br />ends <span className="mono">{fmt(data.tithi.ends)}</span></>}
                </div>
              </div>

              <div className="limb">
                <div className="limb__label">Nakshatra</div>
                <div className="limb__value">{data.nakshatra.name}</div>
                <div className="limb__meta">
                  pada {data.nakshatra.pada} · lord {data.nakshatra.lord}
                  {data.nakshatra.ends && <><br />ends <span className="mono">{fmt(data.nakshatra.ends)}</span></>}
                </div>
              </div>

              <div className="limb">
                <div className="limb__label">Yoga</div>
                <div className="limb__value">
                  {data.yoga.name}
                  {data.yoga.inauspicious && <span className="pill pill--caution" style={{ marginLeft: 6, fontSize: '0.6rem' }}>avoid</span>}
                </div>
                <div className="limb__meta">
                  {data.yoga.ends && <>ends <span className="mono">{fmt(data.yoga.ends)}</span></>}
                </div>
              </div>

              <div className="limb">
                <div className="limb__label">Karana</div>
                <div className="limb__value">
                  {data.karana.name}
                  {data.karana.inauspicious && <span className="pill pill--caution" style={{ marginLeft: 6, fontSize: '0.6rem' }}>Bhadra</span>}
                </div>
                <div className="limb__meta">
                  {data.karana.type}
                  {data.karana.ends && <><br />ends <span className="mono">{fmt(data.karana.ends)}</span></>}
                </div>
              </div>

              <div className="limb">
                <div className="limb__label">Moon</div>
                <div className="limb__value">{data.moon.illumination_percent.toFixed(0)}%</div>
                <div className="limb__meta">
                  illuminated · in {data.moon.sign}
                  <MoonPhase angle={data.moon.phase_angle} />
                </div>
              </div>
            </div>

            <div className="grid2">
              <div className="card">
                <p className="eyebrow">Sun and Moon</p>
                <div className="timing">
                  <span>Sunrise</span>
                  <span className="timing__value">{fmt(data.sun.sunrise)}</span>
                </div>
                <div className="timing">
                  <span>Sunset</span>
                  <span className="timing__value">{fmt(data.sun.sunset)}</span>
                </div>
                <div className="timing">
                  <span>Moonrise</span>
                  <span className="timing__value">{fmt(data.moon.moonrise)}</span>
                </div>
                <div className="timing">
                  <span>Moonset</span>
                  <span className="timing__value">{fmt(data.moon.moonset)}</span>
                </div>
                {data.periods.day_length_hours && (
                  <div className="timing">
                    <span>Daylight</span>
                    <span className="timing__value">
                      {Math.floor(data.periods.day_length_hours)}h{' '}
                      {Math.round((data.periods.day_length_hours % 1) * 60)}m
                    </span>
                  </div>
                )}
              </div>

              <div className="card">
                <p className="eyebrow">Day periods</p>
                {data.periods.available === false ? (
                  <p className="small muted">{data.periods.reason}</p>
                ) : (
                  <>
                    <div className="timing timing--good">
                      <span>
                        Abhijit Muhurat
                        <span className="dim tiny"> · most auspicious</span>
                      </span>
                      <span className="timing__value">
                        {fmt(data.periods.abhijit_muhurat?.start)} – {fmt(data.periods.abhijit_muhurat?.end)}
                      </span>
                    </div>
                    <div className="timing timing--bad">
                      <span>Rahu Kaal</span>
                      <span className="timing__value">
                        {fmt(data.periods.rahu_kaal?.start)} – {fmt(data.periods.rahu_kaal?.end)}
                      </span>
                    </div>
                    <div className="timing timing--bad">
                      <span>Yamaganda</span>
                      <span className="timing__value">
                        {fmt(data.periods.yamaganda?.start)} – {fmt(data.periods.yamaganda?.end)}
                      </span>
                    </div>
                    <div className="timing timing--bad">
                      <span>Gulika Kaal</span>
                      <span className="timing__value">
                        {fmt(data.periods.gulika_kaal?.start)} – {fmt(data.periods.gulika_kaal?.end)}
                      </span>
                    </div>
                    <p className="tiny dim" style={{ marginTop: 'var(--s3)', marginBottom: 0 }}>
                      Each inauspicious window is one eighth of the daylight, and
                      which eighth depends on the weekday.
                    </p>
                  </>
                )}
              </div>
            </div>
          </>
        )}
      </section>
    </div>
  )
}

function MoonPhase({ angle }: { angle: number }) {
  /* A simple, honest terminator: the lit fraction drawn as an ellipse. */
  const r = 9
  const k = Math.cos((angle * Math.PI) / 180)
  return (
    <svg width={r * 2 + 4} height={r * 2 + 4} viewBox="-11 -11 22 22"
         style={{ verticalAlign: 'middle', marginLeft: 6 }} aria-hidden="true">
      <circle r={r} fill="var(--surface-sunken)" stroke="var(--line-strong)" strokeWidth="0.6" />
      <path
        d={`M 0 ${-r} A ${r} ${r} 0 0 ${angle < 180 ? 1 : 0} 0 ${r} A ${Math.abs(k) * r} ${r} 0 0 ${k > 0 === angle < 180 ? 0 : 1} 0 ${-r} Z`}
        fill="var(--accent)"
      />
    </svg>
  )
}

function fmt(iso: string | null | undefined): string {
  if (!iso) return '—'
  return iso.slice(11, 16)
}
