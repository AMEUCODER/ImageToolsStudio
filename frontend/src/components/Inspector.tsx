import { defaultsFor } from '../editor/params'
import type { ParamValue, ParamValues, ToolInfo } from '../types/api'
import { ParamControl } from './ParamControl'
import { ResetIcon, SpinnerIcon } from './Icons'

interface Props {
  tool: ToolInfo | undefined
  values: ParamValues
  hasImage: boolean
  busy: string | null
  onChange: (name: string, value: ParamValue) => void
  onReset: () => void
  onApply: () => void
}

export function Inspector({ tool, values, hasImage, busy, onChange, onReset, onApply }: Props) {
  if (!tool) {
    return (
      <aside className="inspector" aria-label="Options">
        <p className="inspector__empty">Choose a tool to see its options.</p>
      </aside>
    )
  }

  const changed = Object.entries(defaultsFor(tool)).some(([k, v]) => values[k] !== v)
  const disabled = !hasImage || busy !== null

  return (
    <aside className="inspector" aria-label={`${tool.label} options`}>
      <div className="inspector__body">
        <h2 className="inspector__title">{tool.label}</h2>
        {tool.description && <p className="inspector__desc">{tool.description}</p>}

        <div className="inspector__options">
          {tool.params.length === 0 && <p className="opt__help">This tool has no options.</p>}
          {tool.params.map((spec) => (
            <ParamControl
              key={`${tool.name}:${spec.name}`}
              spec={spec}
              value={values[spec.name] ?? spec.default}
              onChange={(v) => onChange(spec.name, v)}
            />
          ))}
        </div>
      </div>

      <div className="inspector__foot">
        <button className="btn btn--primary btn--wide" onClick={onApply} disabled={disabled}>
          {busy ? <><SpinnerIcon /> Applying {busy}</> : `Apply ${tool.label}`}
        </button>
        <div className="inspector__sub">
          <span>{hasImage ? 'Ctrl+Enter applies' : 'Open a photo to apply this tool'}</span>
          <button className="btn btn--ghost btn--small" onClick={onReset} disabled={!changed}>
            <ResetIcon /> Reset options
          </button>
        </div>
      </div>
    </aside>
  )
}
