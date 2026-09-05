import { useEffect, useRef, useState } from 'react'
import type { Bundle } from '../api/types'

interface Message { role: 'user' | 'assistant'; text: string }
const PROMPTS = ['Give me a chart overview', 'Tell me about my Moon', 'What is my rising sign?', 'Explain my nakshatra']

// Deliberately deterministic demo: no model, fetch, or external service.
export function demoReply(question: string, bundle: Bundle | null): string {
  if (!bundle) return 'Create or open a saved chart first, and I can show you a demo overview of its Sun, Moon, rising sign, and nakshatra.'
  const c = bundle.chart
  const moon = c.planets.Moon
  const sun = c.planets.Sun
  const q = question.toLowerCase()
  if (/nakshatra|birth star/.test(q)) return `Your Moon is in ${moon.nakshatra_name}, pada ${moon.pada}. Its nakshatra lord is ${moon.nakshatra_lord}. Nakshatras are the 27 lunar divisions used in Vedic astrology. You can select the Moon in your chart to explore more of its recorded details.${c.time_known ? '' : ' Your birth time is unknown, so this midday Moon placement is approximate.'}`
  if (/moon|emotion|feeling/.test(q)) return `Your Moon is in ${moon.sign_name} at ${moon.degree_str}, in ${moon.nakshatra_name}. In Vedic astrology, the Moon is traditionally associated with the mind, emotions, and familiar rhythms. A reflection prompt: what helps you feel settled and at home?${c.time_known ? '' : ' Because your birth time is unknown, this placement uses midday and may change with the actual time.'}`
  if (/rising|ascendant|lagna/.test(q)) return c.time_known ? `Your rising sign (Lagna) is ${c.ascendant_sign_name}, at ${c.ascendant_degree_str}. It is traditionally used as the starting point for the twelve houses and for exploring how you meet the world. Your ascendant nakshatra is ${c.ascendant_nakshatra}.` : 'Your birth time is unknown, so a rising sign cannot be calculated. Add a known birth time and reveal the chart again to see your Lagna and houses.'
  if (/sun|identity/.test(q)) return `Your sidereal Sun is in ${sun.sign_name} at ${sun.degree_str}, in ${sun.nakshatra_name}. The Sun is traditionally linked with identity, vitality, and purpose. A reflection prompt: which activities make you feel most like yourself?`
  if (/overview|chart|summary/.test(q)) return `Here is ${bundle.name || 'this chart'} at a glance: Sun in ${sun.sign_name}, Moon in ${moon.sign_name}, and ${c.ascendant_sign_name ? `${c.ascendant_sign_name} rising` : 'an unknown rising sign because the birth time is missing'}. The Moon’s nakshatra is ${moon.nakshatra_name}. These are the actual placements from the open chart. Try asking about the Moon, Sun, rising sign, or nakshatra.`
  return 'This offline demo uses a small set of prepared replies, so I cannot answer that question yet. Try asking about the Sun, Moon, rising sign, or nakshatra. For the app’s existing interpretations, open the Reading tab.'
}

export function AstroChat({ bundle, chartKey, open, onClose }: { bundle: Bundle | null; chartKey: string; open: boolean; onClose: () => void }) {
  const [conversations, setConversations] = useState<Record<string, Message[]>>({})
  const [draft, setDraft] = useState('')
  const [pending, setPending] = useState(false)
  const timer = useRef<ReturnType<typeof setTimeout>>()
  const log = useRef<HTMLDivElement>(null)
  const close = useRef<HTMLButtonElement>(null)
  const messages = conversations[chartKey] ?? []
  useEffect(() => { setDraft(''); setPending(false); return () => clearTimeout(timer.current) }, [chartKey])
  useEffect(() => { if (open) close.current?.focus() }, [open])
  useEffect(() => { if (log.current) log.current.scrollTop = log.current.scrollHeight }, [messages.length, pending, open])
  const send = (text: string) => {
    const question = text.trim().slice(0, 1000)
    if (!question || pending) return
    setDraft('')
    setConversations(prev => ({ ...prev, [chartKey]: [...(prev[chartKey] ?? []), { role: 'user', text: question }] }))
    setPending(true)
    timer.current = setTimeout(() => {
      setConversations(prev => ({ ...prev, [chartKey]: [...(prev[chartKey] ?? []), { role: 'assistant', text: demoReply(question, bundle) }] }))
      setPending(false)
    }, 550)
  }
  if (!open) return null
  return <aside className="astro-chat no-print" aria-labelledby="chat-title" onKeyDown={e => { if (e.key === 'Escape') onClose() }}>
    <header className="astro-chat__header"><div className="astro-chat__orb" aria-hidden="true">✦</div><div><h2 id="chat-title">Ask the stars</h2><p>AI chat preview <span>OFFLINE DEMO</span></p></div><button ref={close} className="btn btn--ghost" onClick={onClose} aria-label="Close demo chat">×</button></header>
    <div className="astro-chat__context">◇ {bundle?.name || (bundle ? 'Sample birth chart' : 'No chart selected')}<span>Chart context</span></div>
    <div className="astro-chat__log" ref={log} role="log" aria-live="polite" aria-relevant="additions text" aria-label="Demo conversation">
      <div className="chat-message chat-message--assistant"><span>✦ JYOTISH GUIDE</span><p>Welcome to your little corner of the cosmos. Ask about the chart you have open.</p><p className="chat-disclosure">I’m a scripted demo, not a connected AI. Replies are generated locally; no chat messages are sent to the internet. Conversations last for this page session.</p></div>
      {messages.map((m, i) => <div key={i} className={`chat-message chat-message--${m.role}`}><span>{m.role === 'user' ? 'YOU' : '✦ JYOTISH GUIDE · DEMO'}</span><p>{m.text}</p></div>)}
      {pending && <p className="chat-typing" role="status">✦ Preparing demo reply…</p>}
    </div>
    <div className="chat-prompts">{PROMPTS.map(p => <button key={p} onClick={() => send(p)} disabled={pending}>{p}</button>)}</div>
    <form className="chat-composer" onSubmit={e => { e.preventDefault(); send(draft) }}><label className="sr-only" htmlFor="chat-message">Message the demo guide</label><input id="chat-message" value={draft} onChange={e => setDraft(e.target.value)} maxLength={1000} placeholder="Ask about your chart…" autoComplete="off" /><button className="btn btn--primary" disabled={pending || !draft.trim()} aria-label="Send message">↑</button></form>
    <div className="chat-footer"><span>Prepared replies · no internet connection</span><button disabled={pending || !messages.length} onClick={() => setConversations(prev => ({ ...prev, [chartKey]: [] }))}>Clear chat</button></div>
  </aside>
}
