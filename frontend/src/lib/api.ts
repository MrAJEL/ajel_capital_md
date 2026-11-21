/**
 * AJEL Capital — API Client
 * ==========================
 * All fetch calls go through here.
 * API URL configurable via env var; defaults to same-origin /api (proxied by next.config.js).
 * Auth token attached automatically when available.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

function getAuthHeaders(): Record<string, string> {
  // We now rely on httpOnly cookies
  return {};
}

async function apiFetch<T = any>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
    ...(options.headers as Record<string, string> || {}),
  };

  const res = await fetch(url, { ...options, headers, credentials: 'include' });

  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || errBody.error || `API error ${res.status}`);
  }

  return res.json();
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export async function login(email: string, password: string) {
  const data = await apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (data.user) {
    localStorage.setItem('ajel_user', JSON.stringify(data.user));
  }
  return data;
}

export async function register(email: string, password: string) {
  const data = await apiFetch('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (data.user) {
    localStorage.setItem('ajel_user', JSON.stringify(data.user));
  }
  return data;
}

export async function logout() {
  localStorage.removeItem('ajel_token'); // for backwards compatibility
  localStorage.removeItem('ajel_user');
  try {
    await apiFetch('/auth/logout', { method: 'POST' });
  } catch (e) {
    console.error('Logout API failed', e);
  }
}

export function getStoredUser() {
  if (typeof window === 'undefined') return null;
  const u = localStorage.getItem('ajel_user');
  return u ? JSON.parse(u) : null;
}

export function isAuthenticated(): boolean {
  // Auth relies on httpOnly cookies (set by server), not localStorage.
  // We use the stored user object as a best-effort UI hint only.
  // The real auth check happens on every API call — a 401 means the session expired.
  if (typeof window === 'undefined') return false;
  return !!localStorage.getItem('ajel_user');
}

export async function verifySession(): Promise<boolean> {
  // True server-side session check — hits /auth/me with the httpOnly cookie.
  try {
    await apiFetch('/auth/me');
    return true;
  } catch {
    localStorage.removeItem('ajel_user');
    return false;
  }
}

// ── Status ───────────────────────────────────────────────────────────────────

export async function getStatus() {
  return apiFetch('/status');
}

// ── Prices ───────────────────────────────────────────────────────────────────

export async function getPrice(symbol: string) {
  return apiFetch(`/prices/${encodeURIComponent(symbol)}`);
}

export async function getPricesBatch(symbols: string[]) {
  return apiFetch(`/prices?symbols=${symbols.map(s => encodeURIComponent(s)).join(',')}`);
}

export async function getHistorical(symbol: string, period = '1y', interval = '1wk') {
  return apiFetch(`/historical/${encodeURIComponent(symbol)}?period=${period}&interval=${interval}`);
}

export async function getFundamentals(symbol: string) {
  return apiFetch(`/fundamentals/${encodeURIComponent(symbol)}`);
}

export async function getFearGreed() {
  return apiFetch('/fear-greed');
}

// ── Intelligence ─────────────────────────────────────────────────────────────

export async function getAssetScore(symbol: string) {
  return apiFetch(`/score/${encodeURIComponent(symbol)}`);
}

export async function getBatchScores(symbols: string[]) {
  return apiFetch(`/scores?symbols=${symbols.map(s => encodeURIComponent(s)).join(',')}`);
}

// ── Portfolios ───────────────────────────────────────────────────────────────

export async function getPortfolios() {
  return apiFetch('/portfolios');
}

export async function getPortfolio(id: number) {
  return apiFetch(`/portfolios/${id}`);
}

export async function createPortfolio(data: { name: string; currency?: string; benchmark?: string; client_id?: number }) {
  return apiFetch('/portfolios', { method: 'POST', body: JSON.stringify(data) });
}

export async function deletePortfolio(id: number) {
  return apiFetch(`/portfolios/${id}`, { method: 'DELETE' });
}

// ── Transactions ─────────────────────────────────────────────────────────────

export async function getTransactions(portfolioId?: number, symbol?: string) {
  let path = '/transactions?';
  if (portfolioId) path += `portfolio_id=${portfolioId}&`;
  if (symbol) path += `symbol=${encodeURIComponent(symbol)}&`;
  return apiFetch(path);
}

export async function createTransaction(data: any) {
  return apiFetch('/transactions', { method: 'POST', body: JSON.stringify(data) });
}

export async function deleteTransaction(id: number) {
  return apiFetch(`/transactions/${id}`, { method: 'DELETE' });
}

// ── Positions ────────────────────────────────────────────────────────────────

export async function getPositions(portfolioId?: number) {
  let path = '/positions';
  if (portfolioId) path += `?portfolio_id=${portfolioId}`;
  return apiFetch(path);
}

export async function recalculatePositions(portfolioId: number) {
  return apiFetch(`/positions/recalculate/${portfolioId}`, { method: 'POST' });
}

// ── Clients ──────────────────────────────────────────────────────────────────

export async function getClients() {
  return apiFetch('/clients');
}

export async function getClient(id: number) {
  return apiFetch(`/clients/${id}`);
}

export async function createClient(data: { name: string; email?: string; risk_profile?: string; aum?: number; notes?: string }) {
  return apiFetch('/clients', { method: 'POST', body: JSON.stringify(data) });
}

export async function updateClient(id: number, data: any) {
  return apiFetch(`/clients/${id}`, { method: 'PUT', body: JSON.stringify(data) });
}

export async function deleteClient(id: number) {
  return apiFetch(`/clients/${id}`, { method: 'DELETE' });
}

// ── Portfolio History (Phase 2) ──────────────────────────────────────────────

export async function getPortfolioHistory(id: number) {
  return apiFetch(`/portfolios/${id}/history`);
}

// ── Client Fee Events (Phase 2) ──────────────────────────────────────────────

export async function getClientFeeEvents(id: number) {
  return apiFetch(`/clients/${id}/fee-events`);
}

export async function chargeClientFee(id: number, data: { event_type: string; amount: number; notes?: string }) {
  return apiFetch(`/clients/${id}/charge-fee`, { method: 'POST', body: JSON.stringify(data) });
}

export async function updateClientHWM(id: number, newHwm: number) {
  return apiFetch(`/clients/${id}/update-hwm`, { method: 'POST', body: JSON.stringify({ new_hwm: newHwm }) });
}

export async function addClientCapital(id: number, amount: number) {
  return apiFetch(`/clients/${id}/add-capital?amount=${amount}`, { method: 'POST' });
}
