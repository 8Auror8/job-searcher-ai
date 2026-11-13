# ADR-0002: Modos de candidatura y envío automático

- **Estado:** Sustituido por [ADR-0003](0003-sin-envio-automatico.md) (13/11/2026)
- **Fecha:** 13/11/2026

## Contexto

Requisito inicial: que la IA **envíe directamente** el formulario de la oferta y, si la oferta tiene contacto, mande la carta por email, **siempre respetando la legalidad**.

La revisión legal del Sprint 0 ([legal.md](../legal.md)) encontró que:
- Greenhouse y Lever solo permiten enviar candidaturas por API con una **clave privada de la empresa**.
- El acuerdo de usuario de MyGreenhouse prohíbe el uso de medios automatizados (bots, crawlers).
- Las condiciones de Lever para candidatos no se han podido confirmar.

## Decisión

1. Se implementa el **agente completo** (Playwright + Claude con herramientas) capaz de rellenar y enviar formularios.
2. El envío automático solo se activa en plataformas con `auto_submit_allowed = true`, un indicador que **exige una revisión legal documentada**. En el TFM esto incluye:
   - el **portal ATS de demostración** propio (`demo-ats/`), que imita la estructura de un portal real;
   - en el futuro, empresas que se den de alta voluntariamente.
3. En el resto de plataformas se usa el **modo asistido**: los campos del formulario se obtienen por la API pública (Greenhouse `?questions=true`), Claude prepara las respuestas y el usuario envía la candidatura en la web oficial.
4. Si la oferta tiene un contacto, se usa el **modo email** a través de la Gmail API, con el permiso mínimo `gmail.send`.
5. En todos los modos: aprobación humana previa, sin eludir CAPTCHAs ni logins, y registro de auditoría.

## Consecuencias

- ✅ Cumple la legalidad y lo puede defender ante el tribunal; demuestra el agente completo en un entorno controlado y reproducible.
- ✅ Activar una plataforma nueva solo requiere configuración, no cambiar código.
- ⚠️ En las plataformas reales de hoy, el usuario hace un último clic en la web oficial (modo asistido).
- 🔁 Se revisará si alguna fuente confirma que permite el envío automatizado por terceros.
