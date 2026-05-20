import { apiFetch } from "./client";
import type { LoginCredentials, TokenPair, User } from "../types/auth";

export function login(credentials: LoginCredentials): Promise<TokenPair> {
  return apiFetch<TokenPair>("/api/auth/token/", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}

export function refreshToken(refresh: string): Promise<TokenPair> {
  return apiFetch<TokenPair>("/api/auth/token/refresh/", {
    method: "POST",
    body: JSON.stringify({ refresh }),
  });
}

export function blacklistToken(refresh: string): Promise<void> {
  return apiFetch<void>("/api/auth/token/blacklist/", {
    method: "POST",
    body: JSON.stringify({ refresh }),
  });
}

export function fetchMe(accessToken: string): Promise<User> {
  return apiFetch<User>("/api/auth/me/", { token: accessToken });
}
