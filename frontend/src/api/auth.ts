import { api, json } from './client';

export interface User {
  id: string;
  email: string;
  is_verified: boolean;
  has_password: boolean;
  google_linked: boolean;
  created_at: string;
}

interface Message {
  message: string;
}

export const authApi = {
  me: () => api<User>('/users/me'),
  register: (email: string, password: string, acceptTerms: boolean) =>
    api<Message>('/auth/register', {
      method: 'POST',
      ...json({ email, password, accept_terms: acceptTerms }),
    }),
  verifyEmail: (token: string) =>
    api<Message>('/auth/verify-email', { method: 'POST', ...json({ token }) }),
  resendVerification: (email: string) =>
    api<Message>('/auth/resend-verification', { method: 'POST', ...json({ email }) }),
  login: (email: string, password: string) =>
    api<User>('/auth/login', { method: 'POST', ...json({ email, password }) }),
  logout: () => api<Message>('/auth/logout', { method: 'POST' }),
  forgotPassword: (email: string) =>
    api<Message>('/auth/password/forgot', { method: 'POST', ...json({ email }) }),
  resetPassword: (token: string, password: string) =>
    api<Message>('/auth/password/reset', { method: 'POST', ...json({ token, password }) }),
  googleLoginUrl: '/api/auth/google/login',
};
