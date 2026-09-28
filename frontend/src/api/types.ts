export interface Planet {
  name: string
  sanskrit: string
  longitude: number
  latitude: number
  speed: number
  sign: number
  sign_name: string
  degree_in_sign: number
  degree_str: string
  nakshatra: number
  nakshatra_name: string
  nakshatra_lord: string
  pada: number
  house: number
  retrograde: boolean
  combust: boolean
  dignity: string
  is_benefic: boolean
  abbr: string
  glyph: string
}

export interface House {
  number: number
  cusp: number
  sign: number
  sign_name: string
  sign_sanskrit: string
  lord: string
  degree_str: string
  meaning: string
  planets: string[]
}

export interface Moment {
  jd_ut: number
  utc: string
  local: string
  latitude: number
  longitude: number
  tz_name: string
  utc_offset_hours: number
  utc_offset_label: string
  tz_abbrev: string
  time_standard: string
}

export interface Chart {
  moment: Moment
  ayanamsa: string
  ayanamsa_label: string
  ayanamsa_value: number
  ayanamsa_str: string
  house_system: string
  ascendant: number | null
  ascendant_sign: number | null
  ascendant_sign_name: string | null
  ascendant_degree_str: string | null
  ascendant_nakshatra: string | null
  ascendant_pada: number | null
  ascendant_lord: string | null
  houses: House[]
  planets: Record<string, Planet>
  time_known: boolean
  warnings: string[]
  engine: { backend: string; detail: string; swe_version: string; ephe_path: string | null }
}

export interface VargaPlanet {
  name: string
  sign: number
  sign_name: string
  house: number
  abbr: string
  retrograde: boolean
  dignity: string
  vargottama: boolean
}

export interface Varga {
  varga: string
  name: string
  divisions: number
  signifies: string
  ascendant_sign: number | null
  ascendant_sign_name: string | null
  planets: Record<string, VargaPlanet>
  houses: { number: number; sign: number; sign_name: string; lord: string; planets: string[] }[]
}

export interface DashaPeriod {
  lord: string
  level: number
  level_name: string
  start: string
  end: string
  start_jd: number
  end_jd: number
  duration_years: number
  duration_days?: number
  current?: boolean
  partial_at_birth?: boolean
  children?: DashaPeriod[]
  graha?: string
}

export interface DashaTree {
  system: string
  total_years: number
  birth_nakshatra: string
  starting_lord: string
  balance_at_birth: { lord: string; years: number; readable: string }
  cycle_start?: string
  cycle_end?: string
  periods: DashaPeriod[]
  current_path?: DashaPathNode[]
}

export interface DashaPathNode {
  lord: string
  level: number
  level_name: string
  start: string
  end: string
  start_jd: number
  end_jd: number
  duration_years: number
  elapsed_percent: number
  remaining: string
}

export interface Yoga {
  key: string
  name: string
  sanskrit: string
  planets: string[]
  houses: number[]
  strength: string
  summary: string
  detail: string
}

export interface Ashtakavarga {
  bav: Record<string, number[]>
  sav: number[]
  sav_total: number
  bav_totals: Record<string, number>
  signs: {
    sign: number
    sign_name: string
    sign_sanskrit: string
    house: number
    sav: number
    bav: Record<string, number>
    strength: string
  }[]
  ascendant_sign: number | null
  strongest_sign: number
  weakest_sign: number
  note: string
}

export interface Doshas {
  manglik: {
    present: boolean
    severity?: string
    mars_sign?: string
    mars_house?: number | null
    hits?: { reference: string; house: number; counted_in_south_india: boolean }[]
    cancellations?: string[]
    rule?: string
    note?: string
    reason?: string
  }
  kaal_sarp: {
    present: boolean
    partial?: boolean
    breaking_planet?: string[]
    type?: string | null
    rahu_house?: number | null
    rahu_sign?: string
    ketu_sign?: string
    rule?: string
    note?: string
  }
  pitra: {
    present: boolean
    weak_indication?: boolean
    indicators?: string[]
    ninth_lord?: string
    rule?: string
    note?: string
    reason?: string
  }
  sade_sati?: {
    moon_sign: string
    currently_active: boolean
    current_phase: SadeSatiPhase | null
    phases: SadeSatiPhase[]
    rule: string
    note: string
  }
}

export interface SadeSatiPhase {
  open_start?: boolean
  open_end?: boolean
  phase: string
  house_from_moon: number
  sign: number
  sign_name: string
  start: string
  end: string
  start_jd: number
  end_jd: number
  description: string
  current: boolean
}

export interface TransitPlanet extends Planet {
  house_from_moon: number | null
  house_from_lagna: number | null
  note: string | null
  favourable: boolean | null
  natal_sign_name: string | null
  returned_to_natal_sign: boolean
  bindus_in_sign?: number
  bindu_note?: string
  conjunct_natal: { natal_planet: string; orb: number }[]
}

export interface Section {
  key: string
  title: string
  body: string
  tags: string[]
  evidence: string[]
}

export interface Reading {
  engine: string
  sections: Section[]
  disclaimer: string
}

export interface Bundle {
  name: string
  place: string
  chart: Chart
  cache_key?: string
  cached?: boolean
  aspects?: { planet: string; aspect_number: number; from_sign: number; target_sign: number; target_sign_name: string; special: boolean }[]
  vargas?: Record<string, Varga>
  varga_strength?: Record<string, { counts: Record<string, number>; favourable_vargas: number; total_vargas: number; vargottama: boolean }>
  vargottama?: string[]
  nakshatra_detail?: Record<string, NakshatraDetail>
  dasha?: DashaTree
  dasha_path?: DashaPathNode[]
  dasha_alternates?: { yogini: DashaTree; ashtottari: DashaTree }
  yogas?: Yoga[]
  ashtakavarga?: Ashtakavarga
  doshas?: Doshas
  transits?: { moment: string; natal_moon_sign: string | null; read_from: string; planets: Record<string, TransitPlanet> }
  transit_alerts?: TransitAlert[]
  interpretation?: Reading
}

export interface TransitAlert {
  planet: string
  from_sign: string
  to_sign: string
  date: string
  days_away: number
  house_from_moon: number
  severity: string
  message: string
}

export interface NakshatraDetail {
  index: number
  number: number
  name: string
  lord: string
  deity: string
  symbol: string
  gana: string
  nadi: string
  yoni: string
  yoni_sex: string
  pada: number
  span_start: number
  span_end: number
  degrees_traversed: number
  percent_through: number
}

export interface Panchang {
  date: string
  location: { latitude: number; longitude: number; tz_name: string; tz_abbrev: string; utc_offset_hours: number }
  vara: { index: number; name: string; sanskrit: string; lord: string }
  tithi: Limb & { paksha: string; paksha_meaning: string; deity_note: string | null }
  nakshatra: Limb & { lord: string; deity: string; symbol: string; gana: string; nadi: string; yoni: string; pada: number }
  yoga: Limb & { inauspicious: boolean }
  karana: Limb & { type: string; inauspicious: boolean; note: string | null }
  sun: { sunrise: string | null; sunset: string | null; longitude: number; sign: string }
  moon: { moonrise: string | null; moonset: string | null; longitude: number; sign: string; phase_angle: number; illumination_percent: number }
  periods: Record<string, any>
  note: string
}

export interface Limb {
  index: number
  name: string
  percent_complete: number
  ends: string | null
  ends_jd: number | null
}

export interface Koota {
  koota: string
  sanskrit: string
  score: number
  max: number
  verdict: string
  explanation: string
  detail: string | null
  cancellations?: string[]
}

export interface MatchResult {
  total: number
  maximum: number
  percent: number
  band: string
  summary: string
  kootas: Koota[]
  people: Record<string, any>
  caveat: string
  time_note?: string
  manglik: {
    verdict: string
    note: string
    first: { present: boolean; severity: string; cancellations: string[] }
    second: { present: boolean; severity: string; cancellations: string[] }
  }
  charts: Record<string, any>
}

export interface GeoResult {
  name: string
  country: string
  admin: string
  latitude: number
  longitude: number
  label: string
  timezone?: string
  population?: number
  source: string
}

export interface Reference {
  signs: { index: number; name: string; sanskrit: string; lord: string; element: string; quality: string; symbol: string }[]
  nakshatras: { index: number; number: number; name: string; lord: string; deity: string; symbol: string; gana: string; nadi: string; yoni: string; yoni_sex: string; start: number; end: number }[]
  planets: { name: string; sanskrit: string; glyph: string; abbr: string; benefic: boolean }[]
  houses: { number: number; meaning: string }[]
  ayanamsas: { key: string; label: string; note: string }[]
  house_systems: { key: string; label: string; note: string }[]
  vargas: { key: string; name: string; divisions: number; signifies: string }[]
}

export interface BirthInput {
  gender?: 'female' | 'male' | 'other' | 'prefer_not_to_say' | null
  name: string
  date: string
  time: string | null
  latitude: number
  longitude: number
  place: string
  ayanamsa: string
  house_system: string
  node_type: string
  time_standard: string
}
