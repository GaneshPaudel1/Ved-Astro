import type {
  Bundle, DashaTree, GeoResult, MatchResult, Panchang, Reference, BirthInput,
} from './types'

/*
  Local Vite development proxies `/api` to FastAPI. In production the frontend
  is a separate static site, so Render supplies the API host at build time.
  Keep the fallback for local development and previews.
*/
const configuredApiBase = import.meta.env.VITE_API_BASE?.trim().replace(/\/+$/, '')
const BASE = configuredApiBase ? `${configuredApiBase}/api` : '/api'

export class ApiError extends Error {
  status: number
  detail: unknown
  constructor(status: number, message: string, detail?: unknown) {
    super(message)
    this.status = status
    this.detail = detail
  }
}

function token(): string | null {
  return localStorage.getItem('jyotish_token')
}

export function setToken(value: string | null) {
  if (value) localStorage.setItem('jyotish_token', value)
  else localStorage.removeItem('jyotish_token')
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((init.headers as Record<string, string>) || {}),
  }
  const t = token()
  if (t) headers.Authorization = `Bearer ${t}`

  const res = await fetch(`${BASE}${path}`, { ...init, headers })

  if (res.status === 204) return undefined as T
  const text = await res.text()
  const body = text ? JSON.parse(text) : null

  if (!res.ok) {
    // FastAPI validation errors arrive as a list under `detail`.
    let message = `Request failed (${res.status})`
    const d = body?.detail
    if (typeof d === 'string') message = d
    else if (Array.isArray(d) && d.length) {
      message = d
        .map((e: any) => {
          const field = Array.isArray(e.loc) ? e.loc[e.loc.length - 1] : ''
          return field ? `${field}: ${e.msg}` : e.msg
        })
        .join('; ')
    }
    throw new ApiError(res.status, message, d)
  }
  return body as T
}

const post = <T,>(path: string, body: unknown) =>
  request<T>(path, { method: 'POST', body: JSON.stringify(body) })

export const api = {
  health: () => request<any>('/health'),
  reference: () => request<Reference>('/reference'),

  chart: (input: BirthInput & { include?: string[] }) => post<Bundle>('/chart', input),

  dasha: (input: BirthInput & { system?: string; levels?: number }) =>
    post<DashaTree>('/dasha', input),

  transits: (input: BirthInput & { at?: string }) => post<any>('/transits', input),

  panchang: (input: {
    date: string; latitude: number; longitude: number; ayanamsa?: string
  }) => post<Panchang>('/panchang', input),

  match: (first: BirthInput, second: BirthInput, ayanamsa = 'lahiri') =>
    post<MatchResult>('/match', { first, second, ayanamsa }),

  geocode: (q: string) =>
    request<{ query: string; results: GeoResult[]; offline: boolean; note: string | null }>(
      `/geocode?q=${encodeURIComponent(q)}`),

  timezoneAt: (latitude: number, longitude: number, date: string) =>
    request<{
      tz_name: string; utc_offset_hours: number; abbreviation: string
      pre_standard_time: boolean; lmt_offset_hours: number; note: string | null
    }>(`/timezone?latitude=${latitude}&longitude=${longitude}&date=${date}`),

  // ---- accounts ----
  register: (email: string, password: string, display_name = '') =>
    post<any>('/auth/register', { email, password, display_name }),
  login: (email: string, password: string) => post<any>('/auth/login', { email, password }),
  logout: () => post<any>('/auth/logout', {}),
  me: () => request<any>('/auth/me'),

  // ---- profiles ----
  profiles: () => request<{ profiles: any[] }>('/profiles'),
  createProfile: (body: any) => post<any>('/profiles', body),
  deleteProfile: (id: number) => request<void>(`/profiles/${id}`, { method: 'DELETE' }),
  profileChart: (id: number) => request<Bundle>(`/profiles/${id}/chart`),
}
