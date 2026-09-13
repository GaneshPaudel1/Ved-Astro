import type { Account } from './GoogleAccount'

export function HeritageHome({ user, count, onNew, onChat }: { user: Account | null; count: number; onNew: () => void; onChat: () => void }) {
  return <>
    <section className="heritage-hero" aria-labelledby="heritage-title">
      <img className="heritage-hero__art" src="/art/temple-sanctuary-v1.webp" alt="An ancient golden temple beside a lotus lake, with a peacock, swans and a turtle" />
      <div className="heritage-hero__copy wrap">
        <p className="eyebrow">ANCIENT WISDOM · A PERSONAL JOURNEY</p>
        <div className="heritage-seal" aria-hidden="true">☼</div>
        <h1 id="heritage-title">{user ? <>Your story,<br /><em>written in the stars.</em></> : <>A little closer<br /><em>to your universe.</em></>}</h1>
        <p className="heritage-hero__description">{user ? `Welcome, ${user.display_name.split(' ')[0] || 'stargazer'}. A quiet space to discover your patterns, your people, and your possibilities.` : 'Discover the timeless art of Vedic astrology. Explore your birth chart, understand your rhythms, and find a little perspective.'}</p>
        <div className="cluster"><button className="btn btn--primary" onClick={onNew}>Create a birth chart <span aria-hidden="true">↗</span></button><a className="heritage-link" href="#chart-library">{count ? `My collection (${count})` : 'Explore your sanctuary'} ↓</a></div>
        <p className="heritage-hero__foot">SIDEREAL CHARTS <span>✧</span> PERSONAL INSIGHT <span>✧</span> TIMELESS TRADITION</p>
      </div>
    </section>
    <div className="heritage-ribbon wrap"><span>॥ ज्योतिष ॥</span><p>As above, so within.</p><span>THE ART OF SEEING LIGHT</span></div>
    <section className="sanctuary-paths wrap" aria-label="Your sanctuary">
      <a href="#chart-library"><span className="path-number">01</span><div><h2>Your chart collection</h2><p>{count ? `${count} saved ${count === 1 ? 'story' : 'stories'}, ready to explore.` : 'Keep the stories of your people together.'}</p></div><span aria-hidden="true">↗</span></a>
      <button onClick={onChat}><span className="path-number">02</span><div><h2>A conversation with the stars</h2><p>Select a saved chart. Find a fresh perspective.</p></div><span aria-hidden="true">↗</span></button>
    </section>
  </>
}

export function HeritageGarden({ onChat }: { onChat: () => void }) {
  return <>
    <section className="graha-folio wrap" aria-labelledby="graha-title"><p className="eyebrow">THE LANGUAGE OF THE SKY</p><h2 id="graha-title">Many influences. One unique you.</h2><p className="muted">The grahas offer different lenses for reflection.</p><img loading="lazy" src="/art/graha-folio-v1.webp" alt="Antique astronomical illustrations of the Sun, Moon, Venus, Mars, Jupiter and Saturn" /><div className="graha-labels">{[['Sun', 'Vitality'], ['Moon', 'Emotions'], ['Venus', 'Connection'], ['Mars', 'Courage'], ['Jupiter', 'Wisdom'], ['Saturn', 'Patience']].map(([name, meaning]) => <div key={name}><strong>{name}</strong><span>{meaning}</span></div>)}</div></section>
    <section className="wisdom-garden wrap"><img loading="lazy" src="/art/rishi-garden-v1.webp" alt="A rishi beside a sacred yajna fire, with white and pink lotuses, swans and a turtle in a temple garden" /><div><p className="eyebrow">A MOMENT FOR REFLECTION</p><h2>Ancient insight.<br /><em>Room to grow.</em></h2><p>Your chart is an invitation to understand yourself with curiosity and kindness.</p><button className="btn" onClick={onChat}>Begin a conversation ↗</button></div></section>
  </>
}
