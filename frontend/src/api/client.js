const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = localStorage.getItem("lrmisToken");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (!headers.has("Content-Type") && options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    body: options.body && typeof options.body !== "string" && !(options.body instanceof FormData) ? JSON.stringify(options.body) : options.body
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem("lrmisToken");
      localStorage.removeItem("lrmisUser");
    }
    throw new Error(payload.message || payload.detail || "Request failed");
  }
  return payload.data ?? payload;
}

export { API_BASE };

