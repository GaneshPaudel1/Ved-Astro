import { useCallback, useEffect, useRef, useState } from 'react'
import { api, ApiError } from '../api/client'
import { readLibrary, writeLibrary, type SavedChart } from './ChartLibrary'

// Account collections stay in memory. Guest charts never leak into another account.
export function useChartLibrary(userId: number | null) {
  const [initial] = useState(() => userId ? { charts: [], error: null } : readLibrary())
  const [charts, setCharts] = useState<SavedChart[]>(initial.charts)
  const [error, setError] = useState<string | null>(initial.error)
  const [loading, setLoading] = useState(Boolean(userId))
  const [ready, setReady] = useState(!userId)
  const state = useRef({ charts: initial.charts as SavedChart[], revision: -1 })
  const locked = useRef(false)
  const alive = useRef(true)
  const refresh = useCallback(async () => {
    if (!userId || locked.current) return
    locked.current = true; setLoading(true)
    try {
      const snapshot = await api.library()
      if (snapshot.revision !== state.current.revision) {
        const rebuilt: SavedChart[] = []
        // Bound calculation concurrency when a collection is large.
        for (let i = 0; i < snapshot.charts.length; i += 4) {
          const batch = await Promise.all(snapshot.charts.slice(i, i + 4).map(async c => ({ ...c, bundle: await api.chart(c.birth) })))
          if (!alive.current) return
          rebuilt.push(...batch)
        }
        if (!alive.current) return
        state.current = { charts: rebuilt, revision: snapshot.revision }
        setCharts(rebuilt)
      }
      if (alive.current) { setReady(true); setError(null) }
    } catch (e) {
      if (alive.current) { setReady(false); setError(e instanceof ApiError ? e.message : 'Could not load account charts. Your saved collection has not been changed.') }
    } finally { locked.current = false; if (alive.current) setLoading(false) }
  }, [userId])
  useEffect(() => {
    alive.current = true
    if (userId) void refresh()
    const localChange = (e: StorageEvent) => {
      if (userId || (e.key !== 'jyotish_chart_library_v1' && e.key !== null)) return
      const next = readLibrary()
      setError(next.error)
      if (!next.error) { state.current.charts = next.charts; setCharts(next.charts) }
    }
    const onFocus = () => { if (document.visibilityState === 'visible') void refresh() }
    window.addEventListener('storage', localChange)
    window.addEventListener('focus', onFocus)
    const timer = userId ? window.setInterval(onFocus, 30000) : undefined
    return () => { alive.current = false; window.removeEventListener('storage', localChange); window.removeEventListener('focus', onFocus); clearInterval(timer) }
  }, [userId, refresh])

  const persist = async (next: SavedChart[]) => {
    if (locked.current || !ready) return false
    locked.current = true; setLoading(true)
    let conflict = false
    try {
      if (userId) {
        const result = await api.saveLibrary(state.current.revision, next.map(({ id, birth, savedAt }) => ({ id, birth, savedAt })))
        if (!alive.current) return false
        state.current.revision = result.revision
      } else {
        const latest = readLibrary()
        if (latest.error) throw new Error(latest.error)
        if (JSON.stringify(latest.charts) !== JSON.stringify(state.current.charts)) throw new Error('The browser collection changed in another tab. Reload before retrying.')
        writeLibrary(next)
      }
      if (!alive.current) return false
      state.current.charts = next; setCharts(next); setError(null)
      return true
    } catch (e) {
      conflict = e instanceof ApiError && e.status === 409
      if (alive.current) setError(e instanceof Error ? e.message : 'Saving failed. Please retry.')
      return false
    } finally {
      locked.current = false
      if (alive.current) {
        setLoading(false)
        if (conflict) {
          await refresh()
          if (alive.current) setError('Your collection changed on another device and has been refreshed. Your last edit was not saved; please retry it.')
        }
      }
    }
  }
  const importLocal = async () => {
    const local = readLibrary()
    if (local.error) { setError(local.error); return false }
    const ids = new Set(charts.map(c => c.id))
    return persist([...local.charts.filter(c => !ids.has(c.id)), ...charts])
  }
  return { charts, error, loading, ready, persist, refresh, importLocal }
}
