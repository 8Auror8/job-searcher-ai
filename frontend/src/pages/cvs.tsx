import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRef, useState, type DragEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { cvApi, ORIGIN_LABELS, type CvSummary } from '../api/cvs';
import { Alert, Button } from '../components/ui';
import { errorMessage } from '../lib/errors';

export const CVS_KEY = ['cvs'] as const;

type Mode = 'upload' | 'linkedin_pdf';

const STATUS: Record<CvSummary['extraction_status'], { label: string; className: string }> = {
  ok: { label: 'Analizado con IA', className: 'bg-green-50 text-green-700' },
  manual: { label: 'Manual', className: 'bg-slate-100 text-slate-700' },
  failed: { label: 'Análisis pendiente', className: 'bg-amber-50 text-amber-800' },
};

function UploadPanel({ mode, onClose }: { mode: Mode; onClose: () => void }) {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [consent, setConsent] = useState(false);
  const [dragging, setDragging] = useState(false);

  const upload = useMutation({
    mutationFn: () => cvApi.upload(file!, { origin: mode, consent }),
    onSuccess: (cv) => {
      qc.invalidateQueries({ queryKey: CVS_KEY });
      navigate(`/app/cvs/${cv.id}`);
    },
  });

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  };

  return (
    <section
      aria-label={mode === 'linkedin_pdf' ? 'Importar desde LinkedIn' : 'Subir CV'}
      className="space-y-4 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200"
    >
      <h2 className="text-lg font-semibold">
        {mode === 'linkedin_pdf' ? 'Importar tu perfil de LinkedIn' : 'Subir un CV'}
      </h2>
      {mode === 'linkedin_pdf' && (
        <ol className="list-decimal space-y-1 pl-5 text-sm text-slate-700">
          <li>Abre tu perfil en LinkedIn.</li>
          <li>
            Pulsa <strong>Más</strong> → <strong>Guardar en PDF</strong> (o “Recursos” → “Guardar en
            PDF”).
          </li>
          <li>
            Sube aquí ese archivo. JobPilot no se conecta a LinkedIn: solo lee el PDF que subes.
          </li>
        </ol>
      )}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`flex flex-col items-center gap-2 rounded-xl border-2 border-dashed p-6 text-center text-sm ${
          dragging ? 'border-brand-500 bg-brand-50' : 'border-slate-300'
        }`}
      >
        <p>
          {file ? <strong>{file.name}</strong> : 'Arrastra aquí tu archivo PDF o Word (máx. 5 MB)'}
        </p>
        <button
          type="button"
          className="font-semibold text-brand-600 underline"
          onClick={() => input.current?.click()}
        >
          {file ? 'Elegir otro archivo' : 'O selecciónalo en tu ordenador'}
        </button>
        <input
          ref={input}
          type="file"
          aria-label="Archivo del CV"
          className="sr-only"
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
      </div>
      <label className="flex items-start gap-2 text-sm text-slate-700">
        <input
          type="checkbox"
          className="mt-0.5"
          checked={consent}
          onChange={(e) => setConsent(e.target.checked)}
        />
        <span>
          Doy mi consentimiento para que JobPilot analice mi CV con IA (Anthropic) y lo use para
          buscar ofertas. No guardamos el archivo original, solo su texto y el perfil.{' '}
          <Link className="text-brand-600 underline" to="/privacy" target="_blank">
            Más información
          </Link>
        </span>
      </label>
      {upload.isError && <Alert kind="error">{errorMessage(upload.error)}</Alert>}
      {upload.isPending && (
        <Alert kind="info">
          Leyendo tu CV y extrayendo el perfil con IA… puede tardar unos segundos.
        </Alert>
      )}
      <div className="flex gap-3">
        <Button
          className="sm:w-auto"
          loading={upload.isPending}
          disabled={!file}
          onClick={() => upload.mutate()}
        >
          Analizar CV
        </Button>
        <Button className="sm:w-auto" variant="secondary" onClick={onClose}>
          Cancelar
        </Button>
      </div>
    </section>
  );
}

