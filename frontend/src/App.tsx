import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api, ApiError } from './api/client'
import type { BirthInput, Bundle, Reference } from './api/types'
import { BirthForm } from './components/BirthForm'
import { ChartView } from './views/ChartView'
import { VargaView } from './views/VargaView'
import { DashaView } from './views/DashaView'
import { StrengthView } from './views/StrengthView'
import { TransitView } from './views/TransitView'
import { PanchangView } from './views/PanchangView'
import { MatchmakingPage } from './components/MatchmakingPage'
import { ReadingView } from './views/ReadingView'
import { CosmicSnapshot } from './components/Celestial'
import { ChartLibrary, type SavedChart } from './components/ChartLibrary'
import { useChartLibrary } from './components/useChartLibrary'
import { ChartReport } from './components/ChartReport'
import './styles/report.css'
import { AstroChat } from './components/AstroChat'
import { GoogleAccount, type Account } from './components/GoogleAccount'
import { HeritageHome, HeritageGarden, HeritageFeatures } from './components/HeritageHome'
import { ReadingWindow } from './components/ReadingWindow'
import './app.css'
import './styles/celestial.css'
import './styles/workspace.css'
import './styles/immersive.css'
import './styles/dreamscape.css'
import './styles/realms.css'
import './styles/dashboard.css'
import './styles/heritage.css'
import './styles/home-refresh.css'
import './styles/kundali-refresh.css'
import './styles/matchmaking.css'

const TAB_ICONS = ['◇', '✧', '◷', '✦', '♄', '☾', '≋']

const TABS = [
  { key: 'chart', label: 'Chart' },
  { key: 'vargas', label: 'Divisions' },
  { key: 'dasha', label: 'Periods' },
  { key: 'strength', label: 'Yogas & Doshas' },
  { key: 'transits', label: 'Transits' },
  { key: 'panchang', label: 'Panchang' },
  { key: 'reading', label: 'Reading' },
] as const

type TabKey = (typeof TABS)[number]['key']

const BLANK: BirthInput = {
  name: '',
  date: '',
  time: '',
  latitude: NaN,
  longitude: NaN,
  place: '',
  ayanamsa: 'lahiri',
  house_system: 'whole_sign',
  node_type: 'mean',
  time_standard: 'auto',
}

export default function App() {
  const [user, setUser] = useState<Account | null>(null)
  const [authOpen, setAuthOpen] = useState(false)
  const [createAfterLogin, setCreateAfterLogin] = useState(false)
  const changeUser = useCallback((account: Account | null) => {
    setUser(account)
    setAuthOpen(false)
    if (!account) setCreateAfterLogin(false)
  }, [])
  useEffect(() => {
    const syncSession = (event: StorageEvent) => {
      if (event.key !== 'jyotish_token' && event.key !== null) return
      setUser(null)
      api.me().then(setUser).catch(() => setUser(null))
    }
    window.addEventListener('storage', syncSession)
    return () => window.removeEventListener('storage', syncSession)
  }, [])
  return <>
    <Workspace key={user?.id ?? 'guest'} user={user} setUser={changeUser} authOpen={authOpen} startWithChart={!!user && createAfterLogin} onRequireSignIn={() => { setCreateAfterLogin(true); setAuthOpen(true) }} />
    <ReadingWindow open={authOpen && !user} onClose={() => { setAuthOpen(false); setCreateAfterLogin(false) }} title="Sign in to begin" className="signin-window">
      <div className="signin-invitation"><span className="sanskrit-label" lang="sa">स्वागतम्</span><h2>Your story deserves<br />a place of its own.</h2><p><strong>Sign in with Google to create your birth chart.</strong> Keep your charts together and return to them on any device.</p>{authOpen && !user && <GoogleAccount user={null} onChange={changeUser} />}<p className="small muted">One Google account. No password or registration form here.</p></div>
    </ReadingWindow>
  </>
}

