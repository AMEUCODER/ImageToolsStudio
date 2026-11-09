import type { Link } from '../hooks/useHealth'
import type { Theme } from '../hooks/useTheme'
import { InstallIcon, MoonIcon, RegistrationMark, SunIcon } from './Icons'

interface Props {
  link: Link
  locked: boolean
  theme: Theme
  canInstall: boolean
  onToggleTheme: () => void
  onInstall: () => void
  onOpenToken: () => void
}

const STATUS: Record<Link, string> = {
  connecting: 'Connecting',
  online: 'Connected',
  offline: 'Server offline',
}

export function Header({ link, locked, theme, canInstall, onToggleTheme, onInstall, onOpenToken }: Props) {
  const label = locked ? 'Access token needed' : STATUS[link]
  const tone = locked ? 'warn' : link
  return (
    <header className="header">
      <div className="brand">
        <RegistrationMark size={26} />
        <span className="brand__name">Image Tools Studio</span>
      </div>

      <div className="header__right">
        {canInstall && (
          <button className="btn btn--ghost" onClick={onInstall}>
            <InstallIcon /> Install app
          </button>
        )}
        <button
          className={`status status--${tone}`}
          onClick={locked ? onOpenToken : undefined}
          disabled={!locked}
          title={locked ? 'Enter the access token' : undefined}
        >
          <span className="status__dot" aria-hidden="true" />
          {label}
        </button>
        <button
          className="icon-btn"
          onClick={onToggleTheme}
          aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
        >
          {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
        </button>
      </div>
    </header>
  )
}
