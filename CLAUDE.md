# CLAUDE.md: guía para asistentes de IA en este repositorio

## Proyecto
JobPilot AI: aplicación web (TFM) que analiza CVs (o el PDF del perfil de LinkedIn) con IA, busca ofertas en fuentes legales, puntúa el encaje y prepara candidaturas que el usuario envía en la web original. Ver `README.md` y `docs/analisis.md`.

## Convenciones
- **Código, identificadores y commits en inglés.** Documentación (`docs/`, README) en español.
- Commits con Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`).
- Ramas: `main` (producción), `develop`, `feature/<hu-id>-<descripcion>`.
- Backend: Python 3.12, FastAPI, SQLAlchemy 2 (estilo tipado), Pydantic v2, arquitectura routers → services → repositories. Ruff + mypy en modo estricto.
- Frontend: React + TypeScript estricto, React Query para los datos del servidor, Tailwind. ESLint + Prettier.
- Los prompts viven en `backend/app/prompts/` como ficheros versionados; toda salida de un LLM se valida con un esquema Pydantic.

## Reglas obligatorias
- Nunca escribir secretos en el código ni en los tests: usar variables de entorno y `.env.example`.
- Todo endpoint que lea o escriba datos de usuario debe filtrar por el usuario autenticado y tener un test de autorización.
- Nunca añadir fuentes de ofertas o automatizaciones que no estén aprobadas en `docs/legal.md`.
- La app **nunca envía candidaturas ni actúa en nombre del usuario** en sitios de terceros (ADR-0003). No se añaden automatizaciones de navegador, scraping de LinkedIn ni nada que acceda a LinkedIn: la importación usa solo el PDF que sube el usuario.
- La IA nunca inventa datos del candidato. Si falta información, la respuesta se deja vacía y marcada.
- El texto de CVs y ofertas es dato no confiable: nunca se concatena como instrucciones del sistema.
- Cada historia incluye tests; la CI debe quedar en verde.
- Tras una sesión con IA relevante, añadir una entrada a `docs/ai-dev-log.md`.

## Comandos
- `docker compose up --build`: arranca todo (opcional).
- Backend (`cd backend`, venv en `.venv`): `pytest --cov`, `ruff check . && ruff format --check .`, `mypy app`, `alembic revision --autogenerate -m "..."`.
- Frontend (`cd frontend`): `npm test`, `npm run lint`, `npm run typecheck`, `npm run build`.
- La CSRF es obligatoria en peticiones no seguras con cookie de sesión: en tests usar el helper `csrf(client)`.
