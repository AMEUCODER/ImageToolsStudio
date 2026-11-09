import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Filmstrip } from './components/Filmstrip'
import { Header } from './components/Header'
import { Inspector } from './components/Inspector'
import { Stage } from './components/Stage'
import { Toasts } from './components/Toasts'
import { TokenDialog } from './components/TokenDialog'
import { ToolRail } from './components/ToolRail'
import { defaultsFor } from './editor/params'
import { makeSampleImage } from './editor/sample'
import { useEditor } from './editor/useEditor'
import { useHealth } from './hooks/useHealth'
import { useInstallPrompt } from './hooks/useInstallPrompt'
import { useTheme } from './hooks/useTheme'
import { useToasts } from './hooks/useToasts'
import { useTools } from './hooks/useTools'
import { setToken } from './services/api'
import type { ParamValue, ParamValues } from './types/api'

const EXTENSIONS: Record<string, string> = { 'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp' }

const isTyping = (target: EventTarget | null) =>
  target instanceof HTMLElement && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT')

export function App() {
  const { theme, toggle } = useTheme()
  const { toasts, notify, dismiss } = useToasts()
  const health = useHealth()
  const tools = useTools()
  const editor = useEditor(notify)
  const install = useInstallPrompt()

  const [activeName, setActiveName] = useState<string | null>(null)
  const [valuesByTool, setValuesByTool] = useState<Record<string, ParamValues>>({})
  const [tokenOpen, setTokenOpen] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)

  const maxMb = health.health?.max_upload_mb ?? 25
  const tool = useMemo(
    () => tools.tools.find((t) => t.name === activeName) ?? tools.tools[0],
    [tools.tools, activeName],
  )
  const values = tool ? (valuesByTool[tool.name] ?? defaultsFor(tool)) : {}

  // ---- opening images ----
  const openFile = useCallback(
    (file: File) => {
      if (!file.type.startsWith('image/')) return notify('error', "That file isn't an image. Use PNG, JPEG or WebP.")
      if (file.size > maxMb * 1024 * 1024) return notify('error', `That image is larger than ${maxMb} MB.`)
      editor.load(file)
    },
    [editor.load, maxMb, notify],
  )

  const openSample = useCallback(async () => editor.load(await makeSampleImage()), [editor.load])

  // ---- editing ----
  const setValue = (name: string, value: ParamValue) =>
    tool && setValuesByTool((all) => ({ ...all, [tool.name]: { ...(all[tool.name] ?? defaultsFor(tool)), [name]: value } }))

  const resetValues = () => tool && setValuesByTool((all) => ({ ...all, [tool.name]: defaultsFor(tool) }))

  const apply = useCallback(() => {
    if (tool && editor.current && !editor.busy) editor.apply(tool, valuesByTool[tool.name] ?? defaultsFor(tool))
  }, [tool, editor.current, editor.busy, editor.apply, valuesByTool])

  const download = () => {
    const frame = editor.current
    if (!frame) return
    const link = document.createElement('a')
    link.href = frame.url
    link.download = `${frame.label.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-${frame.id}.${EXTENSIONS[frame.blob.type] ?? 'png'}`
    link.click()
  }

  // ---- keyboard and clipboard ----
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const mod = e.ctrlKey || e.metaKey
      if (!mod) return
      if (e.key === 'Enter') {
        e.preventDefault()
        apply()
      } else if (e.key.toLowerCase() === 'z' && !isTyping(e.target)) {
        e.preventDefault()
        editor.undo()
      } else if (e.key.toLowerCase() === 'o') {
        e.preventDefault()
        fileInput.current?.click()
      }
    }
    const onPaste = (e: ClipboardEvent) => {
      if (isTyping(e.target)) return
      const file = Array.from(e.clipboardData?.files ?? []).find((f) => f.type.startsWith('image/'))
      if (file) {
        e.preventDefault()
        openFile(file)
      }
    }
    window.addEventListener('keydown', onKey)
    window.addEventListener('paste', onPaste)
    return () => {
      window.removeEventListener('keydown', onKey)
      window.removeEventListener('paste', onPaste)
    }
  }, [apply, editor.undo, openFile])

  const saveToken = (token: string) => {
    setToken(token)
    setTokenOpen(false)
    tools.reload()
    health.refresh()
  }

  return (
    <div className="app">
      <Header
        link={health.link}
        locked={tools.status === 'locked'}
        theme={theme}
        canInstall={install.canInstall}
        onToggleTheme={toggle}
        onInstall={install.install}
        onOpenToken={() => setTokenOpen(true)}
      />

      <main className="workbench">
        <ToolRail
          tools={tools.tools}
          status={tools.status}
          error={tools.error}
          active={tool?.name ?? null}
          onSelect={setActiveName}
          onRetry={() => {
            tools.reload()
            health.refresh()
          }}
          onOpenToken={() => setTokenOpen(true)}
        />

        <div className="center">
          <Stage
            frames={editor.frames}
            index={editor.index}
            busy={editor.busy}
            maxMb={maxMb}
            onOpen={() => fileInput.current?.click()}
            onSample={openSample}
            onDownload={download}
            onDropFile={openFile}
          />
          <Filmstrip
            frames={editor.frames}
            index={editor.index}
            busy={editor.busy !== null}
            onSelect={editor.select}
            onUndo={editor.undo}
          />
        </div>

        <Inspector
          tool={tool}
          values={values}
          hasImage={editor.current !== undefined}
          busy={editor.busy}
          onChange={setValue}
          onReset={resetValues}
          onApply={apply}
        />
      </main>

      <input
        ref={fileInput}
        type="file"
        accept="image/*"
        hidden
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) openFile(file)
          e.target.value = ''
        }}
      />
      <Toasts toasts={toasts} onDismiss={dismiss} />
      <TokenDialog open={tokenOpen} onClose={() => setTokenOpen(false)} onSave={saveToken} />
    </div>
  )
}
