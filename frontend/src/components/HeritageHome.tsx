import { WeddingPortrait } from './MatchmakingPage'
import type { Account } from './GoogleAccount'

export function HeritageHome({ user, count, onNew, onChat, onReport, onMatch }: { user: Account | null; count: number; onNew: () => void; onChat: () => void; onReport: () => void; onMatch: () => void }) {
  return <>
    <section className="heritage-hero" aria-labelledby="heritage-title">
      <img className="heritage-hero__art" src="/art/temple-sanctuary-v1.webp" alt="An ancient golden temple beside a lotus lake, with a peacock, swans and a turtle" />
      <div className="heritage-hero__copy wrap">
        <p className="eyebrow"><span lang="sa">स्वागतम्</span> · WELCOME TO YOUR SANCTUARY</p>
        <div className="heritage-seal" aria-hidden="true">☼</div>
        <h1 id="heritage-title">{user ? <>Your story,<br /><em>written in the stars.</em></> : <>A little closer<br /><em>to your universe.</em></>}</h1>
        <p className="heritage-hero__description">{user ? `Welcome, ${user.display_name.split(' ')[0] || 'stargazer'}. A quiet space to discover your patterns, your people, and your possibilities.` : 'Discover the timeless art of Vedic astrology. Explore your birth chart, understand your rhythms, and find a little perspective.'}</p>
        <div className="cluster"><button className="btn btn--primary" onClick={onNew}>Create a birth chart <span aria-hidden="true">↗</span></button><a className="heritage-link" href="#chart-library">{count ? `My collection (${count})` : 'Explore your sanctuary'} ↓</a></div>
        <p className="heritage-hero__foot">SIDEREAL CHARTS <span>✧</span> PERSONAL INSIGHT <span>✧</span> TIMELESS TRADITION</p>
      </div>
    </section>
    <div className="heritage-ribbon wrap"><span lang="sa">आ नो भद्राः क्रतवो यन्तु विश्वतः</span><div><p>May noble thoughts come to us from every direction.</p><a href="https://www.wisdomlib.org/hinduism/book/rig-veda-english-translation/d/doc829922.html" target="_blank" rel="noreferrer">Rigveda 1.89.1 · excerpt, meaning rendered freely</a></div></div>
    <section className="sanctuary-paths wrap" aria-label="Your sanctuary">
      <a href="#chart-library"><span className="path-number">01</span><div><h2><span lang="sa">जन्मकुण्डली</span> · Your chart collection</h2><p>{count ? `${count} saved ${count === 1 ? 'story' : 'stories'}, ready to explore.` : 'Keep the stories of your people together.'}</p></div><span aria-hidden="true">↗</span></a>
      <button onClick={onChat}><span className="path-number">02</span><div><h2>Your Chart Guide</h2><p><strong>Select a saved chart.</strong> Find a fresh perspective.</p></div><span aria-hidden="true">↗</span></button>
      <button className="path-report" onClick={onReport}><span className="path-number">03</span><div><h2>Detailed Reports</h2><p><strong>All nine grahas.</strong> Your chart, explained in depth.</p></div><span aria-hidden="true">↗</span></button>
      <button className="path-match" onClick={onMatch}><span className="path-number">04</span><div><h2>Matchmaking</h2><p><strong>Two charts, thoughtfully compared.</strong> Explore your connection.</p></div><span aria-hidden="true">↗</span></button>
    </section>
  </>
}

export function HeritageGarden({ onChat }: { onChat: () => void }) {
  return <>
    <section className="graha-folio wrap" aria-labelledby="graha-title"><p className="eyebrow">THE LANGUAGE OF THE SKY</p><h2 id="graha-title">Many influences. One unique you.</h2><p className="muted">The grahas offer different lenses for reflection.</p><img loading="lazy" src="/art/graha-folio-v1.webp" alt="Antique astronomical illustrations of the Sun, Moon, Venus, Mars, Jupiter and Saturn" /><div className="graha-labels">{[['Sun', 'Vitality'], ['Moon', 'Emotions'], ['Venus', 'Connection'], ['Mars', 'Courage'], ['Jupiter', 'Wisdom'], ['Saturn', 'Patience']].map(([name, meaning]) => <div key={name}><strong>{name}</strong><span>{meaning}</span></div>)}</div></section>
    <section className="wisdom-garden wrap"><img loading="lazy" src="/art/rishi-garden-v1.webp" alt="A rishi beside a sacred yajna fire, with white and pink lotuses, swans and a turtle in a temple garden" /><div><p className="eyebrow"><span lang="sa">मननम्</span> · A MOMENT FOR REFLECTION</p><h2>Ancient insight.<br /><em>Room to grow.</em></h2><p>Your chart is an invitation to understand yourself with curiosity and kindness.</p><button className="btn" onClick={onChat}>Open Chart Guide ↗</button></div></section>
  </>
}

