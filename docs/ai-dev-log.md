# Registro de desarrollo asistido por IA

Este registro alimenta el capítulo de la memoria sobre **la IA en el proceso de desarrollo**. Cada entrada recoge qué se pidió a la IA, qué produjo, qué se revisó o corrigió y qué se aprendió.

**Herramienta principal:** Claude Code (modelo Claude Opus 5.5), en la aplicación de escritorio.
**Guía del repositorio para la IA:** [`CLAUDE.md`](../CLAUDE.md).

## Plantilla de entrada

```
### AAAA-MM-DD · Sprint N · Tarea
- **Objetivo:**
- **Qué hizo la IA:**
- **Revisión humana / correcciones:**
- **Errores o limitaciones de la IA detectados:**
- **Tiempo estimado** (con IA / sin IA estimado):
- **Aprendizaje:**
```

## Métricas acumuladas

| Sprint | Tareas con IA | Ficheros generados | % revisado y modificado | Errores de la IA detectados | Horas ahorradas (estimación) |
|---|---|---|---|---|---|
| 0 | 3 | 8 | _por completar_ | 1 | _por completar_ |

---

## Entradas

### 13/11/2026 · Sprint 0 · Planificación del proyecto
- **Objetivo:** convertir la idea del TFM en un planning profesional.
- **Qué hizo la IA:**
  - Hizo preguntas de aclaración en dos rondas (stack, LLM, fuentes, modo de candidatura, plazo, despliegue, login, idioma y enfoque).
  - Propuso la arquitectura, el cronograma, la estrategia de testing y seguridad, y los riesgos.
  - Amplió el alcance con las funcionalidades extra cuando se le pidió y recalculó el calendario (de 12 a 15 semanas).
- **Revisión humana / correcciones:** quien realiza el TFM eligió entre las opciones, pidió el envío directo de formularios con respeto a la legalidad e incorporó los extras.
- **Aprendizaje:** dar a la IA restricciones explícitas (presupuesto, plazo, legalidad) mejora mucho la calidad del plan.

### 13/11/2026 · Sprint 0 · Revisión legal de las fuentes
- **Objetivo:** comprobar qué fuentes y plataformas permiten el acceso y el envío automatizado.
- **Qué hizo la IA:** buscó en la web y leyó la documentación oficial (Greenhouse Job Board API, acuerdo de MyGreenhouse, condiciones de Adzuna) y fuentes secundarias (Remotive, Arbeitnow, Lever, Jooble).
- **Hallazgo clave:** el envío por API en Greenhouse y Lever exige la clave de la empresa, y MyGreenhouse prohíbe los bots. Esto llevó a los modos automático, asistido y email ([ADR-0002](adr/0002-aplicacion-automatica.md)).
- **Limitaciones de la IA:**
  - Varias conclusiones se basan en fuentes secundarias (blogs, agregadores) y algunas condiciones no se pudieron leer.
  - Hay que verificarlas a mano (tareas pendientes en [legal.md](legal.md)).
  - La IA no sustituye el asesoramiento jurídico.
- **Aprendizaje:** la IA acelera mucho la búsqueda de documentación, pero hay que contrastar sus fuentes y marcar el grado de certeza de cada una.

### 13/11/2026 · Sprint 0 · Documentación de análisis
- **Objetivo:** redactar el análisis, el backlog, el README, los ADR y el `CLAUDE.md`.
- **Qué hizo la IA:** generó los borradores completos de [analisis.md](analisis.md), [backlog.md](backlog.md), [legal.md](legal.md), el README y los ADR 0001 y 0002.
- **Error detectado y corregido:** en las historias de usuario la IA asumió un género para el rol de desarrollo ("desarrolladora"); se cambió por "equipo de desarrollo", neutral.
- **Revisión humana:** se aprobaron los tres modos de candidatura de la ADR-0002. Falta revisar a mano requisitos, prioridades y fechas.

### 13/11/2026 · Sprint 0 · Verificación de fuentes en documentación oficial
- **Objetivo:** antes de decidir si el proyecto sigue adelante, confirmar cuántas fuentes reales se pueden usar sin problemas legales ni técnicos.
- **Qué hizo la IA:** leyó la documentación oficial de 11 fuentes (Jooble, InfoJobs, Lever, Ashby, SmartRecruiters, Personio, Recruitee, Himalayas, Jobicy, RemoteOK y Workable) y reclasificó cada una en `legal.md`.
- **Resultados:**
  - 7 fuentes confirmadas en documentación oficial.
  - 6 utilizables con reservas o pendientes de confirmar.
  - SmartRecruiters descartada: necesita ser cliente.
  - Hallazgo positivo: InfoJobs tiene una API oficial con OAuth del candidato y una operación para inscribirse en ofertas, lo que podría permitir el envío automático legal (pendiente de sus condiciones de uso).
