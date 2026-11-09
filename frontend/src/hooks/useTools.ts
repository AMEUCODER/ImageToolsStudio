import { useCallback, useEffect, useState } from 'react'
import { ApiError, getTools } from '../services/api'
import type { ToolInfo } from '../types/api'

export type ToolsStatus = 'loading' | 'ready' | 'error' | 'locked'

export function useTools() {
  const [state, setState] = useState<{ status: ToolsStatus; tools: ToolInfo[]; error: string }>({
    status: 'loading',
    tools: [],
    error: '',
  })
  const [nonce, setNonce] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setState((s) => ({ ...s, status: 'loading' }))
    getTools(controller.signal)
      .then((tools) => setState({ status: 'ready', tools, error: '' }))
      .catch((error: Error) => {
        if (controller.signal.aborted) return
        const locked = error instanceof ApiError && error.status === 401
        setState({ status: locked ? 'locked' : 'error', tools: [], error: error.message })
      })
    return () => controller.abort()
  }, [nonce])

  const reload = useCallback(() => setNonce((n) => n + 1), [])
  return { ...state, reload }
}
