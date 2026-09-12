import { useEffect, useRef, useState } from 'react'
import { api, ApiError } from '../api/client'
import type { BirthInput, Bundle } from '../api/types'

interface Message { role: 'user' | 'assistant'; text: string }
const PROMPTS = ['Give me a detailed chart reading', 'What are my natural strengths?', 'Help me understand my emotional needs', 'What can I focus on in this life period?']

export function AstroChat({ bundle, birth, userId, chartKey, open, onClose }: {
  bundle: Bundle | null; birth: BirthInput; userId: number | null; chartKey: string; open: boolean; onClose: () => void
}) {
  const [conversations, setConversations] = useState<Record<string, Message[]>>({})
  const [draft, setDraft] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  const controller = useRef<AbortController | null>(null)
  const log = useRef<HTMLDivElement>(null)
  const close = useRef<HTMLButtonElement>(null)
  const messages = conversations[chartKey] ?? []
  useEffect(() => {
    controller.current?.abort(); controller.current = null
    setDraft(''); setPending(false); setError('')
    return () => { controller.current?.abort(); controller.current = null }
  }, [chartKey, userId])
  useEffect(() => { setConversations({}) }, [userId])
  useEffect(() => { if (open) close.current?.focus() }, [open])
  useEffect(() => { if (log.current) log.current.scrollTop = log.current.scrollHeight }, [messages.length, pending, open, error])
  const send = async (text: string) => {
    const question = text.trim().slice(0, 1000)
    if (!question || controller.current || !bundle || !userId) return
    const request = new AbortController()
    controller.current = request
    setDraft(''); setError(''); setPending(true)
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
  return <aside className="astro-chat no-print" aria-labelledby="chat-title" onKeyDown={e => { if (e.key === 'Escape') onClose() }}>
    <header className="astro-chat__header"><div className="astro-chat__orb" aria-hidden="true">✦</div><div><h2 id="chat-title">Ask the stars</h2><p>Chart conversations <span>GEMINI</span></p></div><button ref={close} className="btn btn--ghost" onClick={onClose} aria-label="Close chat">×</button></header>
    <div className="astro-chat__context">◇ {bundle?.name || (bundle ? 'Sample birth chart' : 'No chart selected')}<span>Chart context</span></div>
    <div className="astro-chat__log" ref={log} role="log" aria-live="polite" aria-relevant="additions text" aria-label="Chart conversation">
      <div className="chat-message chat-message--assistant"><span>✦ JYOTISH GUIDE</span><p>Let’s explore {bundle?.name ? `${bundle.name}’s chart` : 'your chart'} together. Ask for a detailed reading, discover your strengths, or bring a question that’s on your mind.</p><p className="chat-disclosure">Sending a message shares your calculated chart placements and this conversation with Google Gemini. AI can make mistakes; interpretations are for reflection. Conversations last for this page session.</p></div>
      {messages.map((m, i) => <div key={i} className={`chat-message chat-message--${m.role}`}><span>{m.role === 'user' ? 'YOU' : '✦ JYOTISH GUIDE'}</span><p style={{ whiteSpace: 'pre-wrap' }}>{m.text}</p></div>)}
      {pending && <p className="chat-typing" role="status">✦ Reading your chart…</p>}
      {error && <p role="alert">{error}</p>}
      {unavailable && <p>{!userId ? 'Sign in with Google at the top of the page to chat.' : 'Create or open a chart to begin.'}</p>}
    </div>
    <div className="chat-prompts">{PROMPTS.map(p => <button key={p} onClick={() => send(p)} disabled={pending || unavailable}>{p}</button>)}</div>
    <form className="chat-composer" onSubmit={e => { e.preventDefault(); send(draft) }}><label className="sr-only" htmlFor="chat-message">Message the guide</label><input id="chat-message" value={draft} onChange={e => setDraft(e.target.value)} disabled={pending || unavailable} maxLength={1000} placeholder="Ask about your chart…" autoComplete="off" /><button className="btn btn--primary" disabled={pending || unavailable || !draft.trim()} aria-label="Send message">↑</button></form>
    <div className="chat-footer"><span>Powered by Gemini</span><button disabled={pending || !messages.length} onClick={() => { setConversations(prev => ({ ...prev, [chartKey]: [] })); setError('') }}>Clear chat</button></div>
  </aside>
}
