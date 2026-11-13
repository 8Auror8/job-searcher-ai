import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState, type ReactNode } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  cvApi,
  ORIGIN_LABELS,
  type CvDetail,
  type CvProfile,
  type Education,
  type Experience,
} from '../api/cvs';
import { Alert, Button, TextField } from '../components/ui';
import { errorMessage, messageForCode } from '../lib/errors';
import { CVS_KEY } from './cvs';

const FIELD_LABELS: Record<string, string> = {
  skills: 'Habilidad',
  certifications: 'Certificación',
  'experience.company': 'Empresa',
  'education.institution': 'Centro de estudios',
};

const emptyExperience: Experience = {
  title: '',
  company: null,
  location: null,
  start_date: null,
  end_date: null,
  is_current: false,
  description: null,
};
const emptyEducation: Education = {
  degree: '',
  institution: null,
  start_date: null,
  end_date: null,
};

const orNull = (value: string) => (value.trim() === '' ? null : value);

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="space-y-4 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <h2 className="text-lg font-semibold">{title}</h2>
      {children}
    </section>
  );
}

export function TagInput({
  label,
  values,
  onChange,
  placeholder,
}: {
  label: string;
  values: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
}) {
  const [draft, setDraft] = useState('');
  const add = () => {
    const value = draft.trim();
    if (value && !values.some((v) => v.toLowerCase() === value.toLowerCase())) {
      onChange([...values, value]);
    }
    setDraft('');
  };
  return (
    <div className="space-y-2">
      <span className="block text-sm font-medium text-slate-700">{label}</span>
      <ul className="flex flex-wrap gap-2" aria-label={label}>
        {values.map((value) => (
          <li
            key={value}
            className="flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-800"
          >
            {value}
            <button
              type="button"
              aria-label={`Quitar ${value}`}
              className="text-slate-500 hover:text-red-600"
              onClick={() => onChange(values.filter((v) => v !== value))}
            >
              ×
            </button>
          </li>
        ))}
      </ul>
      <div className="flex gap-2">
        <input
          aria-label={`Añadir ${label.toLowerCase()}`}
          className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={draft}
          placeholder={placeholder}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              add();
            }
          }}
        />
        <button
          type="button"
          className="rounded-lg border border-slate-300 px-3 text-sm hover:bg-slate-50"
          onClick={add}
        >
          Añadir
        </button>
      </div>
    </div>
  );
}

