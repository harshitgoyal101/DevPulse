const REFRESH_KEY = "devpulse_refresh";

export function getStoredRefresh(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

export function setStoredRefresh(token: string): void {
  localStorage.setItem(REFRESH_KEY, token);
}

export function clearStoredRefresh(): void {
  localStorage.removeItem(REFRESH_KEY);
}
