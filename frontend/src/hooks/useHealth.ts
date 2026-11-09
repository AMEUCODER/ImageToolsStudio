import { useCallback, useEffect, useState } from 'react'
import { getHealth } from '../services/api'
import type { Health } from '../types/api'

export type Link = 'connecting' | 'online' | 'offline'

/** Polls /api/health so the header can show whether the server is reachable. */
export function useHealth(intervalMs = 15000) {
  const [state, setState] = useState<{ link: Link; health: Health | null }>({ link: 'connecting', health: null })
  const [nonce, setNonce] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    let timer: ReturnType<typeof setTimeout>

    const tick = async () => {
      try {
        const health = await getHealth(controller.signal)
        setState({ link: 'online', health })
      } catch {
        if (!controller.signal.aborted) setState((s) => ({ link: 'offline', health: s.health }))
      }
      if (!controller.signal.aborted) timer = setTimeout(tick, intervalMs)
    }
    tick()
    return () => {
      controller.abort()
      clearTimeout(timer)
    }
  }, [intervalMs, nonce])

  const refresh = useCallback(() => setNonce((n) => n + 1), [])
  return { ...state, refresh }
}
