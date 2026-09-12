import type { Account } from './GoogleAccount'
import type { SavedChart } from './ChartLibrary'

export function DashboardWelcome({ user, charts, busy, onNew, onLoad, onChat }: {
  user: Account; charts: SavedChart[]; busy: boolean; onNew: () => void
  onLoad: (chart: SavedChart) => void; onChat: (chart: SavedChart) => void
}) {
  const latest = [...charts].sort((a, b) => b.savedAt.localeCompare(a.savedAt))[0]
  return <section className="dashboard-welcome wrap no-print" aria-labelledby="dashboard-title">
    <div className="dashboard-intro">
      <p className="eyebrow">YOUR PERSONAL OBSERVATORY</p>
      <h1 id="dashboard-title">Welcome back,<br /><em>{user.display_name.split(' ')[0] || 'stargazer'}.</em></h1>
      <p>A little perspective. A deeper connection.<br />Your people and their stories, all in one place.</p>
      <div className="cluster"><button className="btn btn--primary" disabled={busy} onClick={onNew}>＋ Create a chart</button><a className="btn btn--ghost" href="#chart-library">Explore my charts ↓</a></div>
      <div className="dashboard-count"><strong>{charts.length.toString().padStart(2, '0')}</strong><span>personal {charts.length === 1 ? 'chart' : 'charts'}<br />in your collection</span></div>
    </div>
    <div className="dashboard-orbit" aria-hidden="true"><span>AS ABOVE, SO WITHIN</span></div>
    <div className="dashboard-paths">
      <button disabled={!latest || busy} onClick={() => latest && onLoad(latest)}><span>01 / CONTINUE EXPLORING</span><strong>{latest ? latest.birth.name : 'Your story starts here'} ↗</strong><small>{latest ? 'Open your most recently saved chart' : 'Create your first chart to begin'}</small></button>
      <button disabled={!latest || busy} onClick={() => latest && onChat(latest)}><span>02 / A LITTLE GUIDANCE</span><strong>A conversation with your stars ✦</strong><small>Explore your chart with Gemini</small></button>
    </div>
  </section>
}