- **Limitaciones de la IA:** algunas páginas de condiciones no se pudieron leer (enlace roto en InfoJobs, página aparte en Jooble). Una primera búsqueda daba SmartRecruiters como pública y la documentación oficial lo desmintió: las fuentes secundarias no bastan.

### 13/11/2026 · Sprint 0 · Reorientación: sin envío automático, con importación de LinkedIn
- **Objetivo:** decidir el alcance tras comprobar que el envío automático no es legal en los portales reales.
- **Qué hizo la IA:**
  - Analizó las condiciones de uso de la API de InfoJobs que facilitó quien realiza el TFM: permiten inscribir al candidato con su permiso, pero prohíben las apps agregadoras.
  - Investigó las vías legales para usar LinkedIn: el scraping está prohibido y perseguido (Proxycurl cerró en 2025), y la importación del PDF del perfil es la alternativa legal.
  - Propuso conservar la preparación de la candidatura y quitar solo el envío.
  - Redactó la ADR-0003 y actualizó el análisis, el backlog, el README, `legal.md`, `CLAUDE.md` y la ADR-0001.
- **Decisión humana:** reorientar el proyecto sin envío automático y añadir la importación de LinkedIn. Se mantienen las 15 semanas.
- **Aprendizaje:** el análisis legal temprano hecho con IA evitó construir un componente (el agente de envío) que no se habría podido usar en portales reales. Ahorra unas 2 semanas de desarrollo.

### 13/11/2026 · Sprint 1 · Diseño, base del repositorio y autenticación
- **Objetivo:** completar las épicas E0 (infraestructura) y E1 (autenticación): HU-001 a HU-004 y HU-101 a HU-104.
- **Qué hizo la IA:**
  - Escribió `diseno.md` (arquitectura, ERD, API y secuencias en Mermaid), `seguridad.md` (OWASP Top 10 y STRIDE) y la ADR-0004 (sesión con cookies httpOnly en el mismo origen, rotación de refresh tokens y CSRF *double submit*).
  - Generó el backend: FastAPI, SQLAlchemy async, Alembic, argon2id, JWT, Google OAuth con PKCE, rate limiting y logs estructurados.
  - Generó el frontend: React, React Query y Tailwind, con login, registro, verificación, recuperación de contraseña y rutas protegidas.
  - Configuró la CI (PostgreSQL real, cobertura mínima, auditoría de dependencias), Docker Compose, Render, Vercel, pre-commit y Dependabot.
  - Comprobó el flujo completo en un navegador: registro → verificación → login → recarga → logout.
- **Errores de la IA detectados y corregidos durante la sesión:**
  1. En el login con Google, un usuario recién creado aún no tenía aplicado el valor por defecto `is_active` (`None` antes del *flush*) y el login se rechazaba. Los tests lo detectaron.
  2. La cobertura salía al 41 % porque `coverage` no seguía el código ejecutado en greenlets de SQLAlchemy; se corrigió con `concurrency = ["greenlet"]`.
  3. Incompatibilidad de tipos entre Vite 6 y Vitest 2; se actualizó a Vitest 3.
  4. `npm audit` detectó dos vulnerabilidades moderadas en React Router 6 (entre ellas un *open redirect*); se migró a React Router 7.
  5. Dos tests fallaban porque no enviaban la cabecera CSRF teniendo sesión abierta. El comportamiento del servidor era correcto; se corrigieron los tests.
- **Decisión de seguridad propuesta por la IA:** defensa contra el *pre-hijacking* de cuentas. Si alguien registra un email ajeno sin verificarlo y el dueño real entra después con Google, se borra la contraseña no verificada. Hay un test específico.
- **Resultado:** backend con 30 tests y 92 % de cobertura (ruff y mypy estricto sin errores); frontend con 13 tests (lint, tipado y build en verde; 0 vulnerabilidades en producción).
- **Pendiente humano:** crear las cuentas de Neon, Render, Vercel y Google Cloud para el despliegue (HU-003).
