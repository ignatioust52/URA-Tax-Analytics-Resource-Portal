export async function apiFetch(url: string, options: RequestInit = {}) {
  const defaultOptions: RequestInit = {
    ...options,
    credentials: 'include', // Always send cookies for auth
  };

  const res = await fetch(url, defaultOptions);

  if (res.status === 401 || res.status === 403) {
    // Session expired or unauthorized -> Force redirect to login
    window.location.href = '/login';
    throw new Error('Unauthorized or Session Expired');
  }

  if (!res.ok) {
    throw new Error(`API Error: ${res.status}`);
  }

  return res.json();
}
