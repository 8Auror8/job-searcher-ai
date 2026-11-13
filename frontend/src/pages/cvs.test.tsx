import { fireEvent, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { App } from '../App';
import type { CvDetail } from '../api/cvs';
import { apiError, fakeUser, mockApi, renderWithProviders } from '../test/utils';

const detail: CvDetail = {
  id: 'cv-1',
  name: 'Mi CV',
  origin: 'upload',
  is_primary: true,
  archived: false,
  extraction_status: 'ok',
  created_at: '2026-11-20T10:00:00Z',
  updated_at: '2026-11-20T10:00:00Z',
  has_source_text: true,
  extraction_notes: {
    prompt_version: 'cv_extraction_v1',
    unverified: [{ field: 'skills', value: 'Kubernetes' }],
  },
  profile: {
    full_name: 'Laura Gomez',
    headline: 'Backend Developer',
    summary: null,
    email: null,
    phone: null,
    location: 'Madrid',
    links: [],
    total_years_experience: 5,
    skills: ['Python', 'FastAPI'],
    languages: [],
    experience: [],
    education: [],
    certifications: [],
  },
};

const pdf = () => new File(['%PDF-1.4 fake'], 'cv.pdf', { type: 'application/pdf' });

describe('CVs page', () => {
  it('uploads a CV with consent and opens the editor', async () => {
    const calls: { url: string; method: string; body: unknown }[] = [];
    mockApi((url, init) => {
      calls.push({ url, method: init.method ?? 'GET', body: init.body });
      if (url === '/api/users/me') return { status: 200, body: fakeUser };
      if (url === '/api/cvs' && init.method === 'POST') return { status: 201, body: detail };
      if (url === '/api/cvs') return { status: 200, body: [] };
      if (url === '/api/cvs/cv-1') return { status: 200, body: detail };
      return apiError('not_found', 404);
    });
    renderWithProviders(<App />, { route: '/app/cvs' });

    expect(await screen.findByText(/Aún no tienes ningún CV/)).toBeVisible();
    await userEvent.click(screen.getByRole('button', { name: 'Subir CV' }));

    const analyse = screen.getByRole('button', { name: 'Analizar CV' });
    expect(analyse).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Archivo del CV'), { target: { files: [pdf()] } });
    await userEvent.click(screen.getByRole('checkbox', { name: /Doy mi consentimiento/ }));
    await userEvent.click(analyse);

    expect(await screen.findByRole('heading', { name: 'Mi CV' })).toBeVisible();
    const upload = calls.find((c) => c.url === '/api/cvs' && c.method === 'POST');
    const form = upload?.body as FormData;
    expect(form.get('consent')).toBe('true');
    expect(form.get('origin')).toBe('upload');
    expect((form.get('file') as File).name).toBe('cv.pdf');
  });

  it('shows LinkedIn instructions and sends the linkedin origin', async () => {
    let origin: FormDataEntryValue | null = null;
    mockApi((url, init) => {
      if (url === '/api/users/me') return { status: 200, body: fakeUser };
      if (url === '/api/cvs' && init.method === 'POST') {
        origin = (init.body as FormData).get('origin');
        return apiError('cv_unreadable', 422);
      }
      if (url === '/api/cvs') return { status: 200, body: [] };
      return apiError('not_found', 404);
    });
    renderWithProviders(<App />, { route: '/app/cvs' });

    await userEvent.click(await screen.findByRole('button', { name: 'Importar de LinkedIn' }));
    expect(screen.getByText(/JobPilot no se conecta a LinkedIn/)).toBeVisible();
    fireEvent.change(screen.getByLabelText('Archivo del CV'), { target: { files: [pdf()] } });
    await userEvent.click(screen.getByRole('button', { name: 'Analizar CV' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('No hemos podido leer texto');
    expect(origin).toBe('linkedin_pdf');
  });

  it('lists versions and marks one as primary', async () => {
    const second = { ...detail, id: 'cv-2', name: 'CV Data', is_primary: false };
    let patched: unknown = null;
    mockApi((url, init) => {
      if (url === '/api/users/me') return { status: 200, body: fakeUser };
      if (url === '/api/cvs/cv-2' && init.method === 'PATCH') {
        patched = JSON.parse(String(init.body));
        return { status: 200, body: { ...second, is_primary: true } };
      }
      if (url === '/api/cvs') return { status: 200, body: [detail, second] };
      return apiError('not_found', 404);
    });
    renderWithProviders(<App />, { route: '/app/cvs' });

    expect(await screen.findByText('Principal')).toBeVisible();
    await userEvent.click(screen.getByRole('button', { name: 'Marcar como principal' }));
    await waitFor(() => expect(patched).toEqual({ is_primary: true }));
  });
});

describe('CV editor', () => {
  it('warns about unverified AI data and saves edits', async () => {
    let saved: Record<string, unknown> | null = null;
    mockApi((url, init) => {
      if (url === '/api/users/me') return { status: 200, body: fakeUser };
      if (url === '/api/cvs/cv-1/profile') {
        saved = JSON.parse(String(init.body));
        return { status: 200, body: { ...detail, profile: saved } };
      }
      if (url === '/api/cvs/cv-1') return { status: 200, body: detail };
      if (url.startsWith('/api/cvs')) return { status: 200, body: [] };
      return apiError('not_found', 404);
    });
    renderWithProviders(<App />, { route: '/app/cvs/cv-1' });

    expect(await screen.findByText(/no aparecen tal cual en tu CV/)).toBeVisible();
    expect(screen.getByText('Kubernetes')).toBeVisible();

    const save = screen.getByRole('button', { name: 'Guardar perfil' });
    expect(save).toBeDisabled();
    await userEvent.type(screen.getByLabelText('Añadir habilidades'), 'Kubernetes{Enter}');
    await userEvent.click(screen.getByRole('button', { name: 'Quitar FastAPI' }));
    await userEvent.click(save);

    await waitFor(() => expect(saved).not.toBeNull());
    expect(saved!.skills).toEqual(['Python', 'Kubernetes']);
    expect(await screen.findByText('Guardado ✓')).toBeVisible();
  });
});

describe('preferences', () => {
  it('loads and saves search preferences', async () => {
    let saved: Record<string, unknown> | null = null;
    mockApi((url, init) => {
      if (url === '/api/users/me') return { status: 200, body: fakeUser };
      if (url === '/api/preferences' && init.method === 'PUT') {
        saved = JSON.parse(String(init.body));
        return { status: 200, body: saved };
      }
      if (url === '/api/preferences') {
        return {
          status: 200,
          body: { roles: [], locations: [], remote: 'any', min_salary: null, sources: [] },
        };
      }
      return apiError('not_found', 404);
    });
    renderWithProviders(<App />, { route: '/app/preferences' });

    await userEvent.type(
      await screen.findByLabelText('Añadir puestos que buscas'),
      'Backend Developer{Enter}',
    );
    await userEvent.selectOptions(screen.getByLabelText('Modalidad'), 'remote');
    await userEvent.click(screen.getByRole('checkbox', { name: 'Adzuna' }));
    await userEvent.click(screen.getByRole('button', { name: 'Guardar preferencias' }));

    expect(await screen.findByText('Preferencias guardadas.')).toBeVisible();
    expect(saved).toEqual({
      roles: ['Backend Developer'],
      locations: [],
      remote: 'remote',
      min_salary: null,
      sources: ['adzuna'],
    });
  });
});
