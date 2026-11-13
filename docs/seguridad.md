# Seguridad

> Sprint 1 · Versión 1.0 · 16/11/2026. Se completa en cada sprint y se audita en el Sprint 6.

## 1. OWASP Top 10 (2021): medidas por categoría

| Categoría | Medidas | Estado |
|---|---|---|
| **A01 Control de acceso** | Dependencia `current_user` en todas las rutas privadas. Las consultas filtran siempre por `user_id`. Hay tests de autorización (un usuario no ve los datos de otro). | Sprint 1: base ✅. Por recurso: Sprints 2–5 |
| **A02 Fallos criptográficos** | HTTPS en todo el despliegue, argon2id para contraseñas y SHA-256 para los tokens guardados. Los secretos solo están en variables de entorno. | ✅ |
| **A03 Inyección** | ORM con parámetros enlazados y validación Pydantic de toda entrada. React escapa la salida. Prompt injection: el texto de CVs y ofertas se trata como dato (ver legal.md, sección 5). | ✅ / IA desde Sprint 2 |
| **A04 Diseño inseguro** | Modelado de amenazas en este documento y aprobación humana de todo lo que genera la IA. La app no actúa en sitios de terceros (ADR-0003). | ✅ |
| **A05 Configuración insegura** | Cabeceras de seguridad (CSP, HSTS, X-Content-Type-Options, Referrer-Policy, frame-ancestors). OpenAPI desactivado en producción y CORS cerrado. Los errores no exponen trazas. | ✅ |
| **A06 Componentes vulnerables** | Dependabot, `pip-audit` y `npm audit` en la CI, con versiones fijadas. | Sprint 1: Dependabot ✅ |
| **A07 Fallos de autenticación** | Rate limiting y mensajes genéricos. Verificación de email obligatoria. Tokens de un solo uso con caducidad. Rotación de refresh tokens con detección de reutilización. Al cambiar la contraseña se cierran todas las sesiones. | ✅ |
| **A08 Integridad de software y datos** | `package-lock.json` y dependencias fijadas, CI obligatoria para fusionar y JWT firmados. | ✅ |
| **A09 Registro y monitorización** | Logs JSON con `request_id`. Se registran los logins fallidos y la reutilización de tokens, nunca contraseñas, tokens ni contenido del CV. | ✅ |
| **A10 SSRF** | La app no descarga URLs que proporcione el usuario. Las APIs de empleo son una lista cerrada de hosts. | Sprint 3 |

## 2. Modelo de amenazas (STRIDE resumido)

| Amenaza | Ejemplo | Mitigación |
|---|---|---|
| Suplantación | Robo de la cookie de sesión | httpOnly + Secure + SameSite, access token de vida corta, detección de reutilización |
| Manipulación | Petición forjada desde otra web | SameSite=Lax + CSRF *double submit* |
| Repudio | "Yo no borré mi cuenta" | Registro de auditoría de acciones sensibles (Sprint 6) |
| Fuga de información | Enumerar emails registrados | Respuestas 202 uniformes y mensajes de login genéricos |
| Denegación de servicio | Fuerza bruta o abuso de la IA | Rate limiting y topes de llamadas a la IA por usuario |
| Elevación de privilegios | Leer el CV de otro usuario | Filtro por `user_id` en los repositorios y tests de autorización |

## 3. Gestión de secretos

| Secreto | Dónde vive |
|---|---|
| `JWT_SECRET` | Variable de entorno en Render (≥ 32 bytes aleatorios) |
| `DATABASE_URL` | Variable de entorno en Render (Neon) |
| `GOOGLE_CLIENT_SECRET` | Variable de entorno en Render |
| `RESEND_API_KEY`, `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY` | Variables de entorno en Render |

`.env` está en `.gitignore`. El repositorio solo contiene `.env.example`, sin valores reales.

## 4. Política de contraseñas

- Entre 10 y 128 caracteres, sin reglas de composición forzadas (NIST SP 800-63B).
- Hash argon2id con los parámetros por defecto de `argon2-cffi`. Si cambian los parámetros, el hash se recalcula automáticamente en el siguiente login.
