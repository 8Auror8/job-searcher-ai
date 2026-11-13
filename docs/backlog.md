# Backlog y planificación

> Sprint 0 · Versión 1.1 · 13/11/2026. Reorientado según la [ADR-0003](adr/0003-sin-envio-automatico.md).
> Al crear el repositorio en GitHub (Sprint 1), cada historia se convertirá en un *issue* con su etiqueta de épica, dentro de un tablero de GitHub Projects.

## 1. Calendario (15 semanas)

| Sprint | Semanas | Fechas (provisionales) | Objetivo |
|---|---|---|---|
| 0. Análisis | 1 | 09/11 – 13/11/2026 | Requisitos, revisión legal y backlog ✅ |
| 1. Diseño y base | 2–3 | 16/11 – 27/11/2026 | Diseño, repositorio, CI, auth y primer despliegue ✅ (falta el despliegue: requiere cuentas) |
| 2. CV + versiones + LinkedIn | 4–5 | 30/11 – 11/12/2026 | Subida, importación de LinkedIn, parsing, perfil y versiones ✅ (falta probar la extracción con una clave real de Anthropic) |
| 3. Ofertas + matching | 6–7 | 14/12 – 25/12/2026 | Fuentes, embeddings, puntuación y panel |
| 4. Preparación de candidaturas + evaluación de la IA | 8–9 | 28/12/2026 – 08/01/2027 | Cartas, respuestas al formulario, CV adaptado, seguimiento y evaluación rigurosa de la IA |
| 5. Alertas + estadísticas + sugerencias | 10–12 | 11/01 – 29/01/2027 | Alertas diarias, estadísticas y mejora del CV |
| 6. Calidad | 13–14 | 01/02 – 12/02/2027 | Tests, seguridad, RGPD y pulido |
| 7. Entrega | 15 | 15/02 – 19/02/2027 | README, memoria, slides, vídeo y ensayo |

⚠️ Los sprints 3 y 4 coinciden con Navidad. Si esas semanas tienes menos disponibilidad, se desplaza el calendario o se usa el margen del Sprint 6.

**Puntos de control (hitos):**
- **H1 (27/11):** login desplegado en producción.
- **H2 (25/12):** recomendaciones de ofertas funcionando.
- **H3 (08/01):** candidatura preparada de principio a fin e informe de evaluación de la IA.
- **H4 (29/01):** todas las funcionalidades terminadas.
- **H5 (19/02):** entrega.

## 2. Épicas

| Épica | Descripción | Sprint |
|---|---|---|
| E0 | Infraestructura y DevOps | 1 (y transversal) |
| E1 | Autenticación y cuenta | 1 |
| E2 | CV, perfil, versiones e importación de LinkedIn | 2 |
| E3 | Ofertas y matching | 3 |
| E4 | Preparación de candidaturas y evaluación de la IA | 4 |
| E5 | Alertas | 5 |
| E6 | Estadísticas | 5 |
| E7 | Sugerencias del CV | 5 |
| E8 | Calidad, seguridad y RGPD | 6 (y transversal) |
| E9 | Documentación y entrega | 7 (y transversal) |

## 3. Historias de usuario

Estimación en puntos de historia (1, 2, 3, 5 u 8). La columna RF indica el requisito funcional que cubre cada historia ([analisis.md](analisis.md)).

### E0 · Infraestructura (Sprint 1)
| ID | Historia | Pts | RF/RNF |
|---|---|---|---|
| HU-001 | Como equipo de desarrollo, quiero un monorepo con backend y frontend, Docker Compose y `.env.example` para arrancar todo con un comando | 3 | RNF-12 |
| HU-002 | Como equipo de desarrollo, quiero CI en GitHub Actions (lint, tipos, tests, build) en cada PR para no fusionar código roto | 3 | RNF-07/08 |
| HU-003 | Como equipo de desarrollo, quiero desplegar automáticamente `main` en Vercel, Render y Neon para tener una URL pública desde el principio | 5 | RNF-06 |
| HU-004 | Como equipo de desarrollo, quiero logs estructurados y gestión central de errores para depurar en producción | 2 | RNF-10 |

### E1 · Autenticación (Sprint 1)
| ID | Historia | Pts | RF |
|---|---|---|---|
| HU-101 | Como visitante, quiero registrarme con email y contraseña y verificar mi email | 5 | RF-01 |
| HU-102 | Como candidato, quiero iniciar sesión con email o con Google | 5 | RF-02 |
| HU-103 | Como candidato, quiero que mi sesión se renueve de forma segura y poder cerrarla | 3 | RF-03 |
| HU-104 | Como candidato, quiero recuperar mi contraseña por email | 2 | RF-04 |

