import { useEffect, useRef, useState } from 'react'
import { api, ApiError } from '../api/client'
import type { MatchResult } from '../api/types'
import type { SavedChart } from './ChartLibrary'

const CONTEXT: Record<string, [string, string]> = {
  Varna: ['Outlook & priorities', 'Discuss what a meaningful life looks like to each of you. These historical Moon-sign categories do not describe caste, status or personal worth.'],
  Vashya: ['Cooperation', 'Talk about how you share decisions and respect each other’s independence.'],
  Tara: ['Shared rhythms', 'Discuss how you support one another during change and how you like to recharge.'],
  Yoni: ['Comfort & closeness', 'Share your boundaries and preferences with care. Consent and communication matter more than a symbolic pairing.'],
  'Graha Maitri': ['Communication & friendship', 'Make time to listen without trying to solve everything immediately.'],
  Gana: ['Temperament', 'Notice your different responses to stress and agree on a kind way to pause disagreements.'],
  Bhakoot: ['Life direction', 'Discuss home, work, money and family expectations openly, at a pace that suits both of you.'],
  Nadi: ['Traditional lunar grouping', 'Use this as a conversation prompt, never a conclusion about health, fertility or future children.'],
}

export function WeddingPortrait({ bride = false }: { bride?: boolean }) {
  return <svg className="wedding-portrait" viewBox="0 0 180 190" role="img" aria-label={bride ? 'Illustration of a bride wearing a veil' : 'Illustration of a groom wearing a turban'}>
    <circle cx="90" cy="91" r="78" fill={bride ? '#f2dedc' : '#dce9e5'} />
    <circle cx="90" cy="91" r="65" fill="none" stroke="#c7ab73" strokeDasharray="2 7" />
    {bride ? <><path d="M35 174V80C35 12 145 12 145 80V174Z" fill="#a45b6a"/><path d="M43 172V82C43 24 137 24 137 82V172" fill="none" stroke="#e8c68d" strokeWidth="4"/><path d="M47 181c0-66 86-66 86 0" fill="#803c53"/></> : <path d="M36 182c0-77 108-77 108 0" fill="#2e625b"/>}
    <path d="M78 115v22q12 17 24 0v-22" fill="#bc8867"/>
    <ellipse cx="90" cy="85" rx="31" ry="40" fill="#d8a582"/>
    {bride ? <><path d="M58 76c-2-42 66-42 64 0-12-9-23-13-32-29-7 15-19 24-32 29" fill="#342b29"/><path d="M90 43v21" stroke="#f6dba0" strokeWidth="3"/><circle cx="90" cy="65" r="5" fill="#e3b75f"/><circle cx="90" cy="77" r="2" fill="#993c4c"/><circle cx="56" cy="101" r="5" fill="#eac983"/><circle cx="124" cy="101" r="5" fill="#eac983"/></> : <><path d="M56 69Q47 27 92 29q49 0 34 41Z" fill="#f3dfb1"/><path d="M57 55l64-11M58 65l65-14M64 40l53 23" stroke="#c4a46c" strokeWidth="3"/><path d="M91 29q-6-20 9-23l4 23" fill="#b89a65"/><circle cx="91" cy="58" r="5" fill="#b95e55"/></>}
    <path d="M72 86h8m20 0h8" stroke="#46332d" strokeWidth="2" strokeLinecap="round"/><path d="M85 103q5 5 10 0" fill="none" stroke="#9a5d4f" strokeWidth="2" strokeLinecap="round"/>
    <path d="M64 143q26 27 52 0" fill="none" stroke="#edcd83" strokeWidth="4"/>
    {!bride && <><path d="M90 145v38" stroke="#ddc691" strokeWidth="2"/><circle cx="97" cy="158" r="2" fill="#eacf99"/><circle cx="97" cy="170" r="2" fill="#eacf99"/></>}
    <path d="M51 155l7 7m64-7l7 7" stroke="#ecd59f" strokeWidth="2"/>
  </svg>
}

