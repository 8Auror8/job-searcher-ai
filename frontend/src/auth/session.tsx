import type { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useCurrentUser } from './hooks';

function FullPageSpinner() {
  return (
    <div className="flex min-h-screen items-center justify-center" role="status">
      <span className="text-slate-500">Cargando…</span>
    </div>
  );
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { data: user, isLoading } = useCurrentUser();
  const location = useLocation();
  if (isLoading) return <FullPageSpinner />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <>{children}</>;
}

export function RedirectIfAuthenticated({ children }: { children: ReactNode }) {
  const { data: user, isLoading } = useCurrentUser();
  if (isLoading) return <FullPageSpinner />;
  if (user) return <Navigate to="/app" replace />;
  return <>{children}</>;
}
