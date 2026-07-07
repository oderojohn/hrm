import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "../types";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  setAuth: (data: { access: string; refresh: string; user: User }) => void;
  setAccessToken: (token: string) => void;
  setUser: (user: User) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setAuth: ({ access, refresh, user }) =>
        set({ accessToken: access, refreshToken: refresh, user }),
      setAccessToken: (token) => set({ accessToken: token }),
      setUser: (user) => set({ user }),
      clearAuth: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    { name: "nexas-hrm-auth" }
  )
);

export function hasRole(user: User | null, ...roles: User["role"][]) {
  return !!user && roles.includes(user.role);
}

export function isManagerOrAbove(user: User | null) {
  return hasRole(user, "SUPER_ADMIN", "HR_MANAGER", "DEPARTMENT_MANAGER");
}

export function isHRManagerOrAbove(user: User | null) {
  return hasRole(user, "SUPER_ADMIN", "HR_MANAGER");
}