function CvCard({ cv }: { cv: CvSummary }) {
  const qc = useQueryClient();
  const refresh = () => qc.invalidateQueries({ queryKey: CVS_KEY });
  const patch = useMutation({
    mutationFn: (data: Parameters<typeof cvApi.patch>[1]) => cvApi.patch(cv.id, data),
    onSuccess: refresh,
  });
  const remove = useMutation({ mutationFn: () => cvApi.remove(cv.id), onSuccess: refresh });
  const status = STATUS[cv.extraction_status];

  return (
    <li className="flex flex-col gap-3 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 sm:flex-row sm:items-center sm:justify-between">
      <div className="space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <Link to={`/app/cvs/${cv.id}`} className="font-semibold text-slate-900 hover:underline">
            {cv.name}
          </Link>
          {cv.is_primary && (
            <span className="rounded-full bg-brand-50 px-2 py-0.5 text-xs font-semibold text-brand-700">
              Principal
            </span>
          )}
          {cv.archived && (
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
              Archivado
            </span>
          )}
          <span className={`rounded-full px-2 py-0.5 text-xs ${status.className}`}>
            {status.label}
          </span>
        </div>
        <p className="text-xs text-slate-500">
          {ORIGIN_LABELS[cv.origin]} · actualizado{' '}
          {new Date(cv.updated_at).toLocaleDateString('es-ES')}
        </p>
        {(patch.isError || remove.isError) && (
          <p className="text-sm text-red-600">{errorMessage(patch.error ?? remove.error)}</p>
        )}
      </div>
      <div className="flex flex-wrap gap-2 text-sm">
        <Link
          to={`/app/cvs/${cv.id}`}
          className="rounded-lg border border-slate-300 px-3 py-1.5 hover:bg-slate-50"
        >
          Editar perfil
        </Link>
        {!cv.is_primary && !cv.archived && (
          <button
            type="button"
            className="rounded-lg border border-slate-300 px-3 py-1.5 hover:bg-slate-50"
            onClick={() => patch.mutate({ is_primary: true })}
          >
            Marcar como principal
          </button>
        )}
        <button
          type="button"
          className="rounded-lg border border-slate-300 px-3 py-1.5 hover:bg-slate-50"
          onClick={() => patch.mutate({ archived: !cv.archived })}
        >
          {cv.archived ? 'Restaurar' : 'Archivar'}
        </button>
        <button
          type="button"
          className="rounded-lg border border-red-200 px-3 py-1.5 text-red-700 hover:bg-red-50"
          onClick={() => {
            if (window.confirm(`¿Eliminar "${cv.name}"? Esta acción no se puede deshacer.`))
              remove.mutate();
          }}
        >
          Eliminar
        </button>
      </div>
    </li>
  );
}

export function CvsPage() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode | null>(null);
  const [showArchived, setShowArchived] = useState(false);
  const cvs = useQuery({
    queryKey: [...CVS_KEY, { showArchived }],
    queryFn: () => cvApi.list(showArchived),
  });
  const blank = useMutation({
    mutationFn: () => cvApi.createBlank('CV sin título'),
    onSuccess: (cv) => {
      qc.invalidateQueries({ queryKey: CVS_KEY });
      navigate(`/app/cvs/${cv.id}`);
    },
  });

  return (
    <section className="max-w-4xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Mis CVs</h1>
          <p className="text-sm text-slate-600">
            Puedes tener varias versiones (por ejemplo, una por tipo de puesto). La principal se usa
            por defecto para buscar ofertas.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-sm">
          <button
            type="button"
            className="rounded-lg bg-brand-600 px-3 py-2 font-semibold text-white hover:bg-brand-700"
            onClick={() => setMode('upload')}
          >
            Subir CV
          </button>
          <button
            type="button"
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 font-semibold hover:bg-slate-50"
            onClick={() => setMode('linkedin_pdf')}
          >
            Importar de LinkedIn
          </button>
          <button
            type="button"
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 hover:bg-slate-50"
            onClick={() => blank.mutate()}
          >
            Crear desde cero
          </button>
        </div>
      </div>

      {blank.isError && <Alert kind="error">{errorMessage(blank.error)}</Alert>}
      {mode && <UploadPanel key={mode} mode={mode} onClose={() => setMode(null)} />}

      {cvs.isLoading && <p className="text-slate-500">Cargando…</p>}
      {cvs.isError && <Alert kind="error">{errorMessage(cvs.error)}</Alert>}
      {cvs.data && cvs.data.length === 0 && !mode && (
        <div className="rounded-2xl border border-dashed border-slate-300 p-8 text-center text-slate-600">
          Aún no tienes ningún CV. Sube uno o importa tu perfil de LinkedIn para empezar.
        </div>
      )}
      {cvs.data && cvs.data.length > 0 && (
        <ul className="space-y-3">
          {cvs.data.map((cv) => (
            <CvCard key={cv.id} cv={cv} />
          ))}
        </ul>
      )}
      <label className="flex items-center gap-2 text-sm text-slate-600">
        <input
          type="checkbox"
          checked={showArchived}
          onChange={(e) => setShowArchived(e.target.checked)}
        />
        Mostrar archivados
      </label>
    </section>
  );
}
