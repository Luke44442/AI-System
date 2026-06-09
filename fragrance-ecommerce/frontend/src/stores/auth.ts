import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Customer } from "@/types";
import { authApi } from "@/lib/api";

interface AuthStore {
  customer: Customer | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, firstName?: string, lastName?: string) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      customer: null,
      token: null,
      isLoading: false,

      login: async (email, password) => {
        set({ isLoading: true });
        try {
          const data = await authApi.login(email, password);
          if (typeof window !== "undefined") localStorage.setItem("scentara_token", data.access_token);
          set({ token: data.access_token, isLoading: false });
          await get().fetchMe();
        } catch (err) {
          set({ isLoading: false });
          throw err;
        }
      },

      register: async (email, password, firstName, lastName) => {
        set({ isLoading: true });
        try {
          const data = await authApi.register(email, password, firstName, lastName);
          if (typeof window !== "undefined") localStorage.setItem("scentara_token", data.access_token);
          set({ token: data.access_token, isLoading: false });
          await get().fetchMe();
        } catch (err) {
          set({ isLoading: false });
          throw err;
        }
      },

      logout: () => {
        if (typeof window !== "undefined") localStorage.removeItem("scentara_token");
        set({ customer: null, token: null });
      },

      fetchMe: async () => {
        try {
          const customer = await authApi.me();
          set({ customer });
        } catch {
          set({ customer: null });
        }
      },
    }),
    { name: "scentara-auth", partialize: (state) => ({ token: state.token }) }
  )
);
