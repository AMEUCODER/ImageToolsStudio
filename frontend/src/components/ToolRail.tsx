import type { ToolsStatus } from '../hooks/useTools'
import type { ToolInfo } from '../types/api'
import { ToolIcon } from './Icons'

interface Props {
  tools: ToolInfo[]
  status: ToolsStatus
  error: string
  active: string | null
  onSelect: (name: string) => void
  onRetry: () => void
  onOpenToken: () => void
}

export function ToolRail({ tools, status, error, active, onSelect, onRetry, onOpenToken }: Props) {
  return (
    <nav className="rail" aria-label="Tools">
      {status === 'loading' && (
        <ul className="rail__list" aria-busy="true" aria-label="Loading tools">
          {[0, 1, 2, 3, 4].map((i) => (
            <li key={i}><span className="tool tool--skeleton" /></li>
          ))}
        </ul>
      )}

      {status === 'error' && (
        <div className="rail__note" role="alert">
          <p>{error}</p>
          <button className="btn" onClick={onRetry}>Try again</button>
        </div>
      )}

      {status === 'locked' && (
        <div className="rail__note">
          <p>This server needs an access token before it shows its tools.</p>
          <button className="btn" onClick={onOpenToken}>Enter token</button>
        </div>
      )}

      {status === 'ready' && (
        <ul className="rail__list">
          {tools.map((tool) => (
            <li key={tool.name}>
              <button
                className="tool"
                aria-current={tool.name === active ? 'true' : undefined}
                onClick={() => onSelect(tool.name)}
                title={tool.description}
              >
                <ToolIcon name={tool.name} />
                <span className="tool__label">{tool.label}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </nav>
  )
}
