import type { ParamSpec, ParamValues, ToolInfo } from '../types/api'

export const defaultsFor = (tool: ToolInfo): ParamValues =>
  Object.fromEntries(tool.params.map((p) => [p.name, p.default]))

export const percent = (spec: ParamSpec, value: number): number => {
  const min = spec.min ?? 0
  const max = spec.max ?? 100
  return max === min ? 0 : ((value - min) / (max - min)) * 100
}

/** 0.7 -> "0.7", 12 -> "12", 1.0 -> "1" */
export const formatNumber = (value: number): string => String(Number(value.toFixed(2)))