**Criterios de aceptación de HU-101:**
- La contraseña tiene al menos 10 caracteres y se guarda con argon2.
- El email de verificación caduca a las 24 h.
- No se puede iniciar sesión sin verificar el email.
- El sistema no revela si un email ya está registrado.
- El endpoint tiene rate limiting.

### E2 · CV y perfil (Sprint 2)
| ID | Historia | Pts | RF |
|---|---|---|---|
| HU-201 | Como candidato, quiero subir mi CV en PDF o DOCX dando mi consentimiento | 3 | RF-10, RF-06 |
| HU-202 | Como candidato, quiero que la IA extraiga mi perfil para no tener que escribirlo | 8 | RF-11 |
| HU-203 | Como candidato, quiero revisar y corregir el perfil extraído | 3 | RF-12 |
| HU-204 | Como candidato, quiero tener varias versiones de mi CV y elegir la principal | 5 | RF-13 |
| HU-205 | Como candidato, quiero definir mis preferencias de búsqueda | 3 | RF-14 |
| HU-206 | Como candidato, quiero importar mi perfil de LinkedIn subiendo su PDF, para no tener que preparar un CV | 5 | RF-15 |

**Criterios de aceptación de HU-206:**
- La interfaz explica cómo descargar el PDF desde LinkedIn ("Más → Guardar en PDF").
- La app no se conecta a LinkedIn: solo procesa el archivo que sube el usuario.
- Se crea una versión del CV con origen `linkedin_pdf`, editable como cualquier otra.
- Hay tests con al menos 3 PDF de perfil distintos (anonimizados).

**Criterios de aceptación de HU-202:**
- Se comprueba el tipo MIME real y el tamaño máximo (5 MB).
- La salida de la IA se valida con un esquema Pydantic; si no es válida, se reintenta una vez y después se muestra un error.
- Ningún campo extraído aparece si no está en el CV (comprobado con el conjunto de evaluación).
- Se registran el coste y la latencia de la llamada.

### E3 · Ofertas y matching (Sprint 3)
| ID | Historia | Pts | RF |
|---|---|---|---|
| HU-301 | Como sistema, quiero adapters con una interfaz común `JobSource` para las fuentes confirmadas (Adzuna, Arbeitnow, Jobicy, Himalayas, RemoteOK, Greenhouse y Lever) y, si se confirman, Jooble, Ashby y Personio | 8 | RF-20 |
| HU-307 | Como sistema, quiero una lista configurable de empresas objetivo (plataforma + identificador) para consultar las plataformas de selección | 3 | RF-20 |
| HU-302 | Como sistema, quiero normalizar y deduplicar las ofertas | 3 | RF-21 |
| HU-303 | Como sistema, quiero calcular embeddings y preseleccionar el top N con pgvector | 5 | RF-22 |
| HU-304 | Como candidato, quiero ver una puntuación de 0 a 100 con la explicación del encaje | 8 | RF-23, RF-24 |
| HU-305 | Como candidato, quiero un panel de ofertas con filtros y enlace a la oferta original | 5 | RF-25, RF-26 |
| HU-306 | Como equipo de desarrollo, quiero un script de evaluación del matching con un conjunto etiquetado | 5 | OE3 |

### E4 · Preparación de candidaturas y evaluación de la IA (Sprint 4)
| ID | Historia | Pts | RF |
|---|---|---|---|
| HU-401 | Como candidato, quiero una carta de presentación personalizada y editable, para copiar o descargar | 3 | RF-30 |
| HU-402 | Como candidato, quiero que la IA me prepare las respuestas a las preguntas del formulario de la oferta | 5 | RF-31 |
| HU-403 | Como candidato, quiero sugerencias para adaptar mi CV a una oferta concreta y poder guardar esa versión | 5 | RF-32 |
| HU-404 | Como candidato, quiero una vista "Preparar candidatura" con todo listo y un botón que me lleve a la oferta original | 3 | RF-33 |
| HU-405 | Como candidato, quiero marcar el estado de mis candidaturas y añadir notas | 3 | RF-34 |
| HU-406 | Como candidato, quiero que me avisen si una oferta guardada ya no está publicada | 2 | RF-35 |
| HU-407 | Como equipo de desarrollo, quiero ampliar la evaluación de la IA a cartas y respuestas, midiendo los datos inventados, el coste y la latencia | 5 | OE4, RNF-11 |

