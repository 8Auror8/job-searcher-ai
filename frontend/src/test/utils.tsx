import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render } from '@testing-library/react';
import type { ReactElement } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';

export function renderWithProviders(ui: ReactElement, { route = '/' } = {}) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

type Handler = (url: string, init: RequestInit) => { status: number; body?: unknown };

/** Replaces global fetch with a router of fake API responses. Returns the spy. */
export function mockApi(handler: Handler) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init = {}) => {
    const { status, body } = handler(String(input), init);
    return new Response(body === undefined ? null : JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    });
  });
}

export const apiError = (code: string, status: number) => ({
  status,
  body: { error: { code, message: code } },
});

export const fakeUser = {
  id: '1',
  email: 'ana@example.com',
  is_verified: true,
  has_password: true,
  google_linked: false,
  created_at: '2026-11-16T10:00:00Z',
};
