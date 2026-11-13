import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { authApi } from '../api/auth';
import { ApiError } from '../api/client';
import { ME_KEY } from '../auth/hooks';
import { Alert, AuthLayout, Button, Divider, GoogleButton, TextField } from '../components/ui';
import { errorMessage, PASSWORD_MIN, passwordStrength } from '../lib/errors';

const STRENGTH_LABELS = ['Demasiado corta', 'Débil', 'Aceptable', 'Fuerte'] as const;

function PasswordHint({ password }: { password: string }) {
  const level = passwordStrength(password);
  return (
    <div className="space-y-1" aria-live="polite">
      <div className="flex gap-1" aria-hidden>
        {[1, 2, 3].map((i) => (
          <span
            key={i}
            className={`h-1 flex-1 rounded ${level >= i ? 'bg-brand-500' : 'bg-slate-200'}`}
          />
        ))}
      </div>
      <span>
        {STRENGTH_LABELS[level]} · mínimo {PASSWORD_MIN} caracteres
      </span>
    </div>
  );
}

export function LoginPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();
  const qc = useQueryClient();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const from = (location.state as { from?: string } | null)?.from ?? '/app';

  const login = useMutation({
    mutationFn: () => authApi.login(email, password),
    onSuccess: (user) => {
      qc.setQueryData(ME_KEY, user);
      navigate(from, { replace: true });
    },
  });
  const resend = useMutation({ mutationFn: () => authApi.resendVerification(email) });
  const notVerified = login.error instanceof ApiError && login.error.code === 'email_not_verified';

  const submit = (e: FormEvent) => {
    e.preventDefault();
    login.mutate();
  };

  return (
    <AuthLayout
      title="Inicia sesión"
      footer={
        <>
          ¿No tienes cuenta?{' '}
          <Link className="font-semibold text-brand-600" to="/register">
            Regístrate
          </Link>
        </>
      }
    >
      {params.get('error') === 'google' && (
        <Alert kind="error">No se ha podido iniciar sesión con Google. Inténtalo de nuevo.</Alert>
      )}
      {login.isError && <Alert kind="error">{errorMessage(login.error)}</Alert>}
      {notVerified && (
        <div className="text-sm">
          {resend.isSuccess ? (
            <Alert kind="success">Te hemos enviado un nuevo enlace de confirmación.</Alert>
          ) : (
            <button
              type="button"
              className="font-semibold text-brand-600 underline"
              onClick={() => resend.mutate()}
            >
              Reenviar email de confirmación
            </button>
          )}
        </div>
      )}
      <form className="space-y-4" onSubmit={submit} noValidate>
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <TextField
          label="Contraseña"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <div className="text-right text-sm">
          <Link className="text-brand-600" to="/forgot-password">
            ¿Olvidaste tu contraseña?
          </Link>
        </div>
        <Button type="submit" loading={login.isPending} disabled={!email || !password}>
          Iniciar sesión
        </Button>
      </form>
      <Divider label="o" />
      <GoogleButton href={authApi.googleLoginUrl} />
    </AuthLayout>
  );
}

export function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [accept, setAccept] = useState(false);
  const register = useMutation({ mutationFn: () => authApi.register(email, password, accept) });
  const tooShort = password.length > 0 && password.length < PASSWORD_MIN;

  if (register.isSuccess) {
    return (
      <AuthLayout title="Revisa tu email">
        <Alert kind="success">
          Si los datos son correctos, recibirás en <strong>{email}</strong> un enlace para confirmar
          tu cuenta. Caduca en 24 horas.
        </Alert>
        <Link className="block text-center text-sm font-semibold text-brand-600" to="/login">
          Ir a iniciar sesión
        </Link>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Crea tu cuenta"
      subtitle="Encuentra ofertas que encajan contigo y prepara tus candidaturas con IA."
      footer={
        <>
          ¿Ya tienes cuenta?{' '}
          <Link className="font-semibold text-brand-600" to="/login">
            Inicia sesión
          </Link>
        </>
      }
    >
      {register.isError && <Alert kind="error">{errorMessage(register.error)}</Alert>}
      <form
        className="space-y-4"
        noValidate
        onSubmit={(e) => {
          e.preventDefault();
          register.mutate();
        }}
      >
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <TextField
          label="Contraseña"
          type="password"
          autoComplete="new-password"
          required
          minLength={PASSWORD_MIN}
          maxLength={128}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={tooShort ? `Debe tener al menos ${PASSWORD_MIN} caracteres.` : undefined}
          hint={<PasswordHint password={password} />}
        />
        <label className="flex items-start gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            className="mt-0.5"
            checked={accept}
            onChange={(e) => setAccept(e.target.checked)}
          />
          <span>
            Acepto la{' '}
            <Link className="text-brand-600 underline" to="/privacy" target="_blank">
              política de privacidad
            </Link>{' '}
            y el tratamiento de mi CV para buscar ofertas.
          </span>
        </label>
        <Button
          type="submit"
          loading={register.isPending}
          disabled={!email || password.length < PASSWORD_MIN || !accept}
        >
          Crear cuenta
        </Button>
      </form>
      <Divider label="o" />
      <GoogleButton href={authApi.googleLoginUrl} />
    </AuthLayout>
  );
}

