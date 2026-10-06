"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { AuthChangeEvent, Session, User } from "@supabase/supabase-js";

import { getSupabaseClient } from "@/lib/supabase";
import type { AuthUser } from "@/types/auth";

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  register: (email: string, password: string) => Promise<{ needsEmailConfirmation: boolean }>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  getCurrentUser: () => Promise<AuthUser | null>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function mapUser(user: User | null): AuthUser | null {
  if (!user) return null;
  return { id: user.id, email: user.email ?? null, role: "user" };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    let unsubscribe: () => void = () => undefined;

    const initialize = async () => {
      // Finish initialization asynchronously, including configuration failures.
      await Promise.resolve();
      if (!mounted) return;
      try {
        const client = getSupabaseClient();
        let authChanged = false;
        const subscription = client.auth.onAuthStateChange(
          (_event: AuthChangeEvent, session: Session | null) => {
            authChanged = true;
            if (mounted) {
              setUser(mapUser(session?.user ?? null));
              setIsLoading(false);
            }
          },
        );
        unsubscribe = () => subscription.data.subscription.unsubscribe();
        const { data, error } = await client.auth.getSession();
        if (error) throw error;
        if (mounted && !authChanged) setUser(mapUser(data.session?.user ?? null));
      } catch {
        if (mounted) setUser(null);
      } finally {
        if (mounted) setIsLoading(false);
      }
    };
    void initialize();

    return () => {
      mounted = false;
      unsubscribe();
    };
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    isLoading,
    register: async (email, password) => {
      const { data, error } = await getSupabaseClient().auth.signUp({ email, password });
      if (error) throw error;
      setUser(mapUser(data.session?.user ?? null));
      return { needsEmailConfirmation: !data.session };
    },
    login: async (email, password) => {
      const { data, error } = await getSupabaseClient().auth.signInWithPassword({ email, password });
      if (error) throw error;
      setUser(mapUser(data.user));
    },
    logout: async () => {
      const { error } = await getSupabaseClient().auth.signOut();
      if (error) throw error;
      setUser(null);
    },
    getCurrentUser: async () => {
      const { data, error } = await getSupabaseClient().auth.getUser();
      if (error) throw error;
      const current = mapUser(data.user);
      setUser(current);
      return current;
    },
  }), [isLoading, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