function Workspace({ user, setUser, authOpen, startWithChart, onRequireSignIn }: { user: Account | null; setUser: (user: Account | null) => void; authOpen: boolean; startWithChart: boolean; onRequireSignIn: () => void }) {
  const motionPaused = false
  const [birth, setBirth] = useState<BirthInput>(BLANK)
  const library = useChartLibrary(user?.id ?? null)
  const { charts, error: libraryError, persist } = library
  const [activeId, setActiveId] = useState<string | null>(null)
  const [activeBirth, setActiveBirth] = useState<BirthInput>(BLANK)
  const [formVersion, setFormVersion] = useState(0)
  const [matchOpen, setMatchOpen] = useState(window.location.hash === '#matchmaking')
  const [reportOpen, setReportOpen] = useState(window.location.hash === '#reports')
  const [reportChartId, setReportChartId] = useState('')
  const [chatOpen, setChatOpen] = useState(window.location.hash === '#guide')
  const [chartOpen, setChartOpen] = useState(startWithChart || (!!user && window.location.hash === '#chart'))
  const [chartArrival, setChartArrival] = useState(0)
  const [chatChartId, setChatChartId] = useState('')
  const [status, setStatus] = useState('')
  const [removed, setRemoved] = useState<SavedChart | null>(null)
  const requestId = useRef(0)
  const [bundle, setBundle] = useState<Bundle | null>(null)
  const [reference, setReference] = useState<Reference | null>(null)
  const [tab, setTab] = useState<TabKey>('chart')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [panelOpen, setPanelOpen] = useState(true)
  useEffect(() => {
    if (panelOpen && bundle && chartOpen) document.getElementById('birth-editor')?.scrollIntoView({ block: 'start' })
  }, [panelOpen, chartOpen])
  const leaveChart = () => {
    window.history.replaceState(null, '', window.location.pathname + window.location.search)
    setChartOpen(false)
    setChatOpen(false)
    setReportOpen(false)
    setMatchOpen(false)
    window.scrollTo(0, 0)
  }
  useEffect(() => {
    if (!chartOpen) return
    if (window.location.hash !== '#chart') window.history.pushState(null, '', '#chart')
    window.scrollTo(0, 0)
  }, [chartOpen, chartArrival])
  useEffect(() => {
    const followHistory = () => { setMatchOpen(window.location.hash === '#matchmaking'); setReportOpen(window.location.hash === '#reports'); setChatOpen(window.location.hash === '#guide'); setChartOpen(window.location.hash === '#chart' && !!user); window.scrollTo(0, 0) }
    window.addEventListener('popstate', followHistory)
    return () => window.removeEventListener('popstate', followHistory)
  }, [user])


  useEffect(() => {
    document.documentElement.dataset.theme = 'light'
  }, [])

  useEffect(() => {
    api.reference().then(setReference).catch(() => setReference(null))
  }, [])

  useEffect(() => {
    if (activeId && !charts.some(c => c.id === activeId)) setActiveId(null)
  }, [charts, activeId])

  const cast = async () => {
    if (!user) { onRequireSignIn(); return }
    const currentRequest = ++requestId.current
    const input = { ...birth, name: birth.name.trim() || 'Untitled chart' }
    setBusy(true)
    setError(null)
    try {
      const b = await api.chart(input)
      if (currentRequest !== requestId.current) return
      setBundle(b)
      setActiveBirth(input)
      setBirth(input)
      const id = activeId ?? crypto.randomUUID()
      const saved = { id, birth: input, bundle: b, savedAt: new Date().toISOString() }
      const next = activeId ? charts.map(c => c.id === id ? saved : c) : [saved, ...charts]
      if (await persist(next)) { setActiveId(id); setStatus(`${input.name} saved to your collection.`) }
      setChartArrival(v => v + 1)
      setPanelOpen(false)
    } catch (e) {
      if (currentRequest !== requestId.current) return
      setError(e instanceof ApiError ? e.message : 'Could not reach the calculation service.')
    } finally {
      if (currentRequest === requestId.current) setBusy(false)
    }
  }

  const newChart = () => {
    if (!user) { onRequireSignIn(); return }
    ++requestId.current
    setBirth({ ...BLANK })
    setBundle(null)
    setActiveId(null)
    setError(null)
    setStatus('New chart — enter birth details to begin.')
    setPanelOpen(true)
    setTab('chart')
    setFormVersion(v => v + 1)
    setReportOpen(false)
    setMatchOpen(false)
    setChatOpen(false)
    setChartOpen(true)
    setChartArrival(v => v + 1)
  }
  const loadChart = (chart: SavedChart) => {
    ++requestId.current
    setBirth(chart.birth)
    setActiveBirth(chart.birth)
    setBundle(chart.bundle)
    setActiveId(chart.id)
    setFormVersion(v => v + 1)
    setError(null)
    setTab('chart')
    setStatus(`${chart.birth.name} loaded from your collection.`)
    setPanelOpen(false)
    setReportOpen(false)
    setMatchOpen(false)
    setChatOpen(false)
    setChartOpen(true)
    setChartArrival(v => v + 1)
  }
  const renameChart = async (id: string, name: string) => {
    const next = charts.map(c => c.id === id ? { ...c, birth: { ...c.birth, name }, bundle: { ...c.bundle, name } } : c)
    if (!await persist(next)) return
    if (activeId === id) { setBirth(b => ({ ...b, name })); setActiveBirth(b => ({ ...b, name })); setBundle(b => b ? { ...b, name } : b) }
    setStatus(`Chart renamed to ${name}.`)
  }
  const removeChart = async (id: string) => {
    const chart = charts.find(c => c.id === id)
    if (!chart || !await persist(charts.filter(c => c.id !== id))) return false
    setRemoved(chart)
    if (activeId === id) setActiveId(null)
    setStatus(`${chart.birth.name} removed from the collection. You can undo this.`)
    return true
  }

  useEffect(() => () => { ++requestId.current }, [])

  const chatChart = charts.find(c => c.id === chatChartId) ?? null
  const openMatch = () => { setChartOpen(false); setChatOpen(false); setReportOpen(false); setMatchOpen(true); if (window.location.hash !== '#matchmaking') window.history.pushState(null, '', '#matchmaking'); window.scrollTo(0,0) }
  const openReport = (id = '') => { setMatchOpen(false); setReportChartId(id); setChartOpen(false); setChatOpen(false); setReportOpen(true); if (window.location.hash !== '#reports') window.history.pushState(null, '', '#reports'); window.scrollTo(0, 0) }
  const openChat = (id = '') => { setMatchOpen(false); setReportOpen(false); setChatChartId(id); setChartOpen(false); setChatOpen(true); if (window.location.hash !== '#guide') window.history.pushState(null, '', '#guide'); window.scrollTo(0, 0) }

  const signNames = useMemo(
    () => reference?.signs.map((s) => s.name) ?? [],
    [reference],
  )

  return (
    <div className={`app heritage${motionPaused ? ' motion-paused' : ''}`}>
      <header className="topbar no-print">
        <div className="wrap topbar__inner">
          <div className="brand">
            <BrandMark />
            <div className="brand__text">
              <span className="brand__name">Jyotish</span>
              <span className="brand__sub">
                THE ART OF VEDIC ASTROLOGY
              </span>
            </div>
          </div>

          <div className="cluster">
            {!authOpen && <GoogleAccount user={user} onChange={setUser} />}
            <button className="btn btn--sm topbar__match" aria-current={matchOpen ? 'page' : undefined} onClick={openMatch}>Matchmaking</button>
            <button className="btn btn--sm topbar__guide" onClick={() => openChat()}>Chart Guide</button>
            <button className="btn btn--sm topbar__reports" aria-current={reportOpen ? 'page' : undefined} onClick={() => openReport()}>Detailed Reports</button>
            <button className="btn topbar__library" onClick={() => { if (chartOpen || chatOpen || reportOpen || matchOpen) leaveChart(); else document.getElementById('chart-library')?.scrollIntoView({ behavior: 'smooth' }) }}>◇ My charts <span>{charts.length}</span></button>
          </div>
        </div>
      </header>

      {!chartOpen && !chatOpen && !reportOpen && !matchOpen && <>
      <HeritageHome user={user} count={charts.length} onNew={newChart} onChat={() => openChat()} onReport={() => openReport()} onMatch={openMatch} />
      <ChartLibrary accountEmail={user?.email} charts={charts} activeId={activeId} busy={busy || library.loading || !library.ready} onNew={newChart} onReport={openReport} onLoad={loadChart} onRename={renameChart} onRemove={removeChart} />
      <div className="library-feedback wrap no-print">
        {user && <div className="cluster"><span className="small" role="status">{library.loading ? 'Syncing account charts…' : library.ready ? 'Account collection up to date' : 'Account sync unavailable'}</span><button className="btn btn--sm" disabled={busy || library.loading} onClick={() => library.refresh()}>Refresh account charts</button><button className="btn btn--sm" disabled={busy || library.loading || !library.ready} onClick={async () => { if (await library.importLocal()) setStatus('Browser charts imported into your account. The browser copies are still available when signed out.') }}>Import browser charts</button></div>}
        {libraryError && <p className="notice notice--warn" role="alert">{libraryError}</p>}
        {status && <div className="library-status" role="status"><span>✦ {status}</span>{removed && <button className="btn btn--sm" disabled={busy || library.loading || !library.ready} onClick={async () => {
          if (await persist([removed, ...charts])) { setStatus(`${removed.birth.name} restored.`); setRemoved(null) }
        }}>Undo removal</button>}</div>}
      </div>
      <HeritageFeatures onChat={() => openChat()} onReport={() => openReport()} onMatch={openMatch} />
      <HeritageGarden onChat={() => openChat()} />
      </>}
      {chartOpen && <section className={`reading-window chart-page${!bundle ? ' chart-page--create' : ''}${motionPaused ? ' motion-paused' : ''}`}>
      <div className="chart-page__heading wrap"><button className="btn btn--ghost" onClick={leaveChart} disabled={busy}>← Back to my charts</button><p className="eyebrow" lang="sa">जन्मकुण्डली</p><h1>{bundle ? activeBirth.name : 'Create your birth chart'}</h1>{!bundle && <p>A few details about the moment your story began.</p>}</div>
      {bundle && <div className="chart-arrival" key={chartArrival} role="status">{bundle ? `✦ ${activeBirth.name} is open. Your chart is ready to explore.` : '✧ A new story begins with birth details.'}</div>}
      <main className={`layout wrap${bundle ? ' kundali-layout' : ''}${bundle && panelOpen ? ' kundali-layout--editing' : ''}`} id="chart-workspace">
        <aside id="birth-editor" hidden={!!bundle && !panelOpen} className={`panel no-print${panelOpen ? '' : ' is-collapsed'}`}>
          <div className="birth-portal" aria-hidden="true"><span>EVERY MOMENT HAS A SKY</span></div>
          <div className="panel__head">
            <h2 className="panel__title"><span aria-hidden="true">✧</span> Birth details</h2>
            <button
              className="btn btn--ghost btn--sm panel__toggle"
              onClick={() => setPanelOpen((v) => !v)}
              aria-expanded={panelOpen}
            >
              {panelOpen ? 'Done editing' : 'Edit birth details'}
            </button>
          </div>

          {panelOpen && <p className="panel__intro">Every story begins with a moment. Enter yours.</p>}
          {panelOpen && (
            <BirthForm
              key={formVersion}
              simple
              value={birth}
              onChange={setBirth}
              onSubmit={() => cast()}
              reference={reference}
              busy={busy || library.loading || !library.ready}
              submitLabel={activeId ? '✦ Update saved chart' : '✦ Reveal & save chart'}
            />
          )}

          {!panelOpen && bundle && (
            <button className="panel__summary" onClick={() => setPanelOpen(true)}>
              <span className="panel__summary-name">
                {bundle.name || 'Sample birth chart'}
              </span>
              <span className="panel__summary-meta mono tiny">
                {bundle.chart.moment.local.slice(0, 10)}
                {bundle.chart.time_known
                  ? ` · ${bundle.chart.moment.local.slice(11, 16)}`
                  : ' · time unknown'}
              </span>
              <span className="panel__summary-meta tiny dim">{bundle.place}</span>
            </button>
          )}
        </aside>

        <section className="content" aria-busy={busy}>
          {libraryError && <p className="notice notice--warn" role="alert">{libraryError}</p>}
          {error && (
            <div className="notice notice--warn" role="alert">
              <span className="notice__mark">!</span>
              <span>{error}</span>
            </div>
          )}

          {bundle && (
            <>
              <div className="chart-context no-print"><button className="btn btn--sm" aria-expanded={panelOpen} onClick={() => setPanelOpen(v => !v)}>{panelOpen ? 'Close editor' : 'Edit birth details'}</button><button className="btn btn--sm" disabled={!activeId} onClick={() => openReport(activeId ?? '')}>Read full report</button><span>{activeId ? '◈ Saved chart' : '◇ Unsaved preview'}</span><button className="btn btn--sm" disabled={!activeId} onClick={() => openChat(activeId ?? '')}>✦ Explore with Chart Guide</button></div>
              {JSON.stringify(birth) !== JSON.stringify(activeBirth) && <p className="notice notice--info">Birth details have changed. Reveal the chart to update the results below.</p>}
              <ChartHeader bundle={bundle} />
              <details className="kundali-snapshot"><summary>Your chart at a glance <span>Ascendant, Moon & planetary themes</span></summary><CosmicSnapshot bundle={bundle} /></details>

              <nav className="tabs no-print" role="tablist" aria-label="Chart sections">
                {TABS.map((t, i) => (
                  <button
                    key={t.key}
                    role="tab"
                    id={`tab-${t.key}`}
                    aria-controls={`panel-${t.key}`}
                    tabIndex={tab === t.key ? 0 : -1}
                    onKeyDown={(event) => {
                      let next = i
                      if (event.key === 'ArrowRight') next = (i + 1) % TABS.length
                      else if (event.key === 'ArrowLeft') next = (i - 1 + TABS.length) % TABS.length
                      else if (event.key === 'Home') next = 0
                      else if (event.key === 'End') next = TABS.length - 1
                      else return
                      event.preventDefault()
                      setTab(TABS[next].key)
                      document.getElementById(`tab-${TABS[next].key}`)?.focus()
                    }}
                    className="tab"
                    aria-selected={tab === t.key}
                    onClick={() => setTab(t.key)}
                  >
                    <span className="tab__icon" aria-hidden="true">{TAB_ICONS[i]}</span>{t.label}
                  </button>
                ))}
              </nav>

              <div className="views" role="tabpanel" key={tab} id={`panel-${tab}`} aria-labelledby={`tab-${tab}`} tabIndex={0}>
                {tab !== 'chart' && <RealmBanner section={tab} />}
                {tab === 'chart' && <ChartView bundle={bundle} signNames={signNames} />}
                {tab === 'vargas' && <VargaView bundle={bundle} signNames={signNames} />}
                {tab === 'dasha' && <DashaView bundle={bundle} birth={activeBirth} />}
                {tab === 'strength' && <StrengthView bundle={bundle} />}
                {tab === 'transits' && (
                  <TransitView bundle={bundle} birth={activeBirth} signNames={signNames} />
                )}
                {tab === 'panchang' && <PanchangView birth={activeBirth} />}
                {tab === 'reading' && <ReadingView bundle={bundle} />}
              </div>
            </>
          )}

          {!bundle && !busy && <div className="new-chart-welcome"><div aria-hidden="true">✧</div><p className="eyebrow">A new story in your constellation</p><h2>Who will you discover next?</h2><p>Enter a birth date, time if known, and place. Reveal the chart to add it to your collection.</p></div>}
          {!bundle && busy && (
            <div className="empty">
              <span className="spin" />
              <p className="muted" role="status">Mapping your celestial blueprint…</p>
            </div>
          )}
        </section>
      </main>
      </section>}

      {matchOpen && <MatchmakingPage charts={charts} loading={library.loading} libraryError={libraryError} onBack={leaveChart} onNew={newChart} onRetry={() => library.refresh()} />}
      {reportOpen && <ChartReport charts={charts} selectedId={reportChartId} onSelect={setReportChartId} onBack={leaveChart} onGuide={openChat} loading={library.loading} error={libraryError} onRetry={() => library.refresh()} />}
      <AstroChat bundle={chatChart?.bundle ?? null} birth={chatChart?.birth ?? BLANK} userId={user?.id ?? null} chartKey={chatChart ? `${chatChart.id}:${chatChart.bundle.cache_key || JSON.stringify(chatChart.birth)}` : 'none'} charts={charts} selectedId={chatChart?.id ?? ''} onSelect={setChatChartId} open={chatOpen} onClose={leaveChart} motionPaused={motionPaused} />
      {!chatOpen && !reportOpen && !matchOpen && <footer className="footer no-print">
        <div className="wrap">
          <div className="footer-invitation"><span>✦</span><h2>There is a universe in every story.</h2><p>Take your time. Get to know yours.</p></div>
          <p className="tiny dim">
            Positions are sidereal, computed with the Swiss Ephemeris. Charts
            describe tendencies the tradition associates with these placements —
            not events, and not medical, legal or financial advice.
          </p>
        </div>
      </footer>}
    </div>
  )
}

