import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { AuthUser, ConfigSphereRole } from '@/types';

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  setToken: (token: string) => void;
  setUser: (user: AuthUser) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setToken: (token) => set({ token }),
      setUser: (user) => set({ user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: 'configsphere-auth', partialize: (s) => ({ token: s.token }) }
  )
);

const ROLE_ORDER: Record<ConfigSphereRole, number> = {
  viewer: 0,
  operator: 1,
  approver: 2,
  admin: 3,
};

export const hasRole = (user: AuthUser | null, minRole: ConfigSphereRole): boolean =>
  user ? ROLE_ORDER[user.configsphere_role] >= ROLE_ORDER[minRole] : false;
