import { loadSystemConfig } from './configService';

let cachedApiBaseUrl = null;

async function getApiBaseUrl() {
  if (cachedApiBaseUrl) {
    return cachedApiBaseUrl;
  }
  const config = await loadSystemConfig();
  cachedApiBaseUrl = config.webui.api_base_url;
  return cachedApiBaseUrl;
}

export async function apiRequest(path, method = 'GET', body = null, requiresAuth = true) {
  const baseUrl = await getApiBaseUrl();
  const headers = { 'Content-Type': 'application/json' };

  if (requiresAuth) {
    const token = localStorage.getItem('trucklog_token');
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${baseUrl}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }

  return response.json();
}