export function HeritageFeatures({ onChat, onReport, onMatch }: { onChat: () => void; onReport: () => void; onMatch: () => void }) {
  return <section className="home-discover wrap" aria-labelledby="discover-title">
    <header><p className="eyebrow">EXPLORE YOUR SANCTUARY</p><h2 id="discover-title">A clearer way to understand<br /><em>your own story.</em></h2><p>Start with a chart. Explore its details. Make space for your questions.</p></header>
    <article className="home-feature home-feature--report">
      <div className="home-feature__copy"><p className="eyebrow"><span lang="sa">ग्रहदर्शनम्</span> · YOUR PERSONAL ATLAS</p><h3>Detailed Reports</h3><p className="home-feature__lead">The whole chart.<br /><strong>The reasons behind it.</strong></p><p>Explore every graha through five explained checks, life themes and a timeline that shows where you are today.</p><ul><li>All nine grahas, in one place</li><li>Major periods & Shani’s Sade Sati</li><li>Clear explanations & gentle practices</li></ul><button className="btn" onClick={onReport}>Explore my report <span aria-hidden="true">↗</span></button><small>Choose a saved chart to begin. No per-planet unlocks.</small></div>
      <div className="home-report-art" aria-label="Illustration of the report’s five checks and planetary timeline"><div className="home-art-caption">NAVAGRAHA · NINE PERSPECTIVES</div><div className="home-art-orbit" aria-hidden="true"><span>☉</span><i>☾</i><b>♄</b></div><div className="home-art-sheet"><span>YOUR PLANETARY PORTRAIT</span><h4>Insight, with context.</h4><div><i/>Sign setting <b>01</b></div><div><i/>House setting <b>02</b></div><div><i/>Sign-lord support <b>03</b></div><div><i/>Navamsha setting <b>04</b></div><div><i/>Ashtakavarga points <b>05</b></div><p>◷ Your major-period timeline</p></div><span className="home-art-note">Illustration · your results depend on your chart</span></div>
    </article>
    <article className="home-feature home-feature--guide">
      <div className="home-guide-art"><img loading="lazy" src="/art/rishi-garden-v1.webp" alt="A peaceful temple garden with a rishi, lotus flowers and swans"/><blockquote><p lang="sa">सं गच्छध्वं सं वदध्वं</p><p>Walk together. Speak together.</p><cite><a href="https://vedapath.app/en/rig-veda/mandala-10/191/2" target="_blank" rel="noreferrer">Rigveda 10.191.2 · excerpt</a></cite></blockquote></div>
      <div className="home-feature__copy"><p className="eyebrow"><span lang="sa">संवादः</span> · A CONVERSATION WITH CONTEXT</p><h3>Chart Guide</h3><p className="home-feature__lead">Your questions.<br /><strong>Room to reflect.</strong></p><p>Choose a saved chart and have a thoughtful conversation about its placements, patterns and possibilities.</p><ul><li>Grounded in the chart you select</li><li>A spacious, focused conversation</li><li>Supportive suggestions for everyday life</li></ul><button className="btn" onClick={onChat}>Open Chart Guide <span aria-hidden="true">↗</span></button><small>AI-assisted reflection. Your choices always remain yours.</small></div>
    </article>
    <article className="home-match-feature"><div><p className="eyebrow">कुण्डली मिलान · CONNECTION & COMPATIBILITY</p><h3>Two stories.<br/>A shared perspective.</h3><p>Choose the groom’s and bride’s charts. Explore all eight compatibility checks, with clear scores and thoughtful explanations.</p><button className="btn" onClick={onMatch}>Explore Matchmaking ↗</button></div><div className="home-match-portraits"><WeddingPortrait/><span aria-hidden="true">&</span><WeddingPortrait bride/></div></article>
  </section>
}
