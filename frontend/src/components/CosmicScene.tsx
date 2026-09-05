import { useEffect, useRef } from 'react'

/** Generated cinematic artwork, layered with independently animated stardust. */
export function CosmicScene({ paused }: { paused: boolean }) {
  const layer = useRef<HTMLDivElement>(null)
  const canvas = useRef<HTMLCanvasElement>(null)
  const clock = useRef(0)
  useEffect(() => {
    const host = layer.current
    const element = canvas.current
    if (!host || !element) return
    const ctx = element.getContext('2d')
    if (!ctx) return
    const reduced = matchMedia('(prefers-reduced-motion: reduce)')
    const fine = matchMedia('(pointer: fine)')
    let frame = 0, previous = 0, width = 1000, height = 700, visible = true
    let x = 0, y = 0, aimX = 0, aimY = 0
    let seed = 173
    const random = () => { seed = seed * 16807 % 2147483647; return (seed - 1) / 2147483646 }
    const particles = Array.from({ length: 120 }, () => ({ a: random() * Math.PI * 2, r: .12 + random() * .42, z: random(), size: .3 + random() * 1.1 }))
    const draw = () => {
      ctx.setTransform(element.width / width, 0, 0, element.height / height, 0, 0)
      ctx.clearRect(0, 0, width, height)
      for (const p of particles) {
        const a = p.a + clock.current * (.008 + p.z * .018)
        const px = width * .72 + Math.cos(a) * width * p.r + x * p.z * 24
        const py = height * .48 + Math.sin(a) * height * p.r * .7 + y * p.z * 18
        const alpha = .15 + (Math.sin(p.a * 8 + clock.current * .45) + 1) * .18
        ctx.fillStyle = `rgba(255,${p.z > .5 ? 211 : 235},${p.z > .5 ? 181 : 255},${alpha})`
        ctx.shadowColor = '#f4c8e2'; ctx.shadowBlur = p.z * 5
        ctx.beginPath(); ctx.arc(px, py, p.size, 0, Math.PI * 2); ctx.fill()
      }
    }
    const tick = (now: number) => {
      clock.current += previous ? Math.min((now - previous) / 1000, .05) : 0
      previous = now
      x += (aimX - x) * .03; y += (aimY - y) * .03
      host.style.setProperty('--dream-x', `${x * 11}px`)
      host.style.setProperty('--dream-y', `${y * 8}px`)
      draw(); frame = requestAnimationFrame(tick)
    }
    const start = () => {
      cancelAnimationFrame(frame); previous = 0
      if (visible && !document.hidden && !paused && !reduced.matches) frame = requestAnimationFrame(tick)
      else draw()
    }
    const resize = new ResizeObserver(() => {
      const r = element.getBoundingClientRect()
      if (!r.width || !r.height) return
      width = r.width; height = r.height
      const dpr = Math.min(devicePixelRatio || 1, 2)
      element.width = Math.round(width * dpr); element.height = Math.round(height * dpr); draw()
    })
    const observer = new IntersectionObserver(entries => { visible = entries[0].isIntersecting; start() })
    resize.observe(element); observer.observe(element)
    const move = (e: PointerEvent) => {
      if (paused || reduced.matches || !fine.matches) return
      const r = host.getBoundingClientRect()
      aimX = (e.clientX - r.left) / r.width * 2 - 1
      aimY = (e.clientY - r.top) / r.height * 2 - 1
    }
    const reset = () => { aimX = 0; aimY = 0 }
    const parent = host.parentElement!
    parent.addEventListener('pointermove', move, { passive: true }); parent.addEventListener('pointerleave', reset)
    document.addEventListener('visibilitychange', start); reduced.addEventListener('change', start)
    start()
    return () => {
      cancelAnimationFrame(frame); resize.disconnect(); observer.disconnect()
      parent.removeEventListener('pointermove', move); parent.removeEventListener('pointerleave', reset)
      document.removeEventListener('visibilitychange', start); reduced.removeEventListener('change', start)
    }
  }, [paused])
  return <div className="dreamscape" ref={layer}>
    <div className="dreamscape__parallax"><img className="dreamscape__art" src="/art/celestial-dreamscape-v1.png" alt="An immense amethyst planet surrounded by luminous golden dust rings and billowing violet nebula clouds" width="1536" height="1024" loading="eager" /></div>
    <div className="dreamscape__veil" aria-hidden="true" />
    <div className="dreamscape__mist" aria-hidden="true" />
    <canvas ref={canvas} aria-hidden="true" />
    <div className="dreamscape__shade" aria-hidden="true" />
  </div>
}

/** Decorative card parallax never changes layout or steals pointer actions. */
export function useCosmicTilt(paused: boolean) {
  useEffect(() => {
    const fine = matchMedia('(pointer: fine)')
    const reduced = matchMedia('(prefers-reduced-motion: reduce)')
    let active: HTMLElement | null = null
    const reset = () => { if (active) { active.style.removeProperty('--tilt-x'); active.style.removeProperty('--tilt-y'); active = null } }
    const move = (e: PointerEvent) => {
      if (paused || reduced.matches || !fine.matches) { reset(); return }
      const target = (e.target as Element).closest<HTMLElement>('.cosmic-card, .saved-chart')
      if (target !== active) reset()
      if (!target) return
      active = target
      const r = target.getBoundingClientRect()
      target.style.setProperty('--tilt-x', `${-(e.clientY - r.top - r.height / 2) / r.height * 7}deg`)
      target.style.setProperty('--tilt-y', `${(e.clientX - r.left - r.width / 2) / r.width * 7}deg`)
    }
    document.addEventListener('pointermove', move, { passive: true }); document.addEventListener('pointerleave', reset)
    reduced.addEventListener('change', reset)
    return () => { reset(); document.removeEventListener('pointermove', move); document.removeEventListener('pointerleave', reset); reduced.removeEventListener('change', reset) }
  }, [paused])
}
