import { Link } from 'react-router-dom';

export function LandingPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col justify-center gap-8 px-6 py-16">
      <p className="text-sm font-semibold uppercase tracking-wide text-brand-600">JobPilot AI</p>
      <h1 className="text-4xl font-bold leading-tight sm:text-5xl">
        Sube tu CV. La IA encuentra las ofertas que encajan contigo.
      </h1>
      <p className="max-w-2xl text-lg text-slate-600">
        Buscamos en varias fuentes de empleo, puntuamos cada oferta según tu perfil, te explicamos
        por qué encaja y te dejamos la candidatura preparada. Tú decides y la envías.
      </p>
      <div className="flex flex-wrap gap-3">
        <Link
          to="/register"
          className="rounded-lg bg-brand-600 px-5 py-3 font-semibold text-white hover:bg-brand-700"
        >
          Crear cuenta gratis
        </Link>
        <Link
          to="/login"
          className="rounded-lg border border-slate-300 bg-white px-5 py-3 font-semibold hover:bg-slate-50"
        >
          Iniciar sesión
        </Link>
      </div>
    </main>
  );
}

export function PrivacyPage() {
  return (
    <main className="mx-auto max-w-3xl space-y-4 px-6 py-12">
      <h1 className="text-3xl font-bold">Política de privacidad</h1>
      <p className="text-slate-700">
        Borrador. La política completa se publicará en el Sprint 6 (ver <code>docs/legal.md</code>).
        Resumen: solo tratamos tu CV con tu consentimiento para buscar ofertas y preparar
        candidaturas, nunca enviamos candidaturas en tu nombre y puedes exportar o borrar tus datos
        cuando quieras.
      </p>
      <Link className="text-brand-600 underline" to="/">
        Volver
      </Link>
    </main>
  );
}

export function NotFoundPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-semibold">Página no encontrada</h1>
      <Link className="text-brand-600 underline" to="/">
        Ir al inicio
      </Link>
    </main>
  );
}
