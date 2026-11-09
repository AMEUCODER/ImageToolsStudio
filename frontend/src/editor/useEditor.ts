import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, runTool } from '../services/api'
import type { ParamValues, ToolInfo } from '../types/api'

/** One image in the history. Frame 0 is always the original upload. */
export interface Frame {
  id: number
  blob: Blob
  url: string
  width: number
  height: number
  label: string
  ms?: number
}

const MAX_FRAMES = 13            // the original plus 12 edits; older edits are dropped first

type Notify = (kind: 'info' | 'error', text: string) => void

async function readSize(blob: Blob): Promise<{ width: number; height: number }> {
  try {
    const bitmap = await createImageBitmap(blob)
    const size = { width: bitmap.width, height: bitmap.height }
    bitmap.close()
    return size
  } catch {
    throw new Error("This file can't be displayed as an image.")
  }
}

export function useEditor(notify: Notify) {
  const [frames, setFrames] = useState<Frame[]>([])
  const [index, setIndex] = useState(0)
  const [busy, setBusy] = useState<string | null>(null)
  const nextId = useRef(1)
  const abort = useRef<AbortController | null>(null)
  const live = useRef<Frame[]>([])
  live.current = frames

  // Release image memory when the page closes.
  useEffect(() => {
    const frames = live
    return () => {
      frames.current.forEach((f) => URL.revokeObjectURL(f.url))
    }
  }, [])

  const makeFrame = (blob: Blob, width: number, height: number, label: string, ms?: number): Frame => ({
    id: nextId.current++, blob, url: URL.createObjectURL(blob), width, height, label, ms,
  })

  const load = useCallback(
    async (blob: Blob) => {
      try {
        const { width, height } = await readSize(blob)
        abort.current?.abort()
        live.current.forEach((f) => URL.revokeObjectURL(f.url))
        setBusy(null)
        setFrames([makeFrame(blob, width, height, 'Original')])
        setIndex(0)
      } catch (error) {
        notify('error', (error as Error).message)
      }
    },
    [notify],
  )

  const apply = useCallback(
    async (tool: ToolInfo, params: ParamValues) => {
      const source = live.current[index]
      if (!source || busy) return
      const controller = new AbortController()
      abort.current = controller
      setBusy(tool.label)
      try {
        const result = await runTool(tool.name, source.blob, params, controller.signal)
        if (controller.signal.aborted) return
        const frame = makeFrame(result.blob, result.width, result.height, tool.label, result.ms)

        // Editing from an earlier frame starts a new branch, like undo in any editor.
        const kept = live.current.slice(0, index + 1)
        live.current.slice(index + 1).forEach((f) => URL.revokeObjectURL(f.url))
        let next = [...kept, frame]
        if (next.length > MAX_FRAMES) {
          URL.revokeObjectURL(next[1].url)
          next = [next[0], ...next.slice(2)]
        }
        setFrames(next)
        setIndex(next.length - 1)
        notify('info', `${tool.label} applied`)
      } catch (error) {
        if (controller.signal.aborted) return
        notify('error', error instanceof ApiError ? error.message : 'Something went wrong while applying the tool.')
      } finally {
        if (abort.current === controller) {
          abort.current = null
          setBusy(null)
        }
      }
    },
    [index, busy, notify],
  )

  const select = useCallback((i: number) => setIndex((cur) => (busy ? cur : Math.max(0, Math.min(i, live.current.length - 1)))), [busy])
  const undo = useCallback(() => setIndex((i) => (busy ? i : Math.max(0, i - 1))), [busy])

  return { frames, index, current: frames[index], busy, load, apply, select, undo }
}
