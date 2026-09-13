import { useEffect, useRef, type ReactNode } from 'react'

let windowsOpen = 0
let previousOverflow = ''

export function ReadingWindow({ open, onClose, title, className = '', children, busy = false, resetKey }: {
  open: boolean; onClose: () => void; title: string; className?: string; children: ReactNode; busy?: boolean; resetKey?: number
}) {
  const dialog = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    if (!open) { dialog.current?.close(); return }
    const element = dialog.current
    const previousFocus = document.activeElement as HTMLElement | null
    element?.showModal()
    if (windowsOpen++ === 0) { previousOverflow = document.body.style.overflow; document.body.style.overflow = 'hidden' }
    return () => {
      element?.close()
      if (--windowsOpen === 0) document.body.style.overflow = previousOverflow
      if (previousFocus?.isConnected) previousFocus.focus({ preventScroll: true })
    }
  }, [open])
  useEffect(() => { if (open) dialog.current?.scrollTo({ top: 0, behavior: 'instant' }) }, [open, resetKey])
  return <dialog ref={dialog} className={`reading-window ${className}`} aria-label={title} onCancel={e => { e.preventDefault(); if (!busy) onClose() }}>
    <div className="reading-window__bar"><div><span className="eyebrow">JYOTISH · YOUR PERSONAL SANCTUARY</span><h2>{title}</h2></div><button autoFocus className="window-close" disabled={busy} onClick={onClose} aria-label={`Close ${title}`}>Close <span aria-hidden="true">×</span></button></div>
    {open && children}
  </dialog>
}
