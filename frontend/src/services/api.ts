import axios, { type InternalAxiosRequestConfig } from "axios";
import type { Session } from "@supabase/supabase-js";

import { getSupabaseClient } from "@/lib/supabase";

export class SessionError extends Error {
  readonly status = 401;

  constructor(message = "Your session has expired. Please sign in again.") {
    super(message);
    this.name = "SessionError";
  }
}

type AuthRequestConfig = InternalAxiosRequestConfig & { sessionRetried?: boolean };
let refreshingSession: Promise<Session> | null = null;

async function refreshSession(): Promise<Session> {
  // Concurrent requests share one refresh to avoid rotating the token twice.
  if (!refreshingSession) {
    refreshingSession = getSupabaseClient().auth.refreshSession().then(({ data, error }) => {
      if (error || !data.session) throw new SessionError();
      return data.session;
    }).finally(() => { refreshingSession = null; });
  }
  return refreshingSession;
}

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
});

api.interceptors.request.use(async (config) => {
  const { data, error } = await getSupabaseClient().auth.getSession();
  if (error || !data.session) throw new SessionError();
  let session = data.session;
  if (session.expires_at && session.expires_at <= Math.floor(Date.now() / 1000) + 60) {
    session = await refreshSession();
  }
  config.headers.set("Authorization", `Bearer ${session.access_token}`);
  // Let the browser set multipart boundaries for document uploads.
  if (config.data instanceof FormData) config.headers.delete("Content-Type");
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error)) return Promise.reject(error);
    const config = error.config as AuthRequestConfig | undefined;
    if (error.response?.status === 401 && config) {
      if (!config.sessionRetried) {
        config.sessionRetried = true;
        try {
          const session = await refreshSession();
          config.headers.set("Authorization", `Bearer ${session.access_token}`);
          return api.request(config);
        } catch {
          return Promise.reject(new SessionError());
        }
      }
      return Promise.reject(new SessionError("Your session could not be verified. Please sign in again."));
    }
    return Promise.reject(error);
  },
);
