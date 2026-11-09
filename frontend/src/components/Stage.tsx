import { useState, type DragEvent } from 'react'
import type { Frame } from '../editor/useEditor'
import { Compare } from './Compare'
import { CompareIcon, DownloadIcon, OpenIcon } from './Icons'

interface Props {
  frames: Frame[]
  index: number
  busy: string | null
  maxMb: number
  onOpen: () => void
  onSample: () => void
  onDownload: () => void
  onDropFile: (file: File) => void
}

export function Stage({ frames, index, busy, maxMb, onOpen, onSample, onDownload, onDropFile }: Props) {
  const [dragging, setDragging] = useState(false)
  const [compare, setCompare] = useState(true)

  const current = frames[index]
  const before = index > 0 ? frames[index - 1] : undefined
  // The slider only lines up when both images have the same shape (a crop changes the shape).
  const sameShape = !!before && !!current && Math.abs(before.width / before.height - current.width / current.height) < 0.01
  const comparing = compare && sameShape

  const onDragOver = (e: DragEvent) => {
    if (!e.dataTransfer.types.includes('Files')) return
    e.preventDefault()
    setDragging(true)
  }
  const onDrop = (e: DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) onDropFile(file)
  }

  return (
    <section className="stage" aria-label="Image">
      <div className="stage__bar">
        <div className="stage__meta">
          {current && <span className="chip">{current.width} × {current.height} px</span>}
          {current?.ms != null && <span className="chip chip--accent">{current.label} took {current.ms} ms</span>}
        </div>
        <div className="stage__actions">
          <button className="btn" onClick={onOpen}><OpenIcon /> Open photo</button>
          {sameShape && (
            <button className="btn" aria-pressed={compare} onClick={() => setCompare((c) => !c)}>
              <CompareIcon /> Compare
            </button>
          )}
          {current && <button className="btn" onClick={onDownload}><DownloadIcon /> Download</button>}
        </div>
      </div>

      <div
        className={`stage__canvas${dragging ? ' is-dragging' : ''}`}
        onDragOver={onDragOver}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        {!current ? (
          <div className="drop">
            <span className="drop__mark drop__mark--tl" />
            <span className="drop__mark drop__mark--tr" />
            <span className="drop__mark drop__mark--bl" />
            <span className="drop__mark drop__mark--br" />
            <h1 className="drop__title">Drop a photo to start</h1>
            <p className="drop__hint">
              PNG, JPEG or WebP, up to {maxMb} MB. You can also paste an image from the clipboard.
            </p>
            <div className="drop__actions">
              <button className="btn btn--primary" onClick={onOpen}>Choose a photo</button>
              <button className="btn" onClick={onSample}>Use a sample</button>
            </div>
          </div>
        ) : (
          <div
            className={`frame${busy ? ' is-busy' : ''}`}
            style={{ '--ar': `${current.width} / ${current.height}`, '--arn': current.width / current.height } as React.CSSProperties}
          >
            {comparing && before ? (
              <Compare before={before} after={current} />
            ) : (
              <img className="frame__img" src={current.url} alt={`${current.label} image`} draggable={false} />
            )}
            {busy && (
              <div className="frame__busy" role="status">
                <span className="frame__sweep" />
                <span className="frame__busy-text">Applying {busy}</span>
              </div>
            )}
          </div>
        )}

        {dragging && <div className="stage__veil">Drop to open this photo</div>}
      </div>
    </section>
  )
}
