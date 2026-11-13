import { describe, expect, it, vi } from 'vitest';
import { apiError, mockApi } from '../test/utils';
import { api, ApiError, readCookie } from './client';

describe('api client', () => {
  it('sends the CSRF cookie as a header on unsafe requests only', async () => {
    document.cookie = 'csrf_token=abc123; path=/';
    const fetchSpy = mockApi(() => ({ status: 200, body: { ok: true } }));

    await api('/things', { method: 'POST', body: '{}' });
    await api('/things');

    const postHeaders = new Headers(fetchSpy.mock.calls[0]?.[1]?.headers);
    const getHeaders = new Headers(fetchSpy.mock.calls[1]?.[1]?.headers);
    expect(postHeaders.get('X-CSRF-Token')).toBe('abc123');
    expect(getHeaders.get('X-CSRF-Token')).toBeNull();
    expect(fetchSpy.mock.calls[0]?.[1]?.credentials).toBe('include');
    expect(fetchSpy.mock.calls[0]?.[0]).toBe('/api/things');
  });

  it('refreshes the session once on 401 and retries', async () => {
    let calls = 0;
    const fetchSpy = mockApi((url) => {
      if (url === '/api/auth/refresh') return { status: 200, body: { message: 'ok' } };
      calls += 1;
      return calls === 1 ? apiError('not_authenticated', 401) : { status: 200, body: { v: 1 } };
    });

    await expect(api('/users/me')).resolves.toEqual({ v: 1 });
    expect(fetchSpy.mock.calls.map((c) => c[0])).toEqual([
      '/api/users/me',
      '/api/auth/refresh',
      '/api/users/me',
    ]);
  });

  it('does not try to refresh after a failed login', async () => {
    const fetchSpy = mockApi(() => apiError('invalid_credentials', 401));
    await expect(api('/auth/login', { method: 'POST' })).rejects.toMatchObject({
      code: 'invalid_credentials',
      status: 401,
    });
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it('maps non-JSON errors to an ApiError', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('oops', { status: 502 }));
    const error = await api('/x').catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).code).toBe('http_502');
  });

  it('reads cookies by exact name', () => {
    document.cookie = 'csrf_token_old=zzz; path=/';
    document.cookie = 'csrf_token=yyy; path=/';
    expect(readCookie('csrf_token')).toBe('yyy');
    expect(readCookie('missing')).toBeUndefined();
  });
});
