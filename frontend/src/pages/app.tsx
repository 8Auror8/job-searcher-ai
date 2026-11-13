import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useCurrentUser, useLogout } from '../auth/hooks';

const NAV = [
  { to: '/app', label: 'Inicio', end: true },
  { to: '/app/jobs', label: 'Ofertas', soon: 'Sprint 3' },
  { to: '/app/cvs', label: 'Mis CVs' },
  { to: '/app/preferences', label: 'Preferencias' },
  { to: '/app/applications', label: 'Candidaturas', soon: 'Sprint 4' },
  { to: '/app/alerts', label: 'Alertas', soon: 'Sprint 5' },
  { to: '/app/stats', label: 'Estadísticas', soon: 'Sprint 5' },
];

export function AppLayout() {
  const { data: user } = useCurrentUser();
  const logout = useLogout();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen md:flex">
      <aside className="border-b border-slate-200 bg-white md:w-60 md:border-b-0 md:border-r">
        <div className="flex items-center justify-between p-4 md:block">
          <Link to="/app" className="text-lg font-bold text-brand-700">
            JobPilot AI
          </Link>
        </div>
        <nav aria-label="Principal" className="flex gap-1 overflow-x-auto px-2 pb-2 md:flex-col">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center justify-between whitespace-nowrap rounded-lg px-3 py-2 text-sm ${
                  isActive
                    ? 'bg-brand-50 font-semibold text-brand-700'
                    : 'text-slate-700 hover:bg-slate-100'
                }`
              }
            >
              {item.label}
              {item.soon && <span className="ml-2 text-[10px] text-slate-400">{item.soon}</span>}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="flex-1">
        <header className="flex items-center justify-end gap-3 border-b border-slate-200 bg-white px-6 py-3 text-sm">
          <span className="text-slate-600">{user?.email}</span>
          <button
            type="button"
            className="rounded-lg border border-slate-300 px-3 py-1.5 hover:bg-slate-50"
            onClick={() => logout.mutate(undefined, { onSettled: () => navigate('/login') })}
          >
            Cerrar sesión
          </button>
        </header>
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { data: user } = useCurrentUser();
  return (
    <section className="max-w-3xl space-y-4">
      <h1 className="text-2xl font-semibold">Hola, {user?.email}</h1>
      <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="font-semibold">Primeros pasos</h2>
        <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm text-slate-700">
          <li>
            <Link className="text-brand-600 underline" to="/app/cvs">
              Sube tu CV o el PDF de tu perfil de LinkedIn
            </Link>
            .
          </li>
          <li>
            <Link className="text-brand-600 underline" to="/app/preferences">
              Indica qué tipo de puesto buscas
            </Link>
            .
          </li>
          <li>Revisa las ofertas que mejor encajan contigo.</li>
          <li>Prepara tu candidatura con IA y envíala en la web de la oferta.</li>
        </ol>
      </div>
    </section>
  );
}

export function ComingSoonPage({ title }: { title: string }) {
  return (
    <section className="space-y-2">
      <h1 className="text-2xl font-semibold">{title}</h1>
      <p className="text-slate-600">Esta sección estará disponible en próximos sprints.</p>
    </section>
  );
}
