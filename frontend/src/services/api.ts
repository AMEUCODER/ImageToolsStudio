import type { Health, ParamValues, ToolInfo } from '../types/api'

/** Empty in production and dev (same origin, proxied). Set VITE_API_BASE to call another server. */
const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? ''
const TOKEN_KEY = 'studio.token'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export const getToken = (): string => {
  try {
    return localStorage.getItem(TOKEN_KEY) ?? ''
  } catch {
    return ''
  }
}

export const setToken = (token: string): void => {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* storage can be blocked; the token then only lives until reload */
  }
}

const authHeaders = (): Record<string, string> => {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request(path: string, init: RequestInit): Promise<Response> {
  let res: Response
  try {
    res = await fetch(`${BASE}${path}`, init)
  } catch (error) {
    if (init.signal?.aborted) throw error
    throw new ApiError(0, "Can't reach the server. Check that the backend is running, then try again.")
  }
  if (res.ok) return res

  let message = `The server returned an error (${res.status}).`
  try {
    const body = await res.json()
    if (typeof body.detail === 'string') message = body.detail
    else if (Array.isArray(body.detail)) message = body.detail.map((d: { msg: string }) => d.msg).join('; ')
  } catch {
    /* not JSON: keep the generic message */
  }
  throw new ApiError(res.status, message)
}

export async function getHealth(signal?: AbortSignal): Promise<Health> {
  return (await request('/api/health', { signal })).json()
}

export async function getTools(signal?: AbortSignal): Promise<ToolInfo[]> {
  return (await request('/api/tools', { headers: authHeaders(), signal })).json()
}

export interface RunResult {
  blob: Blob
  width: number
  height: number
  ms: number
}

export async function runTool(
  tool: string,
  image: Blob,
  params: ParamValues,
  signal?: AbortSignal,
): Promise<RunResult> {
  const form = new FormData()
  form.append('file', image, 'image')
  form.append('params', JSON.stringify(params))
  form.append('format', 'png')

  const res = await request(`/api/tools/${encodeURIComponent(tool)}`, {
    method: 'POST',
    body: form,
    headers: authHeaders(),
    signal,
  })
  return {
    blob: await res.blob(),
    width: Number(res.headers.get('X-Image-Width')),
    height: Number(res.headers.get('X-Image-Height')),
    ms: Number(res.headers.get('X-Process-Ms')),
  }
}