function ProfileForm({ cv }: { cv: CvDetail }) {
  const qc = useQueryClient();
  const [profile, setProfile] = useState<CvProfile>(cv.profile);
  const [dirty, setDirty] = useState(false);
  useEffect(() => {
    setProfile(cv.profile);
    setDirty(false);
  }, [cv]);

  const update = (patch: Partial<CvProfile>) => {
    setProfile((p) => ({ ...p, ...patch }));
    setDirty(true);
  };
  const updateItem = <K extends 'experience' | 'education' | 'languages'>(
    key: K,
    index: number,
    patch: Partial<CvProfile[K][number]>,
  ) =>
    update({ [key]: profile[key].map((item, i) => (i === index ? { ...item, ...patch } : item)) });
  const removeItem = (key: 'experience' | 'education' | 'languages', index: number) =>
    update({ [key]: profile[key].filter((_, i) => i !== index) });

  const onSaved = (saved: CvDetail) => {
    qc.setQueryData([...CVS_KEY, saved.id], saved);
    qc.invalidateQueries({ queryKey: CVS_KEY, exact: false });
  };
  const save = useMutation({
    mutationFn: () => cvApi.saveProfile(cv.id, profile),
    onSuccess: onSaved,
  });
  const reextract = useMutation({ mutationFn: () => cvApi.reextract(cv.id), onSuccess: onSaved });

  const unverified = cv.extraction_notes.unverified ?? [];

  return (
    <form
      className="space-y-6"
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate();
      }}
    >
      {cv.extraction_status === 'ok' && (
        <Alert kind="info">
          La IA ha rellenado este perfil a partir de tu documento. Revísalo: tú decides qué es
          correcto.
        </Alert>
      )}
      {cv.extraction_status === 'manual' && cv.has_source_text && (
        <Alert kind="info">
          El análisis con IA no está activado en este servidor. Rellena el perfil a mano.
        </Alert>
      )}
      {cv.extraction_status === 'failed' && (
        <Alert kind="error">
          No se pudo analizar el CV con IA
          {cv.extraction_notes.reason ? `: ${messageForCode(cv.extraction_notes.reason)}` : '.'}
          Puedes reintentarlo o rellenar el perfil a mano.
        </Alert>
      )}
      {unverified.length > 0 && (
        <Alert kind="info">
          <p className="font-semibold">
            Datos que la IA propuso pero no aparecen tal cual en tu CV
          </p>
          <p className="mt-1">
            Para no inventar nada, no los hemos añadido. Si son correctos, añádelos tú:
          </p>
          <ul className="mt-2 list-disc pl-5">
            {unverified.map((item) => (
              <li key={`${item.field}-${item.value}`}>
                {FIELD_LABELS[item.field] ?? item.field}: <strong>{item.value}</strong>
              </li>
            ))}
          </ul>
        </Alert>
      )}

      <Card title="Datos básicos">
        <div className="grid gap-4 sm:grid-cols-2">
          <TextField
            label="Nombre completo"
            value={profile.full_name ?? ''}
            onChange={(e) => update({ full_name: orNull(e.target.value) })}
          />
          <TextField
            label="Titular"
            placeholder="Ej.: Backend Developer"
            value={profile.headline ?? ''}
            onChange={(e) => update({ headline: orNull(e.target.value) })}
          />
          <TextField
            label="Email de contacto"
            type="email"
            value={profile.email ?? ''}
            onChange={(e) => update({ email: orNull(e.target.value) })}
          />
          <TextField
            label="Teléfono"
            value={profile.phone ?? ''}
            onChange={(e) => update({ phone: orNull(e.target.value) })}
          />
          <TextField
            label="Ubicación"
            value={profile.location ?? ''}
            onChange={(e) => update({ location: orNull(e.target.value) })}
          />
          <TextField
            label="Años de experiencia"
            type="number"
            min={0}
            max={70}
            step={0.5}
            value={profile.total_years_experience ?? ''}
            onChange={(e) =>
              update({
                total_years_experience: e.target.value === '' ? null : Number(e.target.value),
              })
            }
          />
        </div>
        <label className="block space-y-1">
          <span className="block text-sm font-medium text-slate-700">Resumen</span>
          <textarea
            rows={4}
            className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={profile.summary ?? ''}
            onChange={(e) => update({ summary: orNull(e.target.value) })}
          />
        </label>
        <TagInput
          label="Enlaces"
          values={profile.links}
          onChange={(links) => update({ links })}
          placeholder="https://github.com/…"
        />
      </Card>

      <Card title="Habilidades">
        <TagInput
          label="Habilidades"
          values={profile.skills}
          onChange={(skills) => update({ skills })}
          placeholder="Ej.: Python"
        />
        <TagInput
          label="Certificaciones"
          values={profile.certifications}
          onChange={(certifications) => update({ certifications })}
        />
      </Card>

      <Card title="Experiencia">
        {profile.experience.map((exp, i) => (
          <fieldset key={i} className="space-y-3 rounded-xl border border-slate-200 p-4">
            <legend className="px-1 text-sm font-semibold">Puesto {i + 1}</legend>
            <div className="grid gap-3 sm:grid-cols-2">
              <TextField
                label="Puesto"
                value={exp.title}
                onChange={(e) => updateItem('experience', i, { title: e.target.value })}
              />
              <TextField
                label="Empresa"
                value={exp.company ?? ''}
                onChange={(e) => updateItem('experience', i, { company: orNull(e.target.value) })}
              />
              <TextField
                label="Inicio (AAAA-MM)"
                value={exp.start_date ?? ''}
                onChange={(e) =>
                  updateItem('experience', i, { start_date: orNull(e.target.value) })
                }
              />
              <TextField
                label="Fin (AAAA-MM)"
                value={exp.end_date ?? ''}
                disabled={exp.is_current}
                onChange={(e) => updateItem('experience', i, { end_date: orNull(e.target.value) })}
              />
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={exp.is_current}
                onChange={(e) =>
                  updateItem('experience', i, { is_current: e.target.checked, end_date: null })
                }
              />
              Es mi puesto actual
            </label>
            <label className="block space-y-1">
              <span className="block text-sm font-medium text-slate-700">Descripción</span>
              <textarea
                rows={3}
                className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={exp.description ?? ''}
                onChange={(e) =>
                  updateItem('experience', i, { description: orNull(e.target.value) })
                }
              />
            </label>
            <button
              type="button"
              className="text-sm text-red-700 underline"
              onClick={() => removeItem('experience', i)}
            >
              Quitar puesto
            </button>
          </fieldset>
        ))}
        <button
          type="button"
          className="text-sm font-semibold text-brand-600"
          onClick={() => update({ experience: [...profile.experience, { ...emptyExperience }] })}
        >
          + Añadir puesto
        </button>
      </Card>

      <Card title="Formación">
        {profile.education.map((edu, i) => (
          <fieldset
            key={i}
            className="grid gap-3 rounded-xl border border-slate-200 p-4 sm:grid-cols-2"
          >
            <legend className="px-1 text-sm font-semibold">Estudio {i + 1}</legend>
            <TextField
              label="Titulación"
              value={edu.degree}
              onChange={(e) => updateItem('education', i, { degree: e.target.value })}
            />
            <TextField
              label="Centro"
              value={edu.institution ?? ''}
              onChange={(e) => updateItem('education', i, { institution: orNull(e.target.value) })}
            />
            <TextField
              label="Inicio"
              value={edu.start_date ?? ''}
              onChange={(e) => updateItem('education', i, { start_date: orNull(e.target.value) })}
            />
            <TextField
              label="Fin"
              value={edu.end_date ?? ''}
              onChange={(e) => updateItem('education', i, { end_date: orNull(e.target.value) })}
            />
            <button
              type="button"
              className="text-left text-sm text-red-700 underline"
              onClick={() => removeItem('education', i)}
            >
              Quitar estudio
            </button>
          </fieldset>
        ))}
        <button
          type="button"
          className="text-sm font-semibold text-brand-600"
          onClick={() => update({ education: [...profile.education, { ...emptyEducation }] })}
        >
          + Añadir estudio
        </button>
      </Card>

      <Card title="Idiomas">
        {profile.languages.map((lang, i) => (
          <div key={i} className="flex flex-wrap items-end gap-3">
            <div className="flex-1">
              <TextField
                label="Idioma"
                value={lang.name}
                onChange={(e) => updateItem('languages', i, { name: e.target.value })}
              />
            </div>
            <div className="flex-1">
              <TextField
                label="Nivel"
                value={lang.level ?? ''}
                onChange={(e) => updateItem('languages', i, { level: orNull(e.target.value) })}
              />
            </div>
            <button
              type="button"
              className="pb-2 text-sm text-red-700 underline"
              onClick={() => removeItem('languages', i)}
            >
              Quitar
            </button>
          </div>
        ))}
        <button
          type="button"
          className="text-sm font-semibold text-brand-600"
          onClick={() => update({ languages: [...profile.languages, { name: '', level: null }] })}
        >
          + Añadir idioma
        </button>
      </Card>

      <div className="sticky bottom-0 flex flex-wrap items-center gap-3 border-t border-slate-200 bg-slate-50/95 py-4">
        <Button type="submit" className="sm:w-auto" loading={save.isPending} disabled={!dirty}>
          Guardar perfil
        </Button>
        {cv.has_source_text && cv.extraction_notes.reason !== 'ai_disabled' && (
          <Button
            type="button"
            variant="secondary"
            className="sm:w-auto"
            loading={reextract.isPending}
            onClick={() => {
              if (!dirty || window.confirm('Se perderán los cambios sin guardar. ¿Continuar?')) {
                reextract.mutate();
              }
            }}
          >
            Volver a analizar con IA
          </Button>
        )}
        {save.isSuccess && !dirty && <span className="text-sm text-green-700">Guardado ✓</span>}
        {dirty && <span className="text-sm text-slate-500">Cambios sin guardar</span>}
      </div>
      {save.isError && <Alert kind="error">{errorMessage(save.error)}</Alert>}
      {reextract.isError && <Alert kind="error">{errorMessage(reextract.error)}</Alert>}
    </form>
  );
}

export function CvEditorPage() {
  const { id = '' } = useParams();
  const cv = useQuery({ queryKey: [...CVS_KEY, id], queryFn: () => cvApi.get(id) });

  return (
    <section className="max-w-4xl space-y-6">
      <Link to="/app/cvs" className="text-sm text-brand-600">
        ← Volver a mis CVs
      </Link>
      {cv.isLoading && <p className="text-slate-500">Cargando…</p>}
      {cv.isError && <Alert kind="error">{errorMessage(cv.error)}</Alert>}
      {cv.data && (
        <>
          <div>
            <h1 className="text-2xl font-semibold">{cv.data.name}</h1>
            <p className="text-sm text-slate-600">
              {ORIGIN_LABELS[cv.data.origin]}
              {cv.data.is_primary ? ' · CV principal' : ''}
            </p>
          </div>
          <ProfileForm cv={cv.data} />
        </>
      )}
    </section>
  );
}
