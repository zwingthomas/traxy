const API_BASE = window.API_BASE_URL;

export async function apiFetch(path, opts = {}) {
  const token = sessionStorage.getItem('token');
  const headers = opts.headers || {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  headers['Content-Type'] = 'application/json';
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  if (res.status === 401) {
    window.location.href = '/login';
    return;
  }
  return res.json();
}