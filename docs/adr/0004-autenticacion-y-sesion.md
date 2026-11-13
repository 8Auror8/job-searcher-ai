# ADR-0004: Autenticación y gestión de sesión

- **Estado:** Aceptado
- **Fecha:** 16/11/2026

## Contexto

La app necesita login con email y contraseña y con Google, y guarda datos personales sensibles (CVs). El frontend (Vercel) y la API (Render) están en dominios distintos.

## Decisión

1. **Mismo origen mediante rewrite:** Vercel reenvía `/api/*` a Render. Para el navegador, la API está en el mismo origen que la SPA.
2. **Tokens en cookies httpOnly**, no en `localStorage`, para que un posible XSS no pueda robarlos:
   - `access_token`: JWT HS256 que dura 15 min, con `Secure` y `SameSite=Lax`.
   - `refresh_token`: aleatorio y opaco, dura 7 días y solo se envía a `/api/auth`. En la BD se guarda **solo su hash SHA-256**.
3. **Rotación de refresh tokens con detección de reutilización:** cada refresco revoca el token usado. Si alguien presenta un token ya revocado, se revoca toda la "familia" de tokens.
4. **CSRF con *double submit cookie*:** la cookie `csrf_token` (legible por JS) debe coincidir con la cabecera `X-CSRF-Token` en los métodos que modifican datos. Esto se suma a `SameSite=Lax`.
5. **Contraseñas:** argon2id (argon2-cffi), mínimo 10 caracteres y máximo 128.
6. **Google:** flujo *authorization code* con PKCE y `state`, en el servidor. El `id_token` se verifica con las claves públicas de Google (JWKS).
7. **No se revela si un email existe:** registro, reenvío y recuperación responden siempre 202.
8. **Rate limiting** por IP en las rutas de autenticación (slowapi).

## Alternativas descartadas

- **JWT en `localStorage`:** expuesto a XSS.
- **Servicio gestionado (Auth0, Clerk, Supabase Auth):** menos código, pero el TFM perdería la parte de seguridad que se quiere demostrar.
- **Sesiones de servidor clásicas:** válidas, pero los JWT de vida corta evitan consultar la BD en cada petición.

## Consecuencias

- ✅ Cubre los riesgos OWASP de robo de tokens, CSRF, enumeración de usuarios y fuerza bruta.
- ⚠️ En local, el proxy de Vite reproduce el mismo origen. Sin HTTPS, la cookie usa `Secure=false` (`COOKIE_SECURE=false`).
- ⚠️ El rate limit en memoria solo vale para una instancia. Si se escala, se pasaría a Redis.
