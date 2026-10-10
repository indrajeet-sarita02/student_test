"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useRouter } from "next/navigation";

import { api, isApiError, setUnauthorizedHandler, tokenStore } from "@/lib/api/client";
import { authApi } from "@/lib/api/endpoints";
import { hasPermission as checkPermission, isStaff as checkStaff } from "@/lib/permissions";
import type { MeResponse } from "@/lib/types";

interface AuthContextValue {
  user: MeResponse | null;
  loading: boolean;
  roleCodes: string[];
  permissions: string[];
  login: (username: string, password: string) => Promise<MeResponse>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<MeResponse | null>;
  hasPermission: (code: string) => boolean;
  isStaff: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const mounted = useRef(true);

  const refreshUser = useCallback(async (): Promise<MeResponse | null> => {
    // Recover a session if only the refresh token survived (the access token
    // may have been dropped independently). The API client will refresh it
    // before calling /auth/me.
    if (!tokenStore.getAccess() && !tokenStore.getRefresh()) {
      setUser(null);
      return null;
    }
    // Keep the proxy's cookie fallback in sync for pre-existing sessions.
    tokenStore.mirrorCookie();
    try {
      const me = await authApi.me();
      if (mounted.current) setUser(me);
      return me;
    } catch (err) {
      // Only sign the user out when the backend explicitly rejects the token.
      // A transient network/server error must not wipe a valid session —
      // otherwise a single blip clears localStorage and every subsequent
      // request goes out unauthenticated (MISSING_TOKEN).
      if (isApiError(err) && err.status === 401) {
        tokenStore.clear();
      }
      if (mounted.current) setUser(null);
      return null;
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    setUnauthorizedHandler(() => {
      setUser(null);
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        router.replace("/login");
      }
    });
    (async () => {
      await refreshUser();
      if (mounted.current) setLoading(false);
    })();
    return () => {
      mounted.current = false;
      setUnauthorizedHandler(null);
    };
  }, [refreshUser, router]);

  const login = useCallback(
    async (username: string, password: string) => {
      const tokens = await authApi.login(username, password);
      tokenStore.set(tokens);
      const me = await authApi.me();
      setUser(me);
      return me;
    },
    []
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      /* ignore network/logout errors */
    }
    tokenStore.clear();
    setUser(null);
    router.replace("/login");
  }, [router]);

  const value = useMemo<AuthContextValue>(() => {
    const roleCodes = user?.roles?.map((r) => r.code) ?? [];
    const permissions = user?.permissions ?? [];
    return {
      user,
      loading,
      roleCodes,
      permissions,
      login,
      logout,
      refreshUser,
      hasPermission: (code: string) => checkPermission(permissions, code),
      isStaff: checkStaff(roleCodes),
    };
  }, [user, loading, login, logout, refreshUser]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}

export { api };
