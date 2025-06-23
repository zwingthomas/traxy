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
  if (sessionStorage.getItem('token')) {
    await syncTimezone();
  }
});

window.apiFetch = async function (path, opts = {}) {
  const token = sessionStorage.getItem('token');
  // Merge headers
  const headers = {
    'Content-Type': 'application/json',
    ...(opts.headers || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(API_BASE + path, {
    ...opts,
    headers,
    credentials: 'include', // send Flask session cookie
  });

  if (res.status === 401) {
    // Not logged in → bounce to login
    window.location.href = '/login';
    return;
  }

  // // do not run .json on no content returns
  // if (res.status === 204) {
  //   return null;
  // }

  // If there's JSON, parse it; otherwise return the raw Response
  const ct = res.headers.get('Content-Type') || '';
  if (ct.includes('application/json')) {
    try {
      data = await res.json();
    } catch {}
  }
  if (!res.ok) {
    // pick up the detail field if provided, or fall back
    const msg = (data && (data.detail || data.message)) || res.statusText;
    throw new Error(msg);
  }
  return data === null ? res : data;
};
