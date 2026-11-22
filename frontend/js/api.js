/* ── API helpers ─────────────────────────────────────────────────────────── */
const BASE = '';

async function apiFetch(path, opts = {}) {
  const url = BASE + path;
  const defaults = {
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
  };
  if (opts.body && typeof opts.body === 'object') {
    opts.body = JSON.stringify(opts.body);
  }
  try {
    const res = await fetch(url, { ...defaults, ...opts, headers: { ...defaults.headers, ...(opts.headers || {}) } });
    const text = await res.text();
    const data = text ? JSON.parse(text) : {};
    if (!res.ok) {
      const msg = data.detail || data.message || `خطا ${res.status}`;
      throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
    return data;
  } catch (e) {
    if (e instanceof TypeError) throw new Error('اتصال به سرور ناموفق بود');
    throw e;
  }
}

const api = {
  get:    (p)       => apiFetch(p),
  post:   (p, body) => apiFetch(p, { method: 'POST',   body }),
  put:    (p, body) => apiFetch(p, { method: 'PUT',    body }),
  patch:  (p, body) => apiFetch(p, { method: 'PATCH',  body }),
  delete: (p)       => apiFetch(p, { method: 'DELETE' }),
};