/* --------------------------------------------------------------- fragments */
function ChartHeader({ bundle }: { bundle: Bundle }) {
  const c = bundle.chart
  return (
    <header className="chartheader">
      <div>
        <p className="eyebrow">
          {c.time_known ? 'Rashi chart · D1' : 'Partial chart · time unknown'}
        </p>
        <h2>{c.ascendant_sign_name ? `${c.ascendant_sign_name} rising` : 'Your planetary placements'}</h2>
        <p className="chartheader__meta small muted">
          <span className="mono">{c.moment.local.slice(0, 10)}</span>
          {c.time_known && (
            <>
              {' '}
              at <span className="mono">{c.moment.local.slice(11, 19)}</span>
            </>
          )}
          {bundle.place && <> · {bundle.place}</>}
          {' · '}
          <span className="mono">{c.moment.utc_offset_label}</span>{' '}
          <span className="dim">{c.moment.tz_abbrev}</span>
        </p>
      </div>

      <details className="chartheader-technical"><summary>Calculation details · ayanamsha, ascendant & Moon</summary><dl className="chartheader__stats">
        <div>
          <dt>Ayanamsa</dt>
          <dd className="mono">{c.ayanamsa_str}</dd>
          <dd className="tiny dim">{c.ayanamsa_label}</dd>
        </div>
        {c.time_known && (
          <div>
            <dt>Lagna</dt>
            <dd className="mono">{c.ascendant_degree_str}</dd>
            <dd className="tiny dim">
              {c.ascendant_nakshatra} pada {c.ascendant_pada}
            </dd>
          </div>
        )}
        <div>
          <dt>Moon</dt>
          <dd className="mono">
            {c.planets.Moon.degree_str} {c.planets.Moon.sign_name}
          </dd>
          <dd className="tiny dim">
            {c.planets.Moon.nakshatra_name} pada {c.planets.Moon.pada}
          </dd>
        </div>
      </dl></details>

      {c.warnings.length > 0 && (
        <div className="chartheader__warnings">
          {c.warnings.map((w, i) => (
            <div key={i} className="notice notice--warn">
              <span className="notice__mark">!</span>
              <span>{w}</span>
            </div>
          ))}
        </div>
      )}
    </header>
  )
}

