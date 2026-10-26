"use client";

import { authService } from "@/services/authService";
import type { LoginRequest, UserProfile, UserRole } from "@/types/auth";
import { useRouter } from "@/i18n/navigation";
import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  role: UserRole | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<UserProfile>;
  logout: () => void;
  switchDemoUser: (username: string) => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const router = useRouter();

  // Hydrate session from localStorage on client-side mount
  useEffect(() => {
    queueMicrotask(() => {
      try {
        const storedToken = localStorage.getItem("auth_token");
        const storedUser = localStorage.getItem("auth_user");

        if (storedToken && storedUser) {
          setToken(storedToken);
          setUser(JSON.parse(storedUser) as UserProfile);
        }
      } catch (e) {
        console.error("Failed to restore session from localStorage:", e);
        localStorage.removeItem("auth_token");
        localStorage.removeItem("auth_user");
        localStorage.removeItem("auth_role");
      } finally {
        setIsLoading(false);
      }
    });
  }, []);

  const login = useCallback(
    async (credentials: LoginRequest): Promise<UserProfile> => {
      setIsLoading(true);
      try {
        const response = await authService.login(credentials);
        const { access_token, user: loggedUser } = response;

        setToken(access_token);
        setUser(loggedUser);

        localStorage.setItem("auth_token", access_token);
        localStorage.setItem("auth_user", JSON.stringify(loggedUser));
        localStorage.setItem("auth_role", loggedUser.role);

        return loggedUser;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
    localStorage.removeItem("auth_role");
    router.push("/signin");
  }, [router]);

  const switchDemoUser = useCallback(
    async (username: string) => {
      // Default dev password for all seeded accounts is "password123"
      await login({ username, password: "password123" });
    },
    [login]
  );

  const refreshProfile = useCallback(async () => {
    try {
      const freshUser = await authService.getMe();
      setUser(freshUser);
      localStorage.setItem("auth_user", JSON.stringify(freshUser));
      localStorage.setItem("auth_role", freshUser.role);
    } catch (e) {
      console.warn("Session expired during profile refresh:", e);
      logout();
    }
  }, [logout]);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        role: user?.role ?? null,
        isLoading,
        isAuthenticated: !!user && !!token,
        login,
        logout,
        switchDemoUser,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
