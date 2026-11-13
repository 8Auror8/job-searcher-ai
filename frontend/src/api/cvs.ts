import { api, json } from './client';

export interface Language {
  name: string;
  level: string | null;
}

export interface Experience {
  title: string;
  company: string | null;
  location: string | null;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  description: string | null;
}

export interface Education {
  degree: string;
  institution: string | null;
  start_date: string | null;
  end_date: string | null;
}

export interface CvProfile {
  full_name: string | null;
  headline: string | null;
  summary: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  links: string[];
  total_years_experience: number | null;
  skills: string[];
  languages: Language[];
  experience: Experience[];
  education: Education[];
  certifications: string[];
}

export type CvOrigin = 'upload' | 'linkedin_pdf' | 'manual' | 'tailored';
export type ExtractionStatus = 'ok' | 'manual' | 'failed';

export interface CvSummary {
  id: string;
  name: string;
  origin: CvOrigin;
  is_primary: boolean;
  archived: boolean;
  extraction_status: ExtractionStatus;
  created_at: string;
  updated_at: string;
}

export interface CvDetail extends CvSummary {
  profile: CvProfile;
  extraction_notes: {
    reason?: string;
    model?: string;
    prompt_version?: string;
    unverified?: { field: string; value: string }[];
    edited_by_user?: boolean;
  };
  has_source_text: boolean;
}

export interface Preferences {
  roles: string[];
  locations: string[];
  remote: 'any' | 'remote' | 'hybrid' | 'onsite';
  min_salary: number | null;
  sources: string[];
}

export const cvApi = {
  list: (includeArchived = false) =>
    api<CvSummary[]>(`/cvs${includeArchived ? '?include_archived=true' : ''}`),
  get: (id: string) => api<CvDetail>(`/cvs/${id}`),
  upload: (
    file: File,
    opts: { origin: 'upload' | 'linkedin_pdf'; consent: boolean; name?: string },
  ) => {
    const form = new FormData();
    form.append('file', file);
    form.append('origin', opts.origin);
    form.append('consent', String(opts.consent));
    if (opts.name) form.append('name', opts.name);
    return api<CvDetail>('/cvs', { method: 'POST', body: form });
  },
  createBlank: (name: string) => api<CvDetail>('/cvs/blank', { method: 'POST', ...json({ name }) }),
  patch: (id: string, data: { name?: string; is_primary?: true; archived?: boolean }) =>
    api<CvDetail>(`/cvs/${id}`, { method: 'PATCH', ...json(data) }),
  saveProfile: (id: string, profile: CvProfile) =>
    api<CvDetail>(`/cvs/${id}/profile`, { method: 'PUT', ...json(profile) }),
  reextract: (id: string) => api<CvDetail>(`/cvs/${id}/extract`, { method: 'POST' }),
  remove: (id: string) => api<void>(`/cvs/${id}`, { method: 'DELETE' }),
  getPreferences: () => api<Preferences>('/preferences'),
  savePreferences: (prefs: Preferences) =>
    api<Preferences>('/preferences', { method: 'PUT', ...json(prefs) }),
};

export const ORIGIN_LABELS: Record<CvOrigin, string> = {
  upload: 'Archivo subido',
  linkedin_pdf: 'LinkedIn',
  manual: 'Creado a mano',
  tailored: 'Adaptado a una oferta',
};

export const JOB_SOURCES = [
  { id: 'adzuna', label: 'Adzuna' },
  { id: 'arbeitnow', label: 'Arbeitnow' },
  { id: 'jobicy', label: 'Jobicy' },
  { id: 'himalayas', label: 'Himalayas' },
  { id: 'remoteok', label: 'Remote OK' },
  { id: 'greenhouse', label: 'Greenhouse (empresas)' },
  { id: 'lever', label: 'Lever (empresas)' },
] as const;
