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
  unsupported_file: 'Solo se admiten archivos PDF o Word (.docx).',
  file_too_large: 'El archivo supera los 5 MB.',
  cv_unreadable:
    'No hemos podido leer texto del archivo. Si es un PDF escaneado, sube otra versión o crea el perfil a mano.',
  cv_too_long: 'El documento es demasiado largo para ser un CV (máximo 20 páginas).',
  consent_required: 'Necesitamos tu consentimiento para analizar el CV.',
  ai_unavailable:
    'La IA no está disponible ahora mismo. Inténtalo más tarde o rellena el perfil a mano.',
  ai_quota_exceeded:
    'Has alcanzado el límite diario de análisis con IA. Vuelve a intentarlo mañana.',
  too_many_versions: 'Puedes tener hasta 10 versiones activas. Archiva alguna antes de crear otra.',
  no_source_text: 'Esta versión no tiene documento que analizar.',
  not_found: 'No hemos encontrado ese CV.',
};

const GENERIC = 'Ha ocurrido un error inesperado. Inténtalo de nuevo.';

export function messageForCode(code: string): string {
  return MESSAGES[code] ?? GENERIC;
}

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return messageForCode(error.code);
  return 'No se ha podido conectar con el servidor.';
}

export const PASSWORD_MIN = 10;

export function passwordStrength(password: string): 0 | 1 | 2 | 3 {
  if (password.length < PASSWORD_MIN) return 0;
  const variety = [/[a-z]/, /[A-Z]/, /\d/, /[^A-Za-z0-9]/].filter((r) => r.test(password)).length;
  if (password.length >= 16 || variety >= 3) return 3;
  return variety >= 2 ? 2 : 1;
}
