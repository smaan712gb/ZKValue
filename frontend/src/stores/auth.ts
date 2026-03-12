import { create } from "zustand";
import { persist } from "zustand/middleware";
import api from "@/lib/api";

interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: string;
}

interface User {
  id: string;
  email: string;
  full_name: string;
  role: "owner" | "admin" | "analyst" | "viewer";
  organization: Organization;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    email: string;
    password: string;
    full_name: string;
    org_name: string;
  }) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email, password) => {
        set({ isLoading: true });
        try {
          const res = await api.post("/auth/login", { email, password });
          const { access_token, user } = res.data;
          localStorage.setItem("zkvalue_token", access_token);
          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      register: async (data) => {
        set({ isLoading: true });
        try {
          const res = await api.post("/auth/register", data);
          const { access_token, user } = res.data;
          localStorage.setItem("zkvalue_token", access_token);
          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        localStorage.removeItem("zkvalue_token");
        set({ user: null, token: null, isAuthenticated: false });
        window.location.href = "/login";
      },

      fetchUser: async () => {
        try {
          const res = await api.get("/auth/me");
          set({ user: res.data, isAuthenticated: true });
        } catch {
          set({ user: null, isAuthenticated: false, token: null });
        }
      },
    }),
    {
      name: "zkvalue-auth",
      partialize: (state) => ({ token: state.token }),
    }
  )
);