**Criterios de aceptación de HU-402:**
- Las preguntas se obtienen de la API de la fuente (Greenhouse `?questions=true`); si la fuente no las da, se ofrece un conjunto de respuestas a preguntas habituales.
- Cada respuesta indica en qué parte del CV se basa. Si no hay base, se deja vacía y marcada como "Completar tú".
- Las preguntas demográficas o sensibles nunca se responden con IA.
- La app no envía nada: el usuario copia las respuestas al formulario original.

### E5 · Alertas (Sprint 5)
| ID | Historia | Pts | RF |
|---|---|---|---|
| HU-501 | Como candidato, quiero crear, editar y pausar alertas | 3 | RF-40 |
| HU-502 | Como sistema, quiero ejecutar las alertas a diario desde un cron de GitHub Actions contra un endpoint protegido | 5 | RF-41 |
| HU-503 | Como candidato, quiero recibir un resumen por email y poder darme de baja con un clic | 5 | RF-42 |

### E6 · Estadísticas (Sprint 5)
| ID | Historia | Pts | RF |
|---|---|---|---|
| HU-601 | Como candidato, quiero ver la distribución de puntuaciones y el embudo de candidaturas | 5 | RF-43 |
| HU-602 | Como candidato, quiero ver las skills más pedidas comparadas con las mías | 5 | RF-43 |
| HU-603 | Como candidato, quiero ver la evolución temporal y comparar mis versiones del CV | 5 | RF-44 |

### E7 · Sugerencias del CV (Sprint 5)
| ID | Historia | Pts | RF |
|---|---|---|---|
| HU-701 | Como candidato, quiero sugerencias priorizadas y justificadas para mejorar mi CV | 8 | RF-45 |
| HU-702 | Como candidato, quiero crear una versión nueva del CV con las sugerencias aceptadas | 5 | RF-46 |

### E8 · Calidad, seguridad y RGPD (Sprint 6)
| ID | Historia | Pts | RF/RNF |
|---|---|---|---|
| HU-801 | Como candidato, quiero exportar mis datos y borrar mi cuenta | 3 | RF-05 |
| HU-802 | Como equipo de desarrollo, quiero tests E2E del flujo completo con Playwright | 5 | RNF-08 |
| HU-803 | Como equipo de desarrollo, quiero revisar la checklist OWASP Top 10 y corregir lo que falte | 5 | RNF-01 |
| HU-804 | Como candidato, quiero una política de privacidad y textos de consentimiento claros | 2 | RNF-02 |
| HU-805 | Como equipo de desarrollo, quiero revisar la accesibilidad y el rendimiento | 3 | RNF-04/09 |

### E9 · Entrega (transversal y Sprint 7)
| ID | Historia | Pts |
|---|---|---|
| HU-901 | README completo con capturas | 3 |
| HU-902 | Memoria del TFM, incluido el capítulo sobre desarrollo con IA | 8 |
| HU-903 | Slides (unas 15) y vídeo de demo (3 min) | 5 |
| HU-904 | Etiquetar la versión v1.0.0 y comprobar el despliegue final | 1 |

**Total aproximado:** unos 209 puntos en 14 semanas de desarrollo, unos 15 por semana. El Sprint 5 es el más cargado y por eso dura 3 semanas. Se mantienen las 15 semanas: las 2 que dejó libres el agente se reparten entre la importación de LinkedIn, la evaluación de la IA y la calidad.

## 4. Definición de terminado (DoD)

Una historia está terminada cuando:
- [ ] Cumple todos sus criterios de aceptación.
- [ ] Tiene tests (unitarios y, si toca, de integración) y la CI está en verde.
- [ ] Pasa lint y tipado sin errores.
- [ ] Está revisada en un PR y fusionada en `develop`.
- [ ] Está documentada si cambia la API, la configuración o el README.
- [ ] Si usa IA: el prompt está versionado y la salida validada con un esquema.
- [ ] Hay una entrada en `docs/ai-dev-log.md` si se desarrolló con ayuda de IA.

## 5. Plan de recorte (si hay retrasos)

Se recorta en este orden: HU-603 → HU-702 → HU-406 → HU-104 → fuentes 🟡 en HU-301 → HU-805.
