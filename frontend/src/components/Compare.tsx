import { useRef, useState, type KeyboardEvent, type PointerEvent } from 'react'
import type { Frame } from '../editor/useEditor'
import { RegistrationMark } from './Icons'

const clamp = (n: number) => Math.max(0, Math.min(100, n))

/** Before on the left, after on the right. Drag anywhere, or focus the handle and use the arrow keys. */
export function Compare({ before, after }: { before: Frame; after: Frame }) {
  const box = useRef<HTMLDivElement>(null)
  const dragging = useRef(false)
  const [pos, setPos] = useState(50)

  const moveTo = (clientX: number) => {
    const rect = box.current?.getBoundingClientRect()
    if (rect && rect.width > 0) setPos(clamp(((clientX - rect.left) / rect.width) * 100))
  }

  const onDown = (e: PointerEvent<HTMLDivElement>) => {
    dragging.current = true
    e.currentTarget.setPointerCapture(e.pointerId)
    moveTo(e.clientX)
  }
  const onKey = (e: KeyboardEvent<HTMLDivElement>) => {
    const step = e.shiftKey ? 10 : 2
    if (e.key === 'ArrowLeft') setPos((p) => clamp(p - step))
    else if (e.key === 'ArrowRight') setPos((p) => clamp(p + step))
    else if (e.key === 'Home') setPos(0)
    else if (e.key === 'End') setPos(100)
    else return
    e.preventDefault()
  }

  return (
    <div
      ref={box}
      className="compare"
      onPointerDown={onDown}
      onPointerMove={(e) => dragging.current && moveTo(e.clientX)}
      onPointerUp={() => (dragging.current = false)}
      onPointerCancel={() => (dragging.current = false)}
    >
      <img className="compare__img" src={before.url} alt="Before" draggable={false} />
      <img className="compare__img" src={after.url} alt="After" draggable={false} style={{ clipPath: `inset(0 0 0 ${pos}%)` }} />
      <span className="compare__tag compare__tag--before">Before</span>
      <span className="compare__tag compare__tag--after">After</span>
      <div
        className="compare__handle"
        style={{ left: `${pos}%` }}
        role="slider"
        tabIndex={0}
        aria-label="Compare before and after"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(pos)}
        onKeyDown={onKey}
      >
        <span className="compare__line" />
        <span className="compare__grip"><RegistrationMark size={34} /></span>
      </div>
    </div>
  )
}
