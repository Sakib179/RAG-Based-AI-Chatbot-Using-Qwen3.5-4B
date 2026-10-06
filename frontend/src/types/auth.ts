export interface AuthUser {
  id: string;
  email: string | null;
  role: string;
}

export interface AuthState {
  user: AuthUser | null;
  isLoading: boolean;
}
