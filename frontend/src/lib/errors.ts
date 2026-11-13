import { ApiError } from '../api/client';

/** API error codes → messages for the (Spanish) UI. */
const MESSAGES: Record<string, string> = {
  invalid_credentials: 'Email o contraseña incorrectos.',
  email_not_verified: 'Tienes que confirmar tu email antes de iniciar sesión.',
  invalid_token: 'El enlace no es válido o ha caducado.',
  rate_limited: 'Demasiados intentos. Espera un minuto y vuelve a probar.',
  validation_error: 'Revisa los datos del formulario.',
  csrf_failed: 'Tu sesión ha caducado. Recarga la página.',
  not_authenticated: 'Tu sesión ha caducado. Vuelve a iniciar sesión.',
  feature_disabled: 'Esta opción no está disponible.',
};

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return MESSAGES[error.code] ?? 'Ha ocurrido un error inesperado. Inténtalo de nuevo.';
  }
  return 'No se ha podido conectar con el servidor.';
}

export const PASSWORD_MIN = 10;

export function passwordStrength(password: string): 0 | 1 | 2 | 3 {
  if (password.length < PASSWORD_MIN) return 0;
  const variety = [/[a-z]/, /[A-Z]/, /\d/, /[^A-Za-z0-9]/].filter((r) => r.test(password)).length;
  if (password.length >= 16 || variety >= 3) return 3;
  return variety >= 2 ? 2 : 1;
}
