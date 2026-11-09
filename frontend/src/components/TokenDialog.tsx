import { useEffect, useRef, useState } from 'react'
import { getToken } from '../services/api'

interface Props {
  open: boolean
  onClose: () => void
  onSave: (token: string) => void
}

export function TokenDialog({ open, onClose, onSave }: Props) {
  const ref = useRef<HTMLDialogElement>(null)
  const [value, setValue] = useState('')

  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    if (open && !dialog.open) {
      setValue(getToken())
      dialog.showModal()
    } else if (!open && dialog.open) {
      dialog.close()
    }
  }, [open])

  return (
    <dialog ref={ref} className="dialog" onClose={onClose}>
      <form
        method="dialog"
        onSubmit={(e) => {
          e.preventDefault()
          onSave(value.trim())
        }}
      >
        <h2 className="dialog__title">Access token</h2>
        <p className="dialog__text">This server asks for a token. Paste the one your administrator gave you. It is stored only in this browser.</p>
        <input
          className="input"
          type="password"
          autoComplete="off"
          spellCheck={false}
          placeholder="Token"
          aria-label="Access token"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          autoFocus
        />
        <div className="dialog__actions">
          <button type="button" className="btn btn--ghost" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn btn--primary">Save token</button>
        </div>
      </form>
    </dialog>
  )
}
