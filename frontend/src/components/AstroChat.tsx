import { useEffect, useRef, useState } from 'react'
import { api, ApiError } from '../api/client'
import type { BirthInput, Bundle } from '../api/types'
import type { SavedChart } from './ChartLibrary'

interface Message { role: 'user' | 'assistant'; text: string }
const PROMPTS = ['Give me a detailed chart reading', 'What are my natural strengths?', 'Help me understand my emotional needs', 'What can I focus on in this life period?']

export function AstroChat({ bundle, birth, userId, chartKey, open, onClose, charts, selectedId, onSelect, motionPaused }: {
  bundle: Bundle | null; birth: BirthInput; userId: number | null; chartKey: string; open: boolean; onClose: () => void
  charts: SavedChart[]; selectedId: string; onSelect: (id: string) => void; motionPaused: boolean
}) {
  const [conversations, setConversations] = useState<Record<string, Message[]>>({})
  const [draft, setDraft] = useState('')
  const [pending, setPending] = useState(false)
  const [pendingQuestion, setPendingQuestion] = useState('')
  const [error, setError] = useState('')
  const controller = useRef<AbortController | null>(null)
  const latestReply = useRef<HTMLDivElement>(null)
  const pendingTurn = useRef<HTMLDivElement>(null)
  const followReply = useRef(true)
  const revealReply = useRef(false)
  const [unread, setUnread] = useState(false)
  const messages = conversations[chartKey] ?? []
  useEffect(() => {
    controller.current?.abort(); controller.current = null
    revealReply.current = false
    setDraft(''); setPending(false); setPendingQuestion(''); setError(''); setUnread(false)
    return () => { controller.current?.abort(); controller.current = null }
  }, [chartKey, userId])
  useEffect(() => { setConversations({}) }, [userId])
  useEffect(() => {
    if (!pending) return
    pendingTurn.current?.scrollIntoView({ block: 'start', behavior: 'instant' })
    const readingElsewhere = () => { followReply.current = false }
    const keyboardScroll = (event: KeyboardEvent) => { if (['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End'].includes(event.key)) readingElsewhere() }
    window.addEventListener('wheel', readingElsewhere, { passive: true })
    window.addEventListener('touchmove', readingElsewhere, { passive: true })
    window.addEventListener('keydown', keyboardScroll)
    return () => { window.removeEventListener('wheel', readingElsewhere); window.removeEventListener('touchmove', readingElsewhere); window.removeEventListener('keydown', keyboardScroll) }
  }, [pending])
  useEffect(() => {
    if (!messages.length || !revealReply.current) return
    revealReply.current = false
    if (followReply.current) latestReply.current?.scrollIntoView({ block: 'start', behavior: 'instant' })
    else setUnread(true)
  }, [messages.length, chartKey])
  const send = async (text: string) => {
    const question = text.trim().slice(0, 1000)
    if (!question || controller.current || !bundle || !userId) return
    const request = new AbortController()
    controller.current = request
    followReply.current = true; setUnread(false)
    setDraft(''); setError(''); setPendingQuestion(question); setPending(true)
    try {
      const result = await api.chat(birth, question, messages.slice(-12), request.signal)
      if (controller.current !== request) return
      revealReply.current = true
      setConversations(prev => ({ ...prev, [chartKey]: [...(prev[chartKey] ?? []), { role: 'user', text: question }, { role: 'assistant', text: result.reply }] }))
    } catch (e) {
      if (controller.current !== request || request.signal.aborted) return
      setDraft(question)
      setError(e instanceof ApiError ? e.message : 'Could not reach chart chat. Please try again.')
    } finally {
      if (controller.current === request) { controller.current = null; setPending(false) }
    }
  }
  if (!open) return null
  const unavailable = !bundle || !userId
  return <main className={`guide-page ${motionPaused ? 'motion-paused' : ''}`}>
    <div className="guide-shell">
      <nav className="guide-nav" aria-label="Guide navigation"><button className="btn btn--ghost" onClick={onClose}>← Back to my charts</button><details className="guide-options"><summary>About this guide</summary><p>Your calculated chart placements and messages are sent to Google Gemini. Responses are for reflection and can be mistaken. Conversations stay in this page session.</p><button className="btn" disabled={pending || !messages.length} onClick={() => { setConversations(prev => ({ ...prev, [chartKey]: [] })); setError(''); setUnread(false) }}>Clear this conversation</button></details></nav>
      <header className="guide-heading"><p className="eyebrow"><span lang="sa">संवादः</span> · UNDERSTAND YOUR CHART</p><h1>Chart Guide</h1><p>A little clarity, one question at a time.</p></header>
      <div className="guide-chart"><label htmlFor="chat-chart-select">{bundle ? 'Your selected chart' : 'Start here · Choose a saved chart'}</label><select id="chat-chart-select" value={selectedId} onChange={e => onSelect(e.target.value)}><option value="">Select a saved chart…</option>{charts.map(c => <option key={c.id} value={c.id}>{c.birth.name} · {c.birth.date}</option>)}</select></div>
      {unavailable ? <section className="guide-empty" id="chat-prerequisite"><span aria-hidden="true">✧</span><h2>{!userId ? 'Sign in to explore your chart' : charts.length ? 'Choose a chart to begin' : 'Your first chart comes first'}</h2><p>{!userId ? 'Use Google sign-in at the top of the page, then select a saved chart.' : charts.length ? 'Choose whose chart you’d like to explore using the selector above. Then bring your questions here.' : 'Create and save a birth chart from your collection. Your guide will be ready when you return.'}</p>{!charts.length && <button className="btn" onClick={onClose}>Go to my charts</button>}</section> : <>
      {!messages.length && !pending && <section className="guide-welcome"><h2>What would you like to understand?</h2><p>Explore <strong>{bundle.name}’s chart</strong> with a question of your own, or start here.</p><div className="guide-starters">{PROMPTS.slice(0, 3).map(p => <button key={p} onClick={() => send(p)}>{p}<span aria-hidden="true">↗</span></button>)}</div></section>}
      <section className="guide-conversation" aria-label="Chart conversation">
        {messages.map((m, i) => <article key={i} ref={i === messages.length - 1 ? latestReply : undefined} className={`guide-message guide-message--${m.role}`}><p className="guide-speaker">{m.role === 'user' ? 'Your question' : 'Chart Guide'}</p><ChatReply text={m.text} /></article>)}
        {pending && <div ref={pendingTurn} className="guide-pending"><article className="guide-message guide-message--user"><p className="guide-speaker">Your question</p><p>{pendingQuestion}</p></article><ChatThinking /></div>}
        {error && <p className="guide-error" role="alert">{error}</p>}
      </section>
      </>}
      {unread && <button className="guide-new-reply" onClick={() => { latestReply.current?.scrollIntoView({ block: 'start', behavior: 'instant' }); setUnread(false) }}>Your response is ready · Read from the beginning ↓</button>}
      <form className="guide-composer" onSubmit={e => { e.preventDefault(); send(draft) }}><label htmlFor="chat-message">Your question</label><div><textarea id="chat-message" value={draft} onChange={e => setDraft(e.target.value)} disabled={pending || unavailable} maxLength={1000} rows={2} aria-describedby={unavailable ? 'chat-prerequisite' : undefined} placeholder={!userId ? 'Sign in to continue' : !bundle ? 'Select a saved chart above' : 'What would you like to know about this chart?'} /><button className="btn btn--primary" disabled={pending || unavailable || !draft.trim()} type="submit">{pending ? 'Preparing…' : 'Send question ↑'}</button></div><p>AI-assisted reflection · Powered by Gemini</p></form>
      <span className="sr-only" role="status">{!pending && messages.length ? 'Your chart response is ready.' : ''}</span>
    </div>
  </main>
}

