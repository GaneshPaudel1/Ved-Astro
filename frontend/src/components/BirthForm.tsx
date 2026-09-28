import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import type { BirthInput, GeoResult, Reference } from '../api/types'
import './birthform.css'

interface Props {
  value: BirthInput
  onChange: (next: BirthInput) => void
  onSubmit: () => void
  reference: Reference | null
  busy?: boolean
  compact?: boolean
  simple?: boolean
  submitLabel?: string
}

/**
 * The birth form carries most of the app's correctness burden, so it shows its
 * work: the resolved timezone and the exact UTC offset the chart will use are
 * displayed before you submit, and an unknown birth time is offered as a real
 * option rather than something to fake with 12:00.
 */
export function BirthForm({
  value, onChange, onSubmit, reference, busy, compact, simple = false, submitLabel = 'Cast chart',
}: Props) {
  const [timeUnknown, setTimeUnknown] = useState(value.time === null)
  const [tzInfo, setTzInfo] = useState<Awaited<ReturnType<typeof api.timezoneAt>> | null>(null)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const set = <K extends keyof BirthInput>(key: K, v: BirthInput[K]) =>
    onChange({ ...value, [key]: v })

  /* Resolve the historical offset whenever the date or the place moves. */
  useEffect(() => {
    if (!value.date || !Number.isFinite(value.latitude)) return
    let cancelled = false
    api
      .timezoneAt(value.latitude, value.longitude, value.date)
      .then((r) => !cancelled && setTzInfo(r))
      .catch(() => !cancelled && setTzInfo(null))
    return () => {
      cancelled = true
    }
  }, [value.date, value.latitude, value.longitude])

  const validate = (): boolean => {
    const e: Record<string, string> = {}
    if (simple && !value.name.trim()) e.name = 'Enter a name.'
    if (!value.date) e.date = 'Enter a birth date.'
    else if (!/^\d{4}-\d{2}-\d{2}$/.test(value.date)) e.date = 'Use the date picker format.'
    if (!timeUnknown && !value.time) e.time = 'Enter a time, or mark it unknown.'
    if (!Number.isFinite(value.latitude) || !Number.isFinite(value.longitude))
      e.place = 'Choose a birth place so we have coordinates.'
    if (Math.abs(value.latitude) > 90) e.place = 'Latitude must be between −90 and 90.'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const submit = (ev: React.FormEvent) => {
    ev.preventDefault()
    if (validate()) onSubmit()
  }

  return (
    <form className={`bform${compact ? ' bform--compact' : ''}`} onSubmit={submit} noValidate>
      <div className="field">
        <label htmlFor="bf-name">Name</label>
        <input
          id="bf-name"
          value={value.name}
          onChange={(e) => set('name', e.target.value)}
          placeholder="Whose chart is this?"
          autoComplete="name"
          aria-invalid={!!errors.name}
        />
        {errors.name && <p className="field__error">{errors.name}</p>}
      </div>
      {simple && <div className="field"><label htmlFor="bf-gender">Gender <span className="muted">(optional)</span></label><select id="bf-gender" value={value.gender ?? ''} onChange={e => set('gender', e.target.value as BirthInput['gender'] || null)}><option value="">Select gender</option><option value="female">Female</option><option value="male">Male</option><option value="other">Other</option><option value="prefer_not_to_say">Prefer not to say</option></select></div>}

      <div className="row row--2">
        <div className="field">
          <label htmlFor="bf-date">Birth date</label>
          <input
            id="bf-date"
            type="date"
            value={value.date}
            max="2200-12-31"
            min="1000-01-01"
            onChange={(e) => set('date', e.target.value)}
            aria-invalid={!!errors.date}
          />
          {errors.date && <p className="field__error">{errors.date}</p>}
        </div>

        <div className="field">
          <label htmlFor="bf-time">Birth time</label>
          {simple ? <BirthTime value={value.time} disabled={timeUnknown} onChange={time => set('time', time)} /> : <>
          <input
            id="bf-time"
            type="time"
            step="1"
            value={value.time ?? ''}
            disabled={timeUnknown}
            onChange={(e) => set('time', e.target.value || null)}
            aria-invalid={!!errors.time}
          />
          </>}
          <label className="bform__check">
            <input
              type="checkbox"
              checked={timeUnknown}
              onChange={(e) => {
                setTimeUnknown(e.target.checked)
                set('time', e.target.checked ? null : '12:00:00')
              }}
            />
            <span>I don&rsquo;t know the birth time</span>
          </label>
          {errors.time && <p className="field__error">{errors.time}</p>}
        </div>
      </div>

      {timeUnknown && !simple && (
        <div className="notice notice--warn" role="status">
          <span className="notice__mark">!</span>
          <span>
            Without a time there is no ascendant, so houses, the lagna reading and
            the divisional charts are switched off. You will still get sign
            positions, nakshatras, dashas and the Panchang for the day. The Moon
            is calculated for midday and may be up to 6&deg; out.
          </span>
        </div>
      )}

      {simple && timeUnknown && <p className="field__hint">Without a birth time, some chart details will be unavailable.</p>}
      <PlaceField
        simple={simple}
        value={value}
        onQueryChange={simple ? place => onChange({ ...value, place, latitude: NaN, longitude: NaN }) : undefined}
        onPick={(g) =>
          onChange({
            ...value,
            place: g.label,
            latitude: g.latitude,
            longitude: g.longitude,
          })
        }
        error={errors.place}
      />

      {tzInfo && !simple && (
        <div className={`bform__tz${tzInfo.pre_standard_time ? ' is-flagged' : ''}`}>
          <div className="bform__tz-row">
            <span className="dim tiny">Timezone at birth</span>
            <span className="mono small">{tzInfo.tz_name}</span>
          </div>
          <div className="bform__tz-row">
            <span className="dim tiny">Offset the chart will use</span>
            <span className="mono small">
              {formatOffset(
                tzInfo.pre_standard_time && value.time_standard === 'auto'
                  ? tzInfo.lmt_offset_hours
                  : tzInfo.utc_offset_hours,
              )}{' '}
              <span className="dim">
                {tzInfo.pre_standard_time && value.time_standard === 'auto'
                  ? 'LMT'
                  : tzInfo.abbreviation}
              </span>
            </span>
          </div>
          {tzInfo.note && <p className="bform__tz-note">{tzInfo.note}</p>}
        </div>
      )}

      {!simple && <button
        type="button"
        className="btn btn--ghost btn--sm bform__toggle"
        onClick={() => setShowAdvanced((v) => !v)}
        aria-expanded={showAdvanced}
      >
        {showAdvanced ? '− Hide' : '+ Show'} calculation settings
      </button>}

      {showAdvanced && reference && (
        <div className="bform__advanced stack">
          <div className="field">
            <label htmlFor="bf-ayan">Ayanamsa</label>
            <select
              id="bf-ayan"
              value={value.ayanamsa}
              onChange={(e) => set('ayanamsa', e.target.value)}
            >
              {reference.ayanamsas.map((a) => (
                <option key={a.key} value={a.key}>
                  {a.label}
                </option>
              ))}
            </select>
            <p className="field__hint">
              {reference.ayanamsas.find((a) => a.key === value.ayanamsa)?.note}
            </p>
          </div>

          <div className="field">
            <label htmlFor="bf-house">House system</label>
            <select
              id="bf-house"
              value={value.house_system}
              onChange={(e) => set('house_system', e.target.value)}
            >
              {reference.house_systems.map((h) => (
                <option key={h.key} value={h.key}>
                  {h.label}
                </option>
              ))}
            </select>
            <p className="field__hint">
              {reference.house_systems.find((h) => h.key === value.house_system)?.note}
            </p>
          </div>

          <div className="row row--2">
            <div className="field">
              <label htmlFor="bf-node">Rahu &amp; Ketu</label>
              <select
                id="bf-node"
                value={value.node_type}
                onChange={(e) => set('node_type', e.target.value)}
              >
                <option value="mean">Mean node (traditional)</option>
                <option value="true">True node</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="bf-std">Clock standard</label>
              <select
                id="bf-std"
                value={value.time_standard}
                onChange={(e) => set('time_standard', e.target.value)}
              >
                <option value="auto">Automatic (recommended)</option>
                <option value="zone">Always use the timezone database</option>
                <option value="lmt">Always use Local Mean Time</option>
              </select>
              <p className="field__hint">
                Automatic switches to Local Mean Time for births before standard
                time reached that place.
              </p>
            </div>
          </div>
        </div>
      )}

      <button type="submit" className="btn btn--primary bform__submit" disabled={busy}>
        {busy ? <><span className="spin" /> Calculating…</> : submitLabel}
      </button>
    </form>
  )
}

/* ------------------------------------------------------------ place lookup */
function PlaceField({
  value, onPick, error, simple = false, onQueryChange,
}: {
  value: BirthInput
  onPick: (g: GeoResult) => void
  error?: string
  simple?: boolean
  onQueryChange?: (place: string) => void
}) {
  const [query, setQuery] = useState(value.place)
  const [results, setResults] = useState<GeoResult[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [cursor, setCursor] = useState(-1)
  const [manual, setManual] = useState(false)
  const boxRef = useRef<HTMLDivElement>(null)
  const timer = useRef<number>()

  useEffect(() => setQuery(value.place), [value.place])

  const search = useCallback((q: string) => {
    window.clearTimeout(timer.current)
    if (q.trim().length < 2) {
      setResults([])
      setOpen(false)
      return
    }
    timer.current = window.setTimeout(async () => {
      setLoading(true)
      try {
        const r = await api.geocode(q)
        setResults(r.results)
        setOpen(r.results.length > 0)
        setCursor(-1)
      } catch {
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 250)
  }, [])

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  const choose = (g: GeoResult) => {
    onPick(g)
    setQuery(g.label)
    setOpen(false)
  }

  return (
    <div className="field" ref={boxRef}>
      <label htmlFor="bf-place">Birth place</label>
      <div className="bform__place">
        <input
          id="bf-place"
          value={query}
          autoComplete="off"
          role="combobox"
          aria-expanded={open}
          aria-controls="bf-place-list"
          aria-autocomplete="list"
          placeholder="Start typing a town or city…"
          onChange={(e) => {
            setQuery(e.target.value)
            onQueryChange?.(e.target.value)
            search(e.target.value)
          }}
          onFocus={() => results.length && setOpen(true)}
          onKeyDown={(e) => {
            if (!open) return
            if (e.key === 'ArrowDown') {
              e.preventDefault()
              setCursor((c) => Math.min(c + 1, results.length - 1))
            } else if (e.key === 'ArrowUp') {
              e.preventDefault()
              setCursor((c) => Math.max(c - 1, 0))
            } else if (e.key === 'Enter' && cursor >= 0) {
              e.preventDefault()
              choose(results[cursor])
            } else if (e.key === 'Escape') {
              setOpen(false)
            }
          }}
          aria-invalid={!!error}
        />
        {loading && <span className="bform__place-spin spin" aria-hidden="true" />}

        {open && (
          <ul className="bform__list" id="bf-place-list" role="listbox">
            {results.map((g, i) => (
              <li key={`${g.label}-${g.latitude}`} role="option" aria-selected={i === cursor}>
                <button
                  type="button"
                  className={`bform__opt${i === cursor ? ' is-cursor' : ''}`}
                  onMouseEnter={() => setCursor(i)}
                  onClick={() => choose(g)}
                >
                  <span className="bform__opt-name">{g.name}</span>
                  <span className="bform__opt-sub">
                    {[g.admin, g.country].filter(Boolean).join(', ')}
                  </span>
                  <span className="bform__opt-coord mono">
                    {g.latitude.toFixed(2)}, {g.longitude.toFixed(2)}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {!simple && <p className="field__hint">
        {Number.isFinite(value.latitude) ? (
          <>
            Using <span className="mono">{value.latitude.toFixed(4)}</span>,{' '}
            <span className="mono">{value.longitude.toFixed(4)}</span>.{' '}
          </>
        ) : (
          'Coordinates are stored with the chart, not the place name. '
        )}
        <button
          type="button"
          className="bform__linkbtn"
          onClick={() => setManual((m) => !m)}
        >
          {manual ? 'Hide' : 'Enter coordinates directly'}
        </button>
      </p>}

      {manual && (
        <div className="row row--2 bform__manual">
          <div>
            <label htmlFor="bf-lat">Latitude</label>
            <input
              id="bf-lat"
              type="number"
              step="0.0001"
              min={-90}
              max={90}
              value={value.latitude}
              onChange={(e) =>
                onPick({
                  ...({} as GeoResult),
                  label: value.place,
                  latitude: parseFloat(e.target.value),
                  longitude: value.longitude,
                } as GeoResult)
              }
            />
          </div>
          <div>
            <label htmlFor="bf-lon">Longitude</label>
            <input
              id="bf-lon"
              type="number"
              step="0.0001"
              min={-180}
              max={180}
              value={value.longitude}
              onChange={(e) =>
                onPick({
                  ...({} as GeoResult),
                  label: value.place,
                  latitude: value.latitude,
                  longitude: parseFloat(e.target.value),
                } as GeoResult)
              }
            />
          </div>
        </div>
      )}

      {error && <p className="field__error">{error}</p>}
    </div>
  )
}

export function formatOffset(hours: number): string {
  const sign = hours < 0 ? '−' : '+'
  const total = Math.round(Math.abs(hours) * 3600)
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  return `UTC${sign}${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}${
    s ? `:${String(s).padStart(2, '0')}` : ''
  }`
}

function BirthTime({ value, disabled, onChange }: { value: string | null; disabled: boolean; onChange: (time: string) => void }) {
  const [hour, setHour] = useState(value ? String(Number(value.split(':')[0]) % 12 || 12) : '')
  const [minute, setMinute] = useState(value ? value.split(':')[1] : '00')
  const [period, setPeriod] = useState(value && Number(value.split(':')[0]) >= 12 ? 'PM' : 'AM')
  useEffect(() => { if (value) { setHour(String(Number(value.split(':')[0]) % 12 || 12)); setMinute(value.split(':')[1]); setPeriod(Number(value.split(':')[0]) >= 12 ? 'PM' : 'AM') } }, [value])
  const update = (h: string, m: string, p: string) => {
    setHour(h); setMinute(m); setPeriod(p)
    onChange(h ? `${String(Number(h) % 12 + (p === 'PM' ? 12 : 0)).padStart(2, '0')}:${m}:00` : '')
  }
  return <div className="birth-time-controls">
    <select id="bf-time" aria-label="Birth hour" disabled={disabled} value={hour} onChange={e => update(e.target.value, minute, period)}><option value="">Hour</option>{Array.from({length:12}, (_,i) => <option key={i+1} value={i+1}>{i+1}</option>)}</select>
    <select aria-label="Birth minute" disabled={disabled} value={minute} onChange={e => update(hour, e.target.value, period)}>{Array.from({length:60}, (_,i) => <option key={i} value={String(i).padStart(2,'0')}>{String(i).padStart(2,'0')}</option>)}</select>
    <select aria-label="AM or PM" disabled={disabled} value={period} onChange={e => update(hour, minute, e.target.value)}><option>AM</option><option>PM</option></select>
  </div>
}
