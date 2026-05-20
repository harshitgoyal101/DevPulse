import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import * as authApi from "../api/auth";
import { ApiError } from "../api/client";
import {
  clearStoredRefresh,
  getStoredRefresh,
  setStoredRefresh,
} from "../lib/tokenStorage";
import type { LoginCredentials, User } from "../types/auth";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface AuthContextValue extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

async function loadSession(
  refresh: string,
): Promise<{ access: string; refresh: string; user: User }> {
  const tokens = await authApi.refreshToken(refresh);
  const user = await authApi.fetchMe(tokens.access);
  return { ...tokens, user };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const applySession = useCallback((access: string, refresh: string, nextUser: User) => {
    setAccessToken(access);
    setStoredRefresh(refresh);
    setUser(nextUser);
    setError(null);
  }, []);

  const clearSession = useCallback(() => {
    setAccessToken(null);
    setUser(null);
    clearStoredRefresh();
  }, []);

  useEffect(() => {
    const refresh = getStoredRefresh();
    if (!refresh) {
      setIsLoading(false);
      return;
    }

    loadSession(refresh)
      .then(({ access, refresh: newRefresh, user: nextUser }) => {
        applySession(access, newRefresh, nextUser);
      })
      .catch(() => {
        clearSession();
      })
      .finally(() => setIsLoading(false));
  }, [applySession, clearSession]);

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      setError(null);
      const tokens = await authApi.login(credentials);
      const nextUser = await authApi.fetchMe(tokens.access);
      applySession(tokens.access, tokens.refresh, nextUser);
    },
    [applySession],
  );

  const logout = useCallback(async () => {
    const refresh = getStoredRefresh();
    clearSession();
    if (refresh) {
      try {
        await authApi.blacklistToken(refresh);
      } catch {
        // Session cleared locally even if blacklist fails (e.g. expired token).
      }
    }
  }, [clearSession]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      accessToken,
      isAuthenticated: Boolean(accessToken && user),
      isLoading,
      error,
      login,
      logout,
      clearError: () => setError(null),
    }),
    [user, accessToken, isLoading, error, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}

export function authErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    return err.message;
  }
  if (err instanceof Error) {
    return err.message;
  }
  return "Something went wrong";
}