// Text and emphasis only: model output is never inserted as HTML.
function ChatReply({ text }: { text: string }) {
  return <div className="chat-reply">{text.split('\n').map((line, i) => {
    const heading = /^#{1,4}\s+/.test(line) || /^\*\*[^*]+\*\*:?$/.test(line.trim())
    const content = line.replace(/^#{1,4}\s+/, '').split(/(\*\*[^*]+\*\*)/g).map((part, j) => part.startsWith('**') && part.endsWith('**') ? <strong key={j}>{part.slice(2, -2)}</strong> : part)
    return heading ? <h3 key={i}>{content}</h3> : <p key={i}>{content || <br />}</p>
  })}</div>
}

function ChatThinking() {
  const [phase, setPhase] = useState(0)
  useEffect(() => {
    const timer = window.setInterval(() => setPhase(v => (v + 1) % 3), 4000)
    return () => window.clearInterval(timer)
  }, [])
  const labels = [['चिन्तनम्', 'Thinking'], ['मननम्', 'Reflecting'], ['विमर्शः', 'Considering']]
  return <div className="chat-thinking" role="status"><span className="thinking-mandala" aria-hidden="true">✺</span><div><strong><span lang="sa">{labels[phase][0]}</span><span className="thinking-dots" aria-hidden="true"><i /><i /><i /></span></strong><p>{labels[phase][1]} · Preparing your chart response</p></div></div>
}
