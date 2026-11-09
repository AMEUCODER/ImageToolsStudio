/** Mirrors engine/schemas (ToolInfo / ParamSpec). The desktop app and this app build controls from the same data. */
export type ParamKind = 'slider' | 'int' | 'choice' | 'bool' | 'text' | 'color'
export type ParamValue = number | string | boolean
export type ParamValues = Record<string, ParamValue>

export interface ParamSpec {
  name: string
  label: string
  kind: ParamKind
  default: ParamValue
  min: number | null
  max: number | null
  step: number | null
  choices: string[]
  help: string
}

export interface ToolInfo {
  name: string
  label: string
  description: string
  params: ParamSpec[]
}

export interface Health {
  status: string
  tools: number
  broken_tools: string[]
  device: string
  auth_required: boolean
  max_upload_mb: number
}
