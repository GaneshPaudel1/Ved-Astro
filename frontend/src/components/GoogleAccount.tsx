import { useEffect, useRef, useState } from 'react'
import { api, ApiError, setToken } from '../api/client'

export interface Account { id: number; email: string; display_name: string }
declare global {
  interface Window {
    google?: { accounts: { id: {
      initialize: (options: { client_id: string; callback: (response: { credential: string }) => void }) => void
      renderButton: (element: HTMLElement, options: { theme: string; size: string }) => void
      disableAutoSelect: () => void
    } } }
  }
}

let googleScript: Promise<void> | undefined
function loadGoogle() {
  if (window.google) return Promise.resolve()
  if (!googleScript) googleScript = new Promise<void>((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => { script.remove(); googleScript = undefined; reject(new Error('Google sign-in could not load. Check your connection and retry.')) }
    document.head.appendChild(script)
  })
  return googleScript
}

export function GoogleAccount({ user, onChange }: { user: Account | null; onChange: (user: Account | null) => void }) {
  const mount = useRef<HTMLDivElement>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    let cancelled = false
    api.me().then(u => { if (!cancelled) onChange(u) }).catch(e => {
      if (!cancelled && e instanceof ApiError && e.status === 401) setToken(null)
    })
    return () => { cancelled = true }
  }, [onChange])
  useEffect(() => {
    if (user) return
    let cancelled = false
    setError('')
    api.authConfig().then(async config => {
      if (!config.google_client_id) throw new Error('Google sign-in is not configured yet.')
      await loadGoogle()
      if (cancelled || !mount.current || !window.google) return
      window.google.accounts.id.initialize({ client_id: config.google_client_id, callback: async ({ credential }) => {
        if (cancelled) return
        setBusy(true); setError('')
        try {
          const result = await api.googleLogin(credential)
          if (!cancelled) { setToken(result.token); onChange(result.user) }
        } catch (e) { if (!cancelled) setError(e instanceof Error ? e.message : 'Sign-in failed.') }
        finally { if (!cancelled) setBusy(false) }
      } })
      mount.current.replaceChildren()
      window.google.accounts.id.renderButton(mount.current, { theme: 'outline', size: 'large' })
    }).catch(e => { if (!cancelled) setError(e instanceof Error ? e.message : 'Sign-in unavailable.') })
    return () => { cancelled = true }
  }, [user, onChange, attempt])
  const logout = async () => {
    setBusy(true); setError('')
    try { await api.logout(); setToken(null); window.google?.accounts.id.disableAutoSelect(); onChange(null) }
    catch { setError('Could not sign out. Please retry.') }
    finally { setBusy(false) }
  }
  return <div className="google-account">
    {user ? <><span className="small">{user.display_name || user.email}</span><button className="btn btn--ghost btn--sm" disabled={busy} onClick={logout}>Sign out</button></> : <div ref={mount} />}
    {busy && <span role="status" className="small">Connecting…</span>}
    {error && <div role="alert" className="small">{error} <button className="btn btn--ghost btn--sm" onClick={() => setAttempt(v => v + 1)}>Retry</button></div>}
  </div>
}
