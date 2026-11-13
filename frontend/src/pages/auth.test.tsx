import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { App } from '../App';
import { passwordStrength } from '../lib/errors';
import { apiError, fakeUser, mockApi, renderWithProviders } from '../test/utils';

describe('login', () => {
  it('signs in and lands on the dashboard', async () => {
    let loggedIn = false;
    mockApi((url) => {
      if (url === '/api/auth/login') {
        loggedIn = true;
        return { status: 200, body: fakeUser };
      }
      if (url === '/api/users/me') {
        return loggedIn ? { status: 200, body: fakeUser } : apiError('not_authenticated', 401);
      }
      return apiError('not_authenticated', 401); // refresh fails while signed out
    });
    renderWithProviders(<App />, { route: '/login' });

    await userEvent.type(await screen.findByLabelText('Email'), 'ana@example.com');
    await userEvent.type(screen.getByLabelText('Contraseña'), 'correct horse battery');
    await userEvent.click(screen.getByRole('button', { name: 'Iniciar sesión' }));

    expect(await screen.findByRole('heading', { name: /Hola, ana@example.com/ })).toBeVisible();
  });

  it('shows a Spanish error and offers to resend verification', async () => {
    const fetchSpy = mockApi((url) => {
      if (url === '/api/auth/login') return apiError('email_not_verified', 403);
      if (url === '/api/auth/resend-verification') return { status: 202, body: { message: 'ok' } };
      return apiError('not_authenticated', 401);
    });
    renderWithProviders(<App />, { route: '/login' });

    await userEvent.type(await screen.findByLabelText('Email'), 'ana@example.com');
    await userEvent.type(screen.getByLabelText('Contraseña'), 'whatever');
    await userEvent.click(screen.getByRole('button', { name: 'Iniciar sesión' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('confirmar tu email');
    await userEvent.click(screen.getByRole('button', { name: /Reenviar/ }));
    expect(await screen.findByText(/nuevo enlace/)).toBeVisible();
    expect(fetchSpy.mock.calls.some((c) => c[0] === '/api/auth/resend-verification')).toBe(true);
  });

  it('shows the Google error coming back from the callback', async () => {
    mockApi(() => apiError('not_authenticated', 401));
    renderWithProviders(<App />, { route: '/login?error=google' });
    expect(await screen.findByText(/No se ha podido iniciar sesión con Google/)).toBeVisible();
  });
});

describe('register', () => {
  it('requires a long enough password and accepting the policy', async () => {
    mockApi((url) =>
      url === '/api/auth/register'
        ? { status: 202, body: { message: 'ok' } }
        : apiError('not_authenticated', 401),
    );
    renderWithProviders(<App />, { route: '/register' });

    const submit = await screen.findByRole('button', { name: 'Crear cuenta' });
    await userEvent.type(screen.getByLabelText('Email'), 'ana@example.com');
    await userEvent.type(screen.getByLabelText('Contraseña'), 'short');
    expect(screen.getByText(/al menos 10 caracteres/)).toBeVisible();
    expect(submit).toBeDisabled();

    await userEvent.type(screen.getByLabelText('Contraseña'), ' but now long');
    expect(submit).toBeDisabled();
    await userEvent.click(screen.getByRole('checkbox'));
    expect(submit).toBeEnabled();

    await userEvent.click(submit);
    expect(await screen.findByRole('heading', { name: 'Revisa tu email' })).toBeVisible();
  });
});

describe('route protection', () => {
  it('redirects anonymous users from /app to /login', async () => {
    mockApi(() => apiError('not_authenticated', 401));
    renderWithProviders(<App />, { route: '/app' });
    expect(await screen.findByRole('heading', { name: 'Inicia sesión' })).toBeVisible();
  });
});

describe('verify email', () => {
  it('verifies the token once', async () => {
    const fetchSpy = mockApi(() => ({ status: 200, body: { message: 'ok' } }));
    renderWithProviders(<App />, { route: '/verify-email?token=tok-1234567890' });
    expect(await screen.findByText(/Email confirmado/)).toBeVisible();
    await waitFor(() =>
      expect(fetchSpy.mock.calls.filter((c) => c[0] === '/api/auth/verify-email')).toHaveLength(1),
    );
  });

  it('explains an invalid link', async () => {
    mockApi(() => apiError('invalid_token', 400));
    renderWithProviders(<App />, { route: '/verify-email?token=bad-token-123' });
    expect(await screen.findByText(/no es válido o ha caducado/)).toBeVisible();
  });
});

describe('passwordStrength', () => {
  it('grades passwords', () => {
    expect(passwordStrength('short')).toBe(0);
    expect(passwordStrength('aaaaaaaaaa')).toBe(1);
    expect(passwordStrength('aaaaaaaaa1')).toBe(2);
    expect(passwordStrength('Aaaaaaaa1!')).toBe(3);
  });
});
