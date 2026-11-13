# ADR-0001: Stack tecnológico

- **Estado:** Aceptado
- **Fecha:** 13/11/2026

## Contexto

El proyecto necesita:
- Procesar documentos (CV).
- Llamar a LLMs con salida estructurada.
- Hacer búsqueda semántica.
- Automatizar un navegador.
- Ejecutar tareas en segundo plano y programadas.
- Ofrecer una interfaz web moderna con gráficos.

Restricciones: una sola persona, 15 semanas, menos de 10 €/mes y el requisito de que sea fácil de defender en un TFM.

## Decisión

| Capa | Elección | Alternativas descartadas |
|---|---|---|
| Backend | **Python + FastAPI** | Next.js API routes (ecosistema de IA y de procesado de documentos más pobre); Django (más pesado y menos orientado a APIs asíncronas) |
| Frontend | **React + TypeScript + Vite** | Next.js (no hace falta SSR: es una aplicación privada tras login); plantillas renderizadas en servidor (menos interactivas) |
| BD | **PostgreSQL + pgvector (Neon)** | Una BD vectorial aparte, como Pinecone (otro servicio más que mantener); SQLite (no sirve para la nube ni para vectores) |
| LLM | **Claude: Haiku 5.5 para el volumen, Sonnet 5.5 para la calidad** | OpenAI (equivalente, pero se prioriza el uso de herramientas para el agente); modelo local (lento y no desplegable gratis) |
| Embeddings | **Voyage AI** | Modelo local con sentence-transformers (demasiada RAM para el plan gratuito) |
| Cola de tareas | **Tabla en PostgreSQL (`SELECT … FOR UPDATE SKIP LOCKED`)** | Celery + Redis (otro servicio más; volumen bajo) |
| Programación | **Cron de GitHub Actions → endpoint protegido** | APScheduler (el plan gratuito de Render se duerme); Render Cron (de pago) |
| Tests E2E | **Playwright** | Selenium (API más antigua y menos fiable). *Nota: tras la ADR-0003, Playwright solo se usa para tests, no para automatizar candidaturas.* |
| Hosting | **Vercel + Render + Neon** | VPS (más control, pero cuesta dinero y hay que mantenerlo) |

## Consecuencias

- ✅ Coste casi nulo, un solo motor de datos, buen encaje con la IA.
- ⚠️ El plan gratuito de Render tiene 512 MB y arranque en frío. Al no haber navegador en el servidor (ADR-0003), basta para la API y las tareas en segundo plano.
- ⚠️ Dos lenguajes (Python y TypeScript): se mitiga generando el cliente de TypeScript a partir del esquema OpenAPI.
