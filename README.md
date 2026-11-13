# JobPilot AI

> Tu copiloto de búsqueda de empleo: sube tu CV o tu perfil de LinkedIn y la IA encuentra las ofertas que encajan contigo, te explica por qué y te deja cada candidatura preparada a un clic de la oferta original.

![Estado](https://img.shields.io/badge/estado-Sprint%201%20%C2%B7%20base%20y%20auth-blue)
![Licencia](https://img.shields.io/badge/licencia-MIT-green)

Trabajo de Fin de Máster sobre **desarrollo de software con IA**. La IA está **dentro del producto** (análisis del CV, matching, preparación de candidaturas y sugerencias) y **en el proceso de desarrollo** (ver el [registro de desarrollo con IA](docs/ai-dev-log.md)).

---

## Índice
1. [Descripción](#descripción)
2. [Funcionalidades](#funcionalidades)
3. [Stack tecnológico](#stack-tecnológico)
4. [Arquitectura](#arquitectura)
5. [Estructura del proyecto](#estructura-del-proyecto)
6. [Instalación y ejecución](#instalación-y-ejecución)
7. [Testing](#testing)
8. [Seguridad y legalidad](#seguridad-y-legalidad)
9. [Despliegue](#despliegue)
10. [Documentación](#documentación)
11. [Hoja de ruta](#hoja-de-ruta)
12. [Licencia](#licencia)

---

## Descripción

Buscar empleo implica revisar muchos portales, descartar ofertas que no encajan y redactar una y otra vez cartas y respuestas parecidas. **JobPilot AI** hace el trabajo mecánico y te deja a ti las decisiones:

1. **Analiza tu CV**, o el PDF de tu perfil de LinkedIn, con IA y crea un perfil estructurado que puedes editar.
2. **Busca ofertas** en varias fuentes legales: APIs oficiales de portales de empleo y de plataformas de selección de empresas.
3. **Puntúa el encaje** de cada oferta (de 0 a 100) y te explica tus puntos fuertes y lo que te falta.
4. **Prepara tu candidatura**: carta de presentación, respuestas al formulario y sugerencias para adaptar tu CV a esa oferta.
5. **Te lleva a la oferta original** para que la envíes tú, y te ayuda a seguir el estado de cada candidatura.

Además, te avisa de las ofertas nuevas, te muestra estadísticas de tu búsqueda y te sugiere cómo mejorar tu CV según lo que de verdad pide el mercado.

> **JobPilot nunca envía candidaturas en tu nombre.** Es una decisión de diseño: los principales portales no permiten que terceros envíen candidaturas automáticamente. El motivo está en la [ADR-0003](docs/adr/0003-sin-envio-automatico.md) y en [docs/legal.md](docs/legal.md).

## Funcionalidades

| Área | Funcionalidad |
|---|---|
| 🔐 Cuenta | Registro con email y contraseña o Google, verificación de email, exportación y borrado de datos (RGPD) |
| 📄 CV | Subida de PDF o DOCX, **importación del PDF del perfil de LinkedIn**, extracción con IA, perfil editable y **varias versiones del CV** |
| 🔎 Ofertas | Adzuna, Arbeitnow, Jobicy, Himalayas, RemoteOK, Greenhouse y Lever (y Jooble, Ashby y Personio cuando se confirmen), con normalización y deduplicación |
| 🎯 Matching | Preselección semántica (embeddings y pgvector) y puntuación explicada con Claude |
| ✍️ Candidaturas | Carta generada por IA, respuestas al formulario, CV adaptado a la oferta, enlace directo a la oferta y seguimiento de estados |
| ⏰ Alertas | Búsquedas programadas diarias o semanales con resumen por email |
| 📊 Estadísticas | Distribución del encaje, skills más pedidas frente a las tuyas, embudo de candidaturas y cobertura por fuente |
| 💡 Mejora del CV | Sugerencias justificadas por las ofertas reales, sin inventar experiencia |

## Stack tecnológico

| Capa | Tecnología | Por qué |
|---|---|---|
| Frontend | React 18 + TypeScript + Vite, TailwindCSS, React Query, React Router y Recharts | Ecosistema maduro, tipado estricto y buena experiencia de desarrollo |
| Backend | Python 3.12 + FastAPI, SQLAlchemy 2, Alembic y Pydantic v2 | Python es el ecosistema natural de la IA; FastAPI es asíncrono, tipado y genera la documentación OpenAPI |
| Base de datos | PostgreSQL 16 + pgvector | Datos relacionales y búsqueda vectorial en un mismo motor |
| IA | Claude API: Haiku 5.5 para extraer y puntuar, Sonnet 5.5 para cartas, respuestas y sugerencias | Salida estructurada fiable y buen equilibrio entre coste y calidad |
| Embeddings | Voyage AI | Buena calidad de búsqueda semántica y plan gratuito |
| Email | Resend | Avisos de alertas |
| Calidad | pytest, Vitest, Playwright (tests E2E), Ruff, mypy, ESLint, Prettier y pre-commit | |
| CI/CD | GitHub Actions | Tests en cada PR, despliegue de `main` y cron de alertas |
| Hosting | Vercel (frontend), Render (API en Docker) y Neon (PostgreSQL) | Planes gratuitos: menos de 10 €/mes en total |

La justificación completa está en la [ADR-0001](docs/adr/0001-stack-tecnologico.md).

## Arquitectura

```
┌──────────────┐  HTTPS   ┌───────────────────┐      ┌──────────────────────┐
│  React SPA   │ ───────► │   FastAPI (API)   │ ───► │ PostgreSQL + pgvector │
│  (Vercel)    │          │     (Render)      │      │        (Neon)         │
└──────────────┘          └─────────┬─────────┘      └──────────────────────┘
                                    │ tareas en segundo plano (cola en BD)
               ┌────────────────────┼─────────────────────┐
               ▼                    ▼                     ▼
      ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
      │ Claude / Voyage  │  │  APIs de empleo  │  │ Resend (avisos) │
      └─────────────────┘  └─────────────────┘  └─────────────────┘
                                    ▲
                     cron de GitHub Actions (alertas diarias)
```

El backend se organiza **por capas** (routers → services → repositories). Cada fuente de empleo es un **adapter** que implementa la interfaz `JobSource`.

## Estructura del proyecto

```
jobpilot-ai/
├── backend/
│   ├── app/
│   │   ├── api/            # routers: auth, cv, jobs, applications, alerts, stats
│   │   ├── core/           # configuración, seguridad y logging
│   │   ├── models/         # modelos SQLAlchemy
│   │   ├── schemas/        # esquemas Pydantic
│   │   ├── services/       # cv_parser, linkedin_import, matching, job_sources/, application_prep, suggestions, mailer
│   │   ├── prompts/        # prompts versionados
│   │   ├── eval/           # evaluación de la IA
│   │   ├── repositories/
│   │   └── workers/
│   ├── alembic/
│   └── tests/              # unitarios e integración
├── frontend/
│   └── src/                # pages, components, hooks, api, routes
├── e2e/                    # tests end-to-end con Playwright
├── docs/                   # análisis, legal, backlog, ADR y registro de IA
├── .github/workflows/
├── docker-compose.yml
├── .env.example
├── CLAUDE.md
└── README.md
```

> Sprint 1: existen `backend/` (autenticación completa), `frontend/` (login, registro, recuperación y panel vacío) y `docs/`. Las carpetas `eval/`, `prompts/` y `e2e/` llegan en los siguientes sprints.

## Instalación y ejecución

**Requisitos:** Python 3.11+ y Node 20+. Docker es opcional.

Las claves de API (Anthropic, Voyage, Adzuna) solo hacen falta a partir del Sprint 2. Google OAuth y Resend son opcionales: sin Resend, los emails (por ejemplo, el enlace de verificación) se escriben en el log de la API.

### Opción A: con Docker

```bash
cp .env.example .env
docker compose up --build
```

### Opción B: sin Docker (SQLite)

1. Crea el `.env` y elige SQLite: en `.env`, comenta la línea de PostgreSQL y activa `DATABASE_URL=sqlite+aiosqlite:///./jobpilot.db`.

   ```bash
   cp .env.example .env
   ```

2. Instala el backend, aplica las migraciones y arranca la API:

   ```bash
   cd backend
   python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   alembic upgrade head
   uvicorn app.main:app --reload --port 8000
   ```

3. En otra terminal, arranca el frontend:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

Con cualquiera de las dos opciones:
- El frontend queda en http://localhost:5173. Vite reenvía `/api` al backend, en el mismo origen que en producción.
- La documentación OpenAPI está en http://localhost:8000/api/docs.

## Testing

| Tipo | Herramienta | Comando |
|---|---|---|
| Backend: unitarios e integración | pytest (SQLite en local, PostgreSQL en la CI) | `cd backend && pytest --cov` |
| Backend: calidad | Ruff + mypy (estricto) | `ruff check . && mypy app` |
| Frontend: unitarios y de componentes | Vitest + Testing Library | `cd frontend && npm test` |
| Frontend: calidad | ESLint + Prettier + `tsc` | `npm run lint && npm run typecheck` |
| End-to-end | Playwright | Sprint 6 |
| Evaluación de la IA | Script propio | Sprints 3 y 4 |

**Estado actual (Sprint 1):**
- Backend: 30 tests, 92 % de cobertura.
- Frontend: 13 tests.
- La CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) exige cobertura ≥ 70 %, que las migraciones funcionen sobre PostgreSQL y una auditoría de dependencias sin vulnerabilidades.

## Seguridad y legalidad

- **Autenticación y sesión:** contraseñas con argon2, JWT de vida corta en cookie httpOnly, CSRF, rate limiting y CORS restringido.
- **Datos:** validación de las subidas y control de acceso por usuario.
- **Prompt injection:** el texto de CVs y ofertas se trata como dato, nunca como instrucciones, y la IA no tiene herramientas con efectos externos.
- **Fuentes:** solo APIs que permiten el acceso, con atribución y enlace al origen. Sin scraping de LinkedIn, Indeed ni otros portales que lo prohíben.
- **Candidaturas:** la app nunca actúa en tu nombre en webs de terceros. Para LinkedIn solo se usa el PDF que tú descargas y subes.
- **RGPD:** consentimiento, minimización de datos, exportación y borrado.

Más detalle en [docs/legal.md](docs/legal.md) y, desde el Sprint 1, en `docs/seguridad.md`.

## Despliegue

| Pieza | Plataforma | Configuración |
|---|---|---|
| Base de datos | Neon (PostgreSQL) | Crear el proyecto y copiar la cadena de conexión con el prefijo `postgresql+asyncpg://` |
| API | Render (Docker) | [`render.yaml`](render.yaml): las migraciones se aplican al arrancar |
| Frontend | Vercel | [`frontend/vercel.json`](frontend/vercel.json): reenvía `/api/*` a Render (mismo origen, ver [ADR-0004](docs/adr/0004-autenticacion-y-sesion.md)) |

> 🚧 URL pública: pendiente de crear las cuentas en Neon, Render y Vercel.

## Documentación

| Documento | Contenido |
|---|---|
| [docs/analisis.md](docs/analisis.md) | Objetivos, requisitos, casos de uso y riesgos |
| [docs/diseno.md](docs/diseno.md) | Arquitectura, modelo de datos, API, diagramas de secuencia y pantallas |
| [docs/seguridad.md](docs/seguridad.md) | OWASP Top 10, modelo de amenazas y gestión de secretos |
| [docs/legal.md](docs/legal.md) | Revisión de las condiciones de uso de cada fuente y RGPD |
| [docs/backlog.md](docs/backlog.md) | Calendario, épicas, historias de usuario y definición de terminado |
| [docs/adr/](docs/adr/) | Registros de decisiones de arquitectura |
| [docs/ai-dev-log.md](docs/ai-dev-log.md) | Registro del desarrollo asistido por IA |

## Hoja de ruta

- [x] **Sprint 0** · Análisis, revisión legal y backlog
- [x] **Sprint 1** · Diseño, repositorio, CI y autenticación (despliegue pendiente de cuentas)
- [ ] **Sprint 2** · CV, versiones e importación de LinkedIn
- [ ] **Sprint 3** · Ofertas y matching
- [ ] **Sprint 4** · Preparación de candidaturas y evaluación de la IA
- [ ] **Sprint 5** · Alertas, estadísticas y sugerencias
- [ ] **Sprint 6** · Calidad y seguridad
- [ ] **Sprint 7** · Entrega

## Licencia

MIT. Las ofertas mostradas pertenecen a sus respectivas fuentes y siempre enlazan al original.
