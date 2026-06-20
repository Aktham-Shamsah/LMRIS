const BASE = '/api/v1'
export const API_BASE = BASE

// FastAPI error responses use {"detail": "..."} (or a list of validation
// errors for 422s); successful responses use {"success","message","data"}.
function extractErrorMessage(json, status) {
  if (!json) return `HTTP ${status}`
  if (typeof json.detail === 'string') return json.detail
  if (Array.isArray(json.detail) && json.detail.length) {
    return json.detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
  }
  return json.message || `HTTP ${status}`
}

async function parseResponse(res) {
  // Read as text first so an empty/non-JSON body never throws a raw,
  // unhelpful "Unexpected end of JSON input" error.
  const text = await res.text()
  let json = null
  if (text) {
    try {
      json = JSON.parse(text)
    } catch {
      json = null
    }
  }

  if (!res.ok) {
    throw new Error(extractErrorMessage(json, res.status))
  }
  if (json === null) {
    throw new Error('Server returned an empty or invalid response.')
  }
  return json
}

async function request(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body !== undefined) opts.body = JSON.stringify(body)

  const res = await fetch(`${BASE}${path}`, opts)
  return parseResponse(res)
}

// Multipart upload — browser sets the Content-Type boundary automatically,
// so it must NOT be set manually on FormData requests.
async function upload(path, file, fields = {}) {
  const form = new FormData()
  form.append('file', file)
  Object.entries(fields).forEach(([key, value]) => form.append(key, value))

  const res = await fetch(`${BASE}${path}`, { method: 'POST', body: form })
  return parseResponse(res)
}

export const api = {
  get: (path) => request('GET', path),
  post: (path, body) => request('POST', path, body),
  patch: (path, body) => request('PATCH', path, body),
  delete: (path) => request('DELETE', path),
  upload,
}
