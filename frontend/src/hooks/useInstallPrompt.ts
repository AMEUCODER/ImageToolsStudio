import { useCallback, useEffect, useState } from 'react'

interface InstallEvent extends Event {
  prompt: () => Promise<void>
}

/** Captures the browser's "install app" prompt so the header can offer it. */
export function useInstallPrompt() {
  const [event, setEvent] = useState<InstallEvent | null>(null)

  useEffect(() => {
    const onPrompt = (e: Event) => {
      e.preventDefault()
      setEvent(e as InstallEvent)
    }
    const onInstalled = () => setEvent(null)
    window.addEventListener('beforeinstallprompt', onPrompt)
    window.addEventListener('appinstalled', onInstalled)
    return () => {
      window.removeEventListener('beforeinstallprompt', onPrompt)
      window.removeEventListener('appinstalled', onInstalled)
    }
  }, [])

  const install = useCallback(async () => {
    if (!event) return
    await event.prompt()
    setEvent(null)
  }, [event])

  return { canInstall: event !== null, install }
}