function BrandMark() {
  /* The North Indian figure, reduced to its lines. */
  return (
    <svg width="30" height="30" viewBox="0 0 100 100" aria-hidden="true" className="brand__mark">
      <rect x="2" y="2" width="96" height="96" fill="none" stroke="currentColor" strokeWidth="4" />
      <path
        d="M2 2 L98 98 M98 2 L2 98 M50 2 L98 50 L50 98 L2 50 Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="4"
      />
    </svg>
  )
}


function RealmBanner({ section }: { section: Exclude<TabKey, 'chart'> }) {
  const realms = {
    vargas: { art: 'rising', title: 'The many dimensions of you', note: 'Explore the divisional charts and their different perspectives.' },
    dasha: { art: 'sun', title: 'Every season has its rhythm', note: 'Follow the planetary periods that shape a Vedic timeline.' },
    strength: { art: 'sun', title: 'Patterns of possibility', note: 'Discover the planetary combinations recorded in your chart.' },
    transits: { art: 'rising', title: 'A sky that never stands still', note: 'Explore planetary movements in relation to your birth chart.' },
    panchang: { art: 'moon', title: 'Tune into the rhythm of the day', note: 'Explore the five elements of the traditional Vedic calendar.' },
    reading: { art: 'moon', title: 'A little closer to yourself', note: 'Reflect on the interpretations associated with your placements.' },
  }
  const realm = realms[section]
  return <div className={`realm-banner realm-banner--${realm.art}`}><p className="eyebrow">EXPLORE YOUR COSMIC STORY</p><h2>{realm.title}</h2><p>{realm.note}</p></div>
}
