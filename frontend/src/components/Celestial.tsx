import type { Bundle } from '../api/types'
import { CosmicScene } from './CosmicScene'

export function CelestialHero({ onBegin, paused, onToggleMotion }: { onBegin: () => void; paused: boolean; onToggleMotion: () => void }) {
  return <section className="cosmic-hero wrap no-print" aria-labelledby="cosmic-title">
    <CosmicScene paused={paused} />
    <div className="cosmic-hero__copy">
      <p className="eyebrow"><span className="live-star">✦</span> Ancient wisdom. A new dimension.</p>
      <h1 id="cosmic-title">A universe within.<br /><em>Step into yours.</em></h1>
      <p className="cosmic-hero__intro">You are more than a moment in time. Explore the planets, patterns, and possibilities that make your sky uniquely yours.</p>
      <div className="cluster"><button className="btn btn--primary cosmic-cta" onClick={onBegin}>Enter my universe <span aria-hidden="true">↗</span></button><span className="cosmic-hero__note">Your sky. Your story.</span></div>
      <div className="cosmic-hero__tags"><span>✧ 9 Grahas</span><span>☾ 27 Nakshatras</span><span>☉ 12 Rashis</span></div>
    </div>
    <div className="scene-controls"><span>A MOMENT BEYOND THE ORDINARY</span><button className="motion-toggle" onClick={onToggleMotion} aria-pressed={paused}>{paused ? '▷ Resume motion' : 'Ⅱ Pause motion'}</button></div>
    <div className="hero-bottom"><span>SCROLL TO DISCOVER ↓</span><span>YOUR PERSONAL COSMIC OBSERVATORY</span></div>
  </section>
}

export function CosmicSnapshot({ bundle }: { bundle: Bundle }) {
  const c = bundle.chart
  const cards = [
    { title: 'Sun sign', subtitle: 'Your core expression', value: c.planets.Sun.sign_name, detail: c.planets.Sun.nakshatra_name, glyph: '☉', tone: 'sun' },
    { title: 'Moon sign', subtitle: 'Your inner world', value: c.planets.Moon.sign_name, detail: c.planets.Moon.nakshatra_name, glyph: '☾', tone: 'moon' },
    { title: 'Rising sign', subtitle: 'How you meet the world', value: c.ascendant_sign_name ?? 'Time unknown', detail: c.ascendant_nakshatra ?? 'Add your birth time to discover', glyph: '✧', tone: 'rising' },
  ]
  return <div className="cosmic-snapshot" aria-label="Your chart at a glance">{cards.map(card => <article key={card.tone} className={`cosmic-card cosmic-card--${card.tone}`}>
    <img className="cosmic-card__art" src={`/art/${card.tone}-realm-v1.png`} alt="" loading="lazy" width="1536" height="1024" />
    <span className="cosmic-card__glyph" aria-hidden="true">{card.glyph}</span>
    <p className="eyebrow">{card.title}</p><h3>{card.value}</h3><p className="cosmic-card__subtitle">{card.subtitle}</p><p className="cosmic-card__detail">{card.detail}</p>
  </article>)}</div>
}