export function MatchmakingPage({ charts, loading, libraryError, onBack, onNew, onRetry }: { charts: SavedChart[]; loading: boolean; libraryError: string|null; onBack:()=>void; onNew:()=>void; onRetry:()=>void }) {
  const [groomId, setGroomId] = useState('')
  const [brideId, setBrideId] = useState('')
  const [result, setResult] = useState<MatchResult|null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const request = useRef(0)
  const resultHeading = useRef<HTMLHeadingElement>(null)
  const groom = charts.find(c=>c.id===groomId)
  const bride = charts.find(c=>c.id===brideId)
  const signature = JSON.stringify([groom?.birth,bride?.birth])
  useEffect(()=>{request.current++;setResult(null);setError('');setBusy(false)},[signature])
  useEffect(()=>()=>{request.current++},[])
  useEffect(()=>{if(result){resultHeading.current?.scrollIntoView({block:'start'});resultHeading.current?.focus({preventScroll:true})}},[result])
  const canRun = !!groom && !!bride && groom.id!==bride.id && !loading && !busy
  const compare = async () => {
    if(!canRun || !groom || !bride) return
    const ticket = ++request.current
    setBusy(true);setError('');setResult(null)
    try {
      // Stable role labels also avoid duplicate display names overwriting API map entries.
      const data = await api.match({...groom.birth,name:'Groom / Bar'}, {...bride.birth,name:'Bride / Badhu'},groom.birth.ayanamsa)
      if(ticket===request.current) setResult(data)
    } catch(e) {if(ticket===request.current)setError(e instanceof ApiError?e.message:'The comparison could not load. Please try again.')}
    finally {if(ticket===request.current)setBusy(false)}
  }
  return <main className="milan-page"><div className="milan-wrap">
    <div className="milan-top"><button className="btn" onClick={onBack}>← My charts</button><span>RELATIONSHIPS · KUNDALI MILAN</span><button className="btn" onClick={onNew}>＋ Create a chart</button></div>
    <header className="milan-heading"><p className="eyebrow" lang="sa">कुण्डली मिलान · TWO STORIES, ONE CONVERSATION</p><h1>Understand your connection.</h1><p>A thoughtful look at traditional compatibility.<br/><strong>Choose both charts. Explore the reasons, not just the number.</strong></p></header>
    {libraryError && <div className="milan-notice" role="alert">{libraryError} <button className="btn" onClick={onRetry}>Reload charts</button></div>}
    <div className="milan-partners">
      {[{bride:false,id:groomId,set:setGroomId,person:groom,other:brideId},{bride:true,id:brideId,set:setBrideId,person:bride,other:groomId}].map(side=><section className={`milan-person ${side.bride?'milan-person--bride':''}`} key={String(side.bride)}>
        <div className="milan-person-heading"><WeddingPortrait bride={side.bride}/><div><p lang="sa">{side.bride?'वधू':'वर'}</p><h2>{side.bride?'Badhu · Bride':'Bar · Groom'}</h2><span>{side.bride?'The bride’s saved birth chart':'The groom’s saved birth chart'}</span></div></div>
        <label htmlFor={side.bride?'bride-chart':'groom-chart'}>{side.bride?'Choose the bride’s chart':'Choose the groom’s chart'}</label>
        <select id={side.bride?'bride-chart':'groom-chart'} value={side.person?side.id:''} disabled={loading||busy} onChange={e=>{request.current++;setResult(null);setError('');side.set(e.target.value)}}><option value="">{loading?'Loading saved charts…':'Select a saved chart'}</option>{charts.map(c=><option key={c.id} value={c.id} disabled={c.id===side.other}>{c.birth.name} · {c.birth.date}</option>)}</select>
        {side.person?<div className="milan-birth"><strong>{side.person.birth.name}</strong><span>{side.person.birth.date} · {side.person.birth.time?.slice(0,5)||'Birth time unknown'}</span><span>{side.person.birth.place}</span></div>:<p className="milan-selection-note">No chart selected yet. Your collection stays unchanged.</p>}
      </section>)}
    </div>
    {!loading && charts.length<2 && <p className="milan-notice"><strong>You’ll need two saved charts.</strong> Create the missing chart, then return here to compare.</p>}
    <div className="milan-action"><button className="btn btn--primary" disabled={!canRun} onClick={compare}>{busy?'Comparing your charts…':'Reveal compatibility report ↗'}</button><p role="status">{busy?'मननम् · Preparing the eight-part comparison.':'Eight kootas · 36 possible points · Each result explained'}</p></div>
    {error && <div className="milan-notice" role="alert">{error}<button className="btn" disabled={!canRun} onClick={compare}>Try again</button></div>}
    {!result && !busy && <section className="milan-intro"><span aria-hidden="true">✧</span><h2>A starting point for understanding.</h2><p>Ashtakoot compares the Moon placements in two birth charts. It is a traditional framework, not a measure of love, consent or the quality of a relationship.</p></section>}
    {result && groom && bride && <section className="milan-results" aria-labelledby="milan-result-title">
      <h2 ref={resultHeading} tabIndex={-1} id="milan-result-title">{groom.birth.name} & {bride.birth.name}</h2><p className="milan-result-sub">Your compatibility report · {groom.birth.ayanamsa} ayanamsha applied to both charts</p>
      <div className="milan-score-card"><div className="milan-score-ring" style={{background:`conic-gradient(#487e75 ${result.percent}%, #dce6e3 0)`}}><div><strong>{result.total}</strong><span>out of {result.maximum}</span></div></div><div><p className="eyebrow">ASHTAKOOT GUNA MILAN</p><h3>{result.total>=26?'Many points of traditional alignment':result.total>=18?'Shared ground, with room to grow':'Take time to explore your differences'}</h3><p>{result.total} of {result.maximum} points are awarded by this method. {result.total>=18?'This meets the commonly used 18-point reference.':'This is below the commonly used 18-point reference; it is not a verdict on your relationship.'}</p><strong>The score is not a percentage chance of a successful marriage.</strong><p>Mutual care, shared values and honest conversation remain essential.</p></div></div>
      {(!groom.birth.time||!bride.birth.time)&&<p className="milan-notice"><strong>Provisional result: birth time is missing.</strong> The Moon can change sign or nakshatra during a day, which can change the score. Add accurate times before relying on this comparison. The Mars cross-check is withheld.</p>}
      <div className="milan-section-heading"><p className="eyebrow">THE REASONS BEHIND THE NUMBER</p><h2>Eight perspectives on your pairing.</h2><p>Each card shows its points, the calculation context and a practical conversation to try.</p></div>
      <div className="milan-kootas">{result.kootas.map((k,i)=><article className="milan-koota" key={k.koota}><div className="milan-koota-heading"><span>0{i+1} · {k.koota}</span><strong>{k.score}<small> / {k.max}</small></strong></div><h3>{CONTEXT[k.koota]?.[0]||k.koota}</h3><div className="milan-meter" role="meter" aria-label={`${k.koota} score`} aria-valuenow={k.score} aria-valuemin={0} aria-valuemax={k.max}><span style={{width:`${k.score/k.max*100}%`}}/></div><p className="milan-score-label">{k.score===k.max?'Full points in this check':k.score>0?'Some points of alignment':'No points awarded in this check'}</p><p>{k.explanation}</p>{k.detail&&<details><summary>How to read this check</summary><p>{k.detail}</p></details>}{!!k.cancellations?.length&&<div className="milan-exceptions"><strong>Additional context</strong><ul>{k.cancellations.map(c=><li key={c}>{c}</li>)}</ul><small>These exceptions provide context; they do not add points to the displayed total.</small></div>}<div className="milan-conversation"><strong>A conversation to try</strong><p>{CONTEXT[k.koota]?.[1]||'Talk about your expectations with openness and care.'}</p></div></article>)}</div>
      <section className="milan-extra"><h2>Mars placement · additional context</h2>{groom.birth.time&&bride.birth.time?<><p>This cross-check is separate from the 36-point score. {result.manglik.verdict==='clear'?'Neither chart has an active Manglik indication in this calculation.':result.manglik.verdict==='balanced'?'Both charts have an active Manglik indication; traditional practice often considers this a balancing factor.':'The charts differ in their Manglik indication. Consider the individual placements and listed exceptions without treating this as a prediction of harm.'}</p><div className="milan-mars-grid">{(['first','second'] as const).map((side,i)=><div key={side}><strong>{i===0?groom.birth.name:bride.birth.name}</strong><p>{result.manglik[side].present?'Indication present':'No active indication'}</p>{result.manglik[side].cancellations.map(c=><p key={c} className="milan-small">{c}</p>)}</div>)}</div></>:<p>An accurate birth time is needed for both charts before displaying this house-based check.</p>}</section>
      <section className="milan-extra"><h2>The Moon placements behind this report</h2><div className="milan-mars-grid">{Object.entries(result.people).map(([role,p])=><div key={role}><strong>{role}</strong><p>{p.moon_sign} · {p.nakshatra} · Pada {p.pada}</p><span className="milan-small">Gana: {p.gana} · Nadi: {p.nadi} · Yoni: {p.yoni}</span></div>)}</div><p className="milan-small">The groom is the first chart and the bride is the second. Some traditional tables depend on this order. The eight kootas use Moon positions; the separate Mars check uses house placements. The score does not assess the whole relationship or the full birth charts.</p></section>
    </section>}
  </div></main>
}
