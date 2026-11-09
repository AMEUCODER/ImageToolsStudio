import { useCallback, useState } from 'react'

export interface Toast {
  id: number
  kind: 'info' | 'error'
  text: string
}

let nextId = 1

export function useToasts() {
  const [toasts, setToasts] = useState<Toast[]>([])

  const dismiss = useCallback((id: number) => setToasts((all) => all.filter((t) => t.id !== id)), [])

  const notify = useCallback(
    (kind: Toast['kind'], text: string) => {
      const id = nextId++
      setToasts((all) => [...all.slice(-2), { id, kind, text }])
      setTimeout(() => dismiss(id), kind === 'error' ? 8000 : 3500)
    },
    [dismiss],
  )

  return { toasts, notify, dismiss }
}
