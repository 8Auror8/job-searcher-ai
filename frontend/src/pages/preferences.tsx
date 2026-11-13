import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { cvApi, JOB_SOURCES, type Preferences } from '../api/cvs';
import { Alert, Button, TextField } from '../components/ui';
import { errorMessage } from '../lib/errors';
import { TagInput } from './cvEditor';

const PREFS_KEY = ['preferences'] as const;

const REMOTE_OPTIONS: { value: Preferences['remote']; label: string }[] = [
  { value: 'any', label: 'Me da igual' },
  { value: 'remote', label: 'Solo remoto' },
  { value: 'hybrid', label: 'Híbrido' },
  { value: 'onsite', label: 'Presencial' },
];

export function PreferencesPage() {
  const qc = useQueryClient();
  const query = useQuery({ queryKey: PREFS_KEY, queryFn: cvApi.getPreferences });
  const [prefs, setPrefs] = useState<Preferences | null>(null);
  useEffect(() => {
    if (query.data) setPrefs(query.data);
  }, [query.data]);

  const save = useMutation({
    mutationFn: (data: Preferences) => cvApi.savePreferences(data),
    onSuccess: (data) => qc.setQueryData(PREFS_KEY, data),
  });

  if (query.isError) return <Alert kind="error">{errorMessage(query.error)}</Alert>;
  if (!prefs) return <p className="text-slate-500">Cargando…</p>;

  const toggleSource = (id: string) =>
    setPrefs({
      ...prefs,
      sources: prefs.sources.includes(id)
        ? prefs.sources.filter((s) => s !== id)
        : [...prefs.sources, id],
    });

  return (
    <section className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Preferencias de búsqueda</h1>
        <p className="text-sm text-slate-600">
          Las usaremos para buscar ofertas (Sprint 3) y en tus alertas.
        </p>
      </div>
      <form
        className="space-y-6 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200"
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate(prefs);
        }}
      >
        <TagInput
          label="Puestos que buscas"
          values={prefs.roles}
          onChange={(roles) => setPrefs({ ...prefs, roles })}
          placeholder="Ej.: Backend Developer"
        />
        <TagInput
          label="Ubicaciones"
          values={prefs.locations}
          onChange={(locations) => setPrefs({ ...prefs, locations })}
          placeholder="Ej.: Madrid"
        />
        <label className="block space-y-1">
          <span className="block text-sm font-medium text-slate-700">Modalidad</span>
          <select
            className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={prefs.remote}
            onChange={(e) =>
              setPrefs({ ...prefs, remote: e.target.value as Preferences['remote'] })
            }
          >
            {REMOTE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
        <TextField
          label="Salario mínimo anual (€)"
          type="number"
          min={0}
          step={1000}
          value={prefs.min_salary ?? ''}
          onChange={(e) =>
            setPrefs({
              ...prefs,
              min_salary: e.target.value === '' ? null : Number(e.target.value),
            })
          }
        />
        <fieldset className="space-y-2">
          <legend className="text-sm font-medium text-slate-700">
            Fuentes de ofertas (vacío = todas)
          </legend>
          <div className="grid gap-2 sm:grid-cols-2">
            {JOB_SOURCES.map((source) => (
              <label key={source.id} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={prefs.sources.includes(source.id)}
                  onChange={() => toggleSource(source.id)}
                />
                {source.label}
              </label>
            ))}
          </div>
        </fieldset>
        {save.isError && <Alert kind="error">{errorMessage(save.error)}</Alert>}
        {save.isSuccess && <Alert kind="success">Preferencias guardadas.</Alert>}
        <Button type="submit" className="sm:w-auto" loading={save.isPending}>
          Guardar preferencias
        </Button>
      </form>
    </section>
  );
}
