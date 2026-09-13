import { useEffect, useRef, useState } from 'react'
import { api, ApiError } from '../api/client'
import type { BirthInput, Bundle } from '../api/types'
import type { SavedChart } from './ChartLibrary'
import { ReadingWindow } from './ReadingWindow'

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
  const log = useRef<HTMLDivElement>(null)
  const messages = conversations[chartKey] ?? []
  useEffect(() => {
    controller.current?.abort(); controller.current = null
    setDraft(''); setPending(false); setPendingQuestion(''); setError('')
    return () => { controller.current?.abort(); controller.current = null }
  }, [chartKey, userId])
  useEffect(() => { setConversations({}) }, [userId])
  useEffect(() => { if (log.current) log.current.scrollTop = log.current.scrollHeight }, [messages.length, pending, open, error])
  const send = async (text: string) => {
    const question = text.trim().slice(0, 1000)
    if (!question || controller.current || !bundle || !userId) return
    const request = new AbortController()
    controller.current = request
    setDraft(''); setError(''); setPendingQuestion(question); setPending(true)
    try {
      const result = await api.chat(birth, question, messages.slice(-12), request.signal)
      if (controller.current !== request) return
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
  return <ReadingWindow open={open} onClose={onClose} title="A conversation with the stars" className={`chat-reading-window ${motionPaused ? 'motion-paused' : ''}`}>
    <div className="chat-sanctuary">
    <aside className="chat-sanctuary__guide"><p className="eyebrow"><span lang="sa">संवादः</span> · YOUR PERSONAL GUIDE</p><h2>Insight begins<br /><em>with your story.</em></h2><p>Choose a saved chart, then explore its meaning together.</p><label htmlFor="chat-chart-select"><strong>{bundle ? 'Selected birth chart' : 'Step 1 · Select your saved chart'}</strong></label><select id="chat-chart-select" className={!bundle ? 'chart-select-required' : ''} value={selectedId} onChange={e => onSelect(e.target.value)}><option value="">Select a saved chart…</option>{charts.map(c => <option key={c.id} value={c.id}>{c.birth.name} · {c.birth.date}</option>)}</select>{!charts.length && <p className="small">Create and save a birth chart first. It will appear here.</p>}<img src="/art/rishi-garden-v1.webp" alt="Rishi reflecting beside a sacred fire and lotus pond" /><p className="tiny">Thoughtful guidance, grounded in your selected chart.</p></aside>
    <section className="astro-chat no-print" aria-label="Chart chat">
    <div className="astro-chat__context">◇ {bundle?.name || 'Select a chart to begin'}<span>GEMINI GUIDE</span></div>
    <div className="astro-chat__log" ref={log} role="log" aria-live="polite" aria-relevant="additions text" aria-label="Chart conversation">
      <div className="chat-message chat-message--assistant"><span>✦ JYOTISH GUIDE</span><p>{bundle ? `Let’s explore ${bundle.name}’s chart together. Ask for a detailed reading, discover your strengths, or bring a question that’s on your mind.` : 'Welcome to your space for reflection. Choose a saved chart to start a personal conversation.'}</p><p className="chat-disclosure">Sending a message shares your calculated chart placements and this conversation with Google Gemini. AI can make mistakes; interpretations are for reflection. Conversations last for this page session.</p></div>
      {messages.map((m, i) => <div key={i} className={`chat-message chat-message--${m.role}`}><span>{m.role === 'user' ? 'YOU' : '✦ JYOTISH GUIDE'}</span><ChatReply text={m.text} /></div>)}
      {pending && <><div className="chat-message chat-message--user"><span>YOU</span><p>{pendingQuestion}</p></div><ChatThinking /></>}
      {error && <p role="alert">{error}</p>}

    </div>
    {unavailable && <div className="chat-action-notice" role="status" id="chat-prerequisite"><span aria-hidden="true">✧</span><div><strong>{!userId ? 'Sign in with Google to start chatting' : 'Select a saved chart to unlock chat'}</strong><p>{!userId ? 'Close this window and use Google sign-in at the top of the page.' : charts.length ? 'Your message box becomes available as soon as you choose a chart.' : 'Create and save your first birth chart, then return here.'}</p>{!!userId && charts.length > 0 && <button onClick={() => document.getElementById('chat-chart-select')?.focus()}>Choose my chart ↑</button>}</div></div>}
    <div className="chat-prompts">{PROMPTS.map(p => <button key={p} onClick={() => send(p)} disabled={pending || unavailable}>{p}</button>)}</div>
    <form className="chat-composer" onSubmit={e => { e.preventDefault(); send(draft) }}><label className="sr-only" htmlFor="chat-message">Message the guide</label><input id="chat-message" value={draft} onChange={e => setDraft(e.target.value)} disabled={pending || unavailable} maxLength={1000} aria-describedby={unavailable ? 'chat-prerequisite' : undefined} placeholder={!userId ? 'Sign in with Google to chat' : !bundle ? 'Select a saved chart first' : 'Ask about your chart…'} autoComplete="off" /><button className="btn btn--primary" disabled={pending || unavailable || !draft.trim()} aria-label="Send message">↑</button></form>
    <div className="chat-footer"><span>Powered by Gemini</span><button disabled={pending || !messages.length} onClick={() => { setConversations(prev => ({ ...prev, [chartKey]: [] })); setError('') }}>Clear chat</button></div>
  </section></div></ReadingWindow>
}

// Text and emphasis only: model output is never inserted as HTML.
function ChatReply({ text }: { text: string }) {
  return <div className="chat-reply">{text.split('\n').map((line, i) => {
    const heading = /^#{1,4}\s+/.test(line)
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
