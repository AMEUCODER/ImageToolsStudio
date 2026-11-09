import { useEffect, useRef } from 'react'
import type { Frame } from '../editor/useEditor'
import { UndoIcon } from './Icons'

interface Props {
  frames: Frame[]
  index: number
  busy: boolean
  onSelect: (index: number) => void
  onUndo: () => void
}

/** The edit history as a strip of frames: click one to go back to it. */
export function Filmstrip({ frames, index, busy, onSelect, onUndo }: Props) {
  const active = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    active.current?.scrollIntoView({ block: 'nearest', inline: 'nearest' })
  }, [index, frames.length])

  if (frames.length === 0) return <div className="strip strip--empty" />

  return (
    <div className="strip">
      <ol className="strip__frames" aria-label="Edit history">
        {frames.map((frame, i) => (
          <li key={frame.id}>
            <button
              ref={i === index ? active : undefined}
              className="frame-thumb"
              aria-current={i === index ? 'true' : undefined}
              onClick={() => onSelect(i)}
              disabled={busy}
            >
              <img src={frame.url} alt="" draggable={false} />
              <span className="frame-thumb__label">{frame.label}</span>
            </button>
          </li>
        ))}
      </ol>
      <button className="btn btn--ghost" onClick={onUndo} disabled={busy || index === 0}>
        <UndoIcon /> Undo
      </button>
    </div>
  )
}
