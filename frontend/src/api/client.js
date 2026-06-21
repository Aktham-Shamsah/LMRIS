const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  headers.set("X-LRMIS-Role", localStorage.getItem("lrmisRole") || "staff");
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    body: options.body && typeof options.body !== "string" ? JSON.stringify(options.body) : options.body
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.message || payload.detail || "Request failed");
  }
  return payload.data ?? payload;
}

export { API_BASE };