export function VerifyEmailPage() {
  const [params] = useSearchParams();
  const token = params.get('token') ?? '';
  const verify = useMutation({ mutationFn: authApi.verifyEmail });
  const started = useRef(false);

  useEffect(() => {
    // Tokens are single-use: guard against React StrictMode's double effect.
    if (token && !started.current) {
      started.current = true;
      verify.mutate(token);
    }
  }, [token, verify]);

  return (
    <AuthLayout title="Confirmación de email">
      {!token && <Alert kind="error">Falta el enlace de confirmación.</Alert>}
      {verify.isPending && <Alert kind="info">Confirmando tu email…</Alert>}
      {verify.isError && <Alert kind="error">{errorMessage(verify.error)}</Alert>}
      {verify.isSuccess && (
        <Alert kind="success">¡Email confirmado! Ya puedes iniciar sesión.</Alert>
      )}
      <Link className="block text-center text-sm font-semibold text-brand-600" to="/login">
        Ir a iniciar sesión
      </Link>
    </AuthLayout>
  );
}

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const forgot = useMutation({ mutationFn: () => authApi.forgotPassword(email) });
  return (
    <AuthLayout
      title="Recupera tu contraseña"
      subtitle="Te enviaremos un enlace para crear una nueva."
      footer={<Link to="/login">Volver a iniciar sesión</Link>}
    >
      {forgot.isSuccess ? (
        <Alert kind="success">
          Si existe una cuenta con ese email, recibirás un enlace en unos minutos.
        </Alert>
      ) : (
        <form
          className="space-y-4"
          noValidate
          onSubmit={(e) => {
            e.preventDefault();
            forgot.mutate();
          }}
        >
          {forgot.isError && <Alert kind="error">{errorMessage(forgot.error)}</Alert>}
          <TextField
            label="Email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Button type="submit" loading={forgot.isPending} disabled={!email}>
            Enviar enlace
          </Button>
        </form>
      )}
    </AuthLayout>
  );
}

export function ResetPasswordPage() {
  const [params] = useSearchParams();
  const token = params.get('token') ?? '';
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const reset = useMutation({ mutationFn: () => authApi.resetPassword(token, password) });
  const mismatch = confirm.length > 0 && confirm !== password;

  return (
    <AuthLayout title="Nueva contraseña" footer={<Link to="/login">Volver a iniciar sesión</Link>}>
      {!token && <Alert kind="error">Falta el enlace de recuperación.</Alert>}
      {reset.isSuccess ? (
        <Alert kind="success">
          Contraseña actualizada. Hemos cerrado tus sesiones abiertas por seguridad.{' '}
          <Link className="font-semibold underline" to="/login">
            Inicia sesión
          </Link>
        </Alert>
      ) : (
        <form
          className="space-y-4"
          noValidate
          onSubmit={(e) => {
            e.preventDefault();
            reset.mutate();
          }}
        >
          {reset.isError && <Alert kind="error">{errorMessage(reset.error)}</Alert>}
          <TextField
            label="Nueva contraseña"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            hint={<PasswordHint password={password} />}
          />
          <TextField
            label="Repite la contraseña"
            type="password"
            autoComplete="new-password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            error={mismatch ? 'Las contraseñas no coinciden.' : undefined}
          />
          <Button
            type="submit"
            loading={reset.isPending}
            disabled={!token || password.length < PASSWORD_MIN || password !== confirm}
          >
            Guardar contraseña
          </Button>
        </form>
      )}
    </AuthLayout>
  );
}
