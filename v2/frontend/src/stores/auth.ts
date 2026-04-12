import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import { AuthUser } from '@/types';

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  devMode: boolean;
  loginDev: (email: string, displayName: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      devMode: true,
      loginDev: (email, displayName) =>
        set({
          token: `dev-token:${email}`,
          user: { email, displayName },
          devMode: true,
        }),
      logout: () => set({ token: null, user: null }),
    }),
    {
      name: 'configsphere-v2-auth',
    }
  )
);

