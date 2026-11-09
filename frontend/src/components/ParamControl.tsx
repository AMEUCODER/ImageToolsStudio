import type { CSSProperties } from 'react'
import { formatNumber, percent } from '../editor/params'
import type { ParamSpec, ParamValue } from '../types/api'

interface Props {
  spec: ParamSpec
  value: ParamValue
  onChange: (value: ParamValue) => void
}

/** Renders one option of a tool. The kind comes from the engine's ParamSpec, so new tools need no UI code. */
export function ParamControl({ spec, value, onChange }: Props) {
  const id = `opt-${spec.name}`

  switch (spec.kind) {
    case 'slider':
    case 'int': {
      const n = Number(value)
      const min = spec.min ?? 0
      const max = spec.max ?? 100
      const step = spec.kind === 'int' ? 1 : (spec.step ?? (max - min) / 100)
      return (
        <div className="opt">
          <div className="opt__head">
            <label htmlFor={id}>{spec.label}</label>
            <output htmlFor={id} className="opt__value">{formatNumber(n)}</output>
          </div>
          <input
            id={id}
            className="range"
            type="range"
            min={min}
            max={max}
            step={step}
            value={n}
            style={{ '--p': `${percent(spec, n)}%` } as CSSProperties}
            onChange={(e) => onChange(Number(e.target.value))}
          />
          {spec.help && <p className="opt__help">{spec.help}</p>}
        </div>
      )
    }

    case 'choice': {
      const compact = spec.choices.length <= 4 && spec.choices.every((c) => c.length <= 10)
      return (
        <div className="opt">
          <div className="opt__head"><label htmlFor={id}>{spec.label}</label></div>
          {compact ? (
            <div className="segmented" role="radiogroup" aria-label={spec.label}>
              {spec.choices.map((choice) => (
                <button
                  key={choice}
                  type="button"
                  role="radio"
                  aria-checked={value === choice}
                  className="segmented__item"
                  onClick={() => onChange(choice)}
                >
                  {choice}
                </button>
              ))}
            </div>
          ) : (
            <select id={id} className="select" value={String(value)} onChange={(e) => onChange(e.target.value)}>
              {spec.choices.map((choice) => <option key={choice} value={choice}>{choice}</option>)}
            </select>
          )}
          {spec.help && <p className="opt__help">{spec.help}</p>}
        </div>
      )
    }

    case 'bool':
      return (
        <div className="opt opt--row">
          <label htmlFor={id}>{spec.label}</label>
          <button
            id={id}
            type="button"
            role="switch"
            aria-checked={Boolean(value)}
            className="switch"
            onClick={() => onChange(!value)}
          >
            <span className="switch__knob" />
          </button>
        </div>
      )

    case 'text':
      return (
        <div className="opt">
          <div className="opt__head"><label htmlFor={id}>{spec.label}</label></div>
          <input
            id={id}
            className="input"
            type="text"
            value={String(value)}
            maxLength={spec.max ?? 200}
            onChange={(e) => onChange(e.target.value)}
          />
          {spec.help && <p className="opt__help">{spec.help}</p>}
        </div>
      )

    case 'color':
      return (
        <div className="opt opt--row">
          <label htmlFor={id}>{spec.label}</label>
          <span className="swatch">
            <input id={id} className="swatch__input" type="color" value={String(value)} onChange={(e) => onChange(e.target.value)} />
            <span className="swatch__hex">{String(value)}</span>
          </span>
        </div>
      )

    default:
      return null
  }
}
