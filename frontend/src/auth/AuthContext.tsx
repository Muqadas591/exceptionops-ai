import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

import { api, AUTH_STORAGE_KEY } from "../api";

import type {
  LoginRequest,
  User,
} from "../types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  authenticated: boolean;

  login: (
    credentials: LoginRequest,
  ) => Promise<void>;

  logout: () => void;

  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<
  AuthContextValue | undefined
>(undefined);

export function AuthProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    sessionStorage.removeItem(AUTH_STORAGE_KEY);
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    const token = sessionStorage.getItem(
      AUTH_STORAGE_KEY,
    );

    if (!token) {
      setUser(null);
      return;
    }

    const currentUser = await api.getCurrentUser();

    setUser(currentUser);
  }, []);

  const login = useCallback(
    async (credentials: LoginRequest) => {
      const response = await api.login(credentials);

      sessionStorage.setItem(
        AUTH_STORAGE_KEY,
        response.access_token,
      );

      setUser(response.user);
    },
    [],
  );

  useEffect(() => {
    let mounted = true;

    async function initializeSession() {
      try {
        const token = sessionStorage.getItem(
          AUTH_STORAGE_KEY,
        );

        if (!token) {
          return;
        }

        const currentUser = await api.getCurrentUser();

        if (mounted) {
          setUser(currentUser);
        }
      } catch {
        sessionStorage.removeItem(AUTH_STORAGE_KEY);

        if (mounted) {
          setUser(null);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void initializeSession();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    function handleSessionExpired() {
      logout();
    }

    window.addEventListener(
      "exceptionops:session-expired",
      handleSessionExpired,
    );

    return () => {
      window.removeEventListener(
        "exceptionops:session-expired",
        handleSessionExpired,
      );
    };
  }, [logout]);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        authenticated: Boolean(user),
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider.",
    );
  }

  return context;
}