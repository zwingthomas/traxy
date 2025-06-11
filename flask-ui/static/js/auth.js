const API_BASE = window.API_BASE_URL;

// Get timezone of user
async function syncTimezone() {
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
  // fire & forget
  await window.apiFetch('/api/users/me', {
    method: 'PATCH',
    body: JSON.stringify({ timezone: tz }),
  });
}

// on page load
document.addEventListener('DOMContentLoaded', async () => {
  await syncTimezone();
});

window.apiFetch = async function(path, opts = {}) {
  const token = sessionStorage.getItem('token');
  // Merge headers
  const headers = {
    'Content-Type': 'application/json',
    ...(opts.headers || {})
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(API_BASE + path, {
    ...opts,
    headers,
    credentials: 'include'    // send Flask session cookie
  });

  if (res.status === 401) {
    // Not logged in → bounce to login
    window.location.href = '/login';
    return;
  }

  // If there's JSON, parse it; otherwise return the raw Response
  const ct = res.headers.get('Content-Type') || '';
  if (ct.includes('application/json')) {
    return res.json();
  }
  return res;
};