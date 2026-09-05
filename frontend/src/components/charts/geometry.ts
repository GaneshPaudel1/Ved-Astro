/*
  Chart geometry.

  Both layouts are drawn from first principles rather than from a background
  image, so they stay crisp at any size and every region is a real hit target.

  ── North Indian (diamond) ────────────────────────────────────────────────
  Houses are FIXED in position and the signs rotate through them. House 1 is
  always the diamond at top centre, and the houses run anticlockwise.

  The figure is a square crossed by both diagonals and by the rhombus joining
  the four edge midpoints. Each rhombus edge meets one diagonal at a quarter
  point of the square, and those twelve regions are the houses.

  ── South Indian (grid) ───────────────────────────────────────────────────
  The mirror image: SIGNS are fixed in a 4×4 ring and the houses rotate. Aries
  sits second along the top row and the signs run clockwise from there. The
  ascendant is marked with a diagonal stroke in its cell.
*/

export interface Poly {
  house: number
  points: [number, number][]
  /** where to stack planet labels, in unit coordinates */
  anchor: [number, number]
  /** where the sign number sits, in unit coordinates */
  signAnchor: [number, number]
}

/** Unit square corners, edge midpoints, quarter points and centre. */
const NW: [number, number] = [0, 0]
const NE: [number, number] = [1, 0]
const SE: [number, number] = [1, 1]
const SW: [number, number] = [0, 1]
const N: [number, number] = [0.5, 0]
const E: [number, number] = [1, 0.5]
const S: [number, number] = [0.5, 1]
const W: [number, number] = [0, 0.5]
const NWq: [number, number] = [0.25, 0.25]
const NEq: [number, number] = [0.75, 0.25]
const SEq: [number, number] = [0.75, 0.75]
const SWq: [number, number] = [0.25, 0.75]
const C: [number, number] = [0.5, 0.5]

export const NORTH_HOUSES: Poly[] = [
  { house: 1, points: [N, NEq, C, NWq], anchor: [0.5, 0.3], signAnchor: [0.5, 0.11] },
  { house: 2, points: [NW, N, NWq], anchor: [0.27, 0.115], signAnchor: [0.12, 0.05] },
  { house: 3, points: [NW, NWq, W], anchor: [0.115, 0.27], signAnchor: [0.05, 0.12] },
  { house: 4, points: [W, NWq, C, SWq], anchor: [0.3, 0.5], signAnchor: [0.11, 0.5] },
  { house: 5, points: [W, SWq, SW], anchor: [0.115, 0.73], signAnchor: [0.05, 0.88] },
  { house: 6, points: [SW, SWq, S], anchor: [0.27, 0.885], signAnchor: [0.12, 0.95] },
  { house: 7, points: [S, SWq, C, SEq], anchor: [0.5, 0.7], signAnchor: [0.5, 0.89] },
  { house: 8, points: [S, SEq, SE], anchor: [0.73, 0.885], signAnchor: [0.88, 0.95] },
  { house: 9, points: [SE, SEq, E], anchor: [0.885, 0.73], signAnchor: [0.95, 0.88] },
  { house: 10, points: [E, SEq, C, NEq], anchor: [0.7, 0.5], signAnchor: [0.89, 0.5] },
  { house: 11, points: [E, NEq, NE], anchor: [0.885, 0.27], signAnchor: [0.95, 0.12] },
  { house: 12, points: [NE, NEq, N], anchor: [0.73, 0.115], signAnchor: [0.88, 0.05] },
]

/** The lines that make up the North Indian figure. */
export const NORTH_LINES: [[number, number], [number, number]][] = [
  [NW, SE],
  [NE, SW],
  [N, E],
  [E, S],
  [S, W],
  [W, N],
]

/**
 * South Indian cell for each sign, as [row, col] in a 4×4 grid.
 * Pisces occupies the top-left and the signs run clockwise.
 */
export const SOUTH_CELLS: Record<number, [number, number]> = {
  11: [0, 0], // Pisces
  0: [0, 1], // Aries
  1: [0, 2], // Taurus
  2: [0, 3], // Gemini
  3: [1, 3], // Cancer
  4: [2, 3], // Leo
  5: [3, 3], // Virgo
  6: [3, 2], // Libra
  7: [3, 1], // Scorpio
  8: [3, 0], // Sagittarius
  9: [2, 0], // Capricorn
  10: [1, 0], // Aquarius
}

export const SOUTH_ORDER: number[] = [11, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

export function polygonPoints(poly: Poly, size: number): string {
  return poly.points.map(([x, y]) => `${x * size},${y * size}`).join(' ')
}

/** Dignity → CSS custom property, so both themes stay in sync. */
export function dignityColor(dignity: string): string {
  switch (dignity) {
    case 'exalted':
      return 'var(--exalted)'
    case 'debilitated':
      return 'var(--debilitated)'
    case 'own sign':
    case 'moolatrikona':
      return 'var(--accent-bright)'
    default:
      return 'var(--text)'
  }
}

export function dignityShort(dignity: string): string {
  switch (dignity) {
    case 'exalted':
      return '↑'
    case 'debilitated':
      return '↓'
    case 'own sign':
      return '•'
    case 'moolatrikona':
      return '◆'
    default:
      return ''
  }
}
