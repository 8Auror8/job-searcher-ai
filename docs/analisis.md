# Análisis del proyecto JobPilot AI

> Sprint 0 · Versión 1.1 · 13/11/2026. Reorientado según la [ADR-0003](adr/0003-sin-envio-automatico.md): sin envío automático y con importación de LinkedIn.

## 1. Contexto y problema

Buscar empleo exige revisar a diario decenas de portales, leer ofertas que muchas veces no encajan con el perfil y rellenar una y otra vez los mismos formularios. Según el propio sector, la mayor parte del tiempo de un candidato se va en **filtrar** y en **tareas repetitivas**, no en preparar bien las candidaturas que de verdad le interesan.

Los grandes modelos de lenguaje (LLM) permiten hoy entender un CV y una oferta como lo haría una persona de selección, explicar por qué encajan o no, y redactar textos personalizados. Esto abre la puerta a un asistente que haga el trabajo mecánico **sin quitarle al candidato el control de la decisión**.

## 2. Objetivos

**Objetivo general:** desarrollar una aplicación web que, a partir del CV del usuario, encuentre ofertas de empleo afines en varias fuentes, las ordene por encaje con una explicación y le prepare cada candidatura (carta, respuestas y adaptación del CV), con enlace directo a la oferta original para que la envíe él mismo.

**Objetivos específicos:**

| ID | Objetivo | Indicador de éxito |
|---|---|---|
| OE1 | Extraer un perfil estructurado de un CV en PDF o DOCX o del PDF del perfil de LinkedIn | ≥ 90 % de campos correctos en el conjunto de evaluación |
| OE2 | Agregar ofertas de al menos 3 fuentes legales | 3 adapters funcionando con deduplicación |
| OE3 | Puntuar el encaje CV–oferta con explicación | Correlación ≥ 0,7 con la valoración humana en el conjunto de evaluación |
| OE4 | Preparar con IA cada candidatura sin inventar datos | Carta, respuestas y adaptación del CV con un 0 % de datos inventados en la evaluación; enlace directo a la oferta |
| OE5 | Mantener al usuario informado y ayudarle a mejorar | Alertas diarias, panel de estadísticas y sugerencias del CV |
| OE6 | Documentar el uso de IA en el proceso de desarrollo | Registro de desarrollo con IA y capítulo propio en la memoria |
| OE7 | Garantizar calidad y seguridad | Cobertura de tests ≥ 70 %, checklist OWASP Top 10 superado, CI en verde |

## 3. Alcance

**Dentro del alcance:** todo lo descrito en los requisitos funcionales (RF) de la sección 5.

**Fuera del alcance:**
- **Enviar candidaturas en nombre del usuario**, ni por formulario ni por email ([ADR-0003](adr/0003-sin-envio-automatico.md)).
- Leer ofertas de LinkedIn, Indeed, Glassdoor, InfoJobs o Remotive, por sus condiciones de uso ([legal.md](legal.md)).
- Acceder a LinkedIn: la importación usa solo el PDF que el usuario descarga y sube.
- Saltarse CAPTCHAs, logins o límites de las plataformas.
- Apps móviles nativas; la web será responsive.
- Pagos o planes de suscripción.

## 4. Actores

| Actor | Descripción |
|---|---|
| **Candidato** (usuario registrado) | Sube su CV o su perfil de LinkedIn, revisa las ofertas, prepara candidaturas con la IA, las envía en la web original y consulta estadísticas. |
| **Visitante** | Ve la página de inicio y puede registrarse o iniciar sesión. |
| **Planificador** (sistema) | Lanza las búsquedas programadas a diario. |
| **Servicios externos** | Claude API, Voyage AI, APIs de empleo, Google OAuth (solo login) y Resend. |
| **Administrador** | Gestiona las fuentes activas y la lista de empresas que se consultan en las plataformas de selección, y consulta los logs. Sin interfaz propia en el MVP: se gestiona por configuración. |

## 5. Requisitos funcionales

Prioridad según MoSCoW: **M** = Must (imprescindible), **S** = Should (debería tener).

### Autenticación y cuenta
| ID | Requisito | Prioridad |
|---|---|---|
| RF-01 | Registro con email y contraseña, con verificación de email | M |
| RF-02 | Inicio de sesión con email y contraseña, y con Google (OAuth 2.0) | M |
| RF-03 | Cierre de sesión y renovación segura de la sesión (refresh token) | M |
| RF-04 | Recuperación de contraseña por email | S |
| RF-05 | Exportar mis datos (JSON) y eliminar mi cuenta con todos sus datos | M |
| RF-06 | Gestionar los consentimientos (tratamiento del CV y alertas por email) | M |

### CV y perfil
| ID | Requisito | Prioridad |
|---|---|---|
| RF-10 | Subir un CV en PDF o DOCX (máximo 5 MB) | M |
| RF-11 | Extraer con IA un perfil estructurado: datos de contacto, resumen, experiencia, formación, skills, idiomas, ubicación y años de experiencia | M |
| RF-12 | Revisar y editar el perfil extraído | M |
| RF-13 | Gestionar **varias versiones del CV**: crear, renombrar, marcar como principal y archivar | M |
| RF-14 | Definir preferencias de búsqueda: puestos, ubicaciones, modalidad, salario mínimo y fuentes | M |
| RF-15 | **Importar el perfil de LinkedIn** subiendo el PDF que genera LinkedIn ("Más → Guardar en PDF") y crear con él una versión del CV | M |

### Ofertas y matching
| ID | Requisito | Prioridad |
|---|---|---|
| RF-20 | Buscar ofertas en las fuentes activas según las preferencias | M |
| RF-21 | Normalizar las ofertas a un modelo común y eliminar duplicados entre fuentes | M |
| RF-22 | Preseleccionar ofertas por similitud semántica (embeddings) | M |
| RF-23 | Puntuar cada oferta preseleccionada (0–100) con IA, explicando los puntos fuertes y las carencias | M |
| RF-24 | Proponer la versión del CV que mejor encaja con cada oferta | M |
| RF-25 | Listar las ofertas recomendadas con filtros (puntuación, fuente, modalidad, fecha) y la atribución de su origen | M |
| RF-26 | Descartar una oferta o guardarla para después | S |

### Candidaturas
| ID | Requisito | Prioridad |
|---|---|---|
| RF-30 | Generar con IA una carta de presentación personalizada, editable, para copiar o descargar (PDF/DOCX) | M |
| RF-31 | Preparar respuestas a las preguntas del formulario cuando la fuente las proporciona (Greenhouse) | M |
| RF-32 | Sugerir cómo adaptar el CV a cada oferta, sin inventar datos, y crear opcionalmente una versión adaptada | M |
| RF-33 | Mostrar un **enlace directo a la oferta original** para que el usuario envíe allí la candidatura | M |
| RF-34 | Seguimiento manual de candidaturas: estados (guardada, aplicada, entrevista, descartada, oferta recibida), fechas y notas | M |
| RF-35 | Avisar si una oferta guardada ha caducado o ya no está publicada en la fuente | S |

### Alertas, estadísticas y mejora del CV
| ID | Requisito | Prioridad |
|---|---|---|
| RF-40 | Crear, editar y pausar alertas de búsqueda con frecuencia (diaria o semanal) y puntuación mínima | M |
| RF-41 | Ejecutar automáticamente las alertas y puntuar solo las ofertas nuevas | M |
| RF-42 | Enviar un resumen por email con las mejores ofertas y un enlace de baja con un clic | M |
| RF-43 | Panel de estadísticas: distribución de puntuaciones, skills más pedidas frente a las propias, embudo de candidaturas (encontradas → guardadas → aplicadas → entrevistas) y cobertura por fuente | M |
| RF-44 | Estadísticas avanzadas: evolución temporal y comparativa entre versiones del CV | S |
| RF-45 | Sugerencias de mejora del CV basadas en la demanda real de las ofertas (skills que faltan, palabras clave ATS, redacción y logros sin cuantificar), con la oferta que las justifica | M |
| RF-46 | Crear una nueva versión del CV aplicando las sugerencias aceptadas | S |

## 6. Requisitos no funcionales

| ID | Categoría | Requisito |
|---|---|---|
| RNF-01 | Seguridad | Cumplir el OWASP Top 10: contraseñas con argon2, JWT de vida corta en cookie httpOnly, CSRF, rate limiting, validación de entradas y subidas |
| RNF-02 | Privacidad | Cumplir el RGPD y la LOPDGDD según [legal.md](legal.md); los secretos y tokens OAuth se cifran en la BD |
| RNF-03 | Legalidad | Solo fuentes con API autorizada; atribución y enlace al origen; la app nunca actúa en nombre del usuario en sitios de terceros |
| RNF-04 | Rendimiento | La API responde en < 300 ms (p95) sin llamadas a IA; parsear un CV tarda < 20 s; puntuar 20 ofertas tarda < 60 s (en segundo plano, con progreso visible); preparar una carta tarda < 15 s |
| RNF-05 | Coste | Infraestructura y APIs por debajo de 10 €/mes con hasta 20 usuarios activos: Haiku para el volumen, caché, topes por búsqueda y por alerta |
| RNF-06 | Disponibilidad | Despliegue público durante la evaluación; se acepta que el plan gratuito "arranque en frío" (< 60 s) |
| RNF-07 | Mantenibilidad | Arquitectura por capas, fuentes como *adapters*, tipado estricto (mypy y TypeScript), linters en CI |
| RNF-08 | Calidad | Cobertura ≥ 70 % en el backend; tests E2E del flujo principal; CI en verde para fusionar |
| RNF-09 | Usabilidad | Interfaz responsive, accesibilidad WCAG 2.1 AA básica, interfaz en español |
| RNF-10 | Observabilidad | Logs estructurados con id de petición; coste y latencia de cada llamada a la IA |
| RNF-11 | IA responsable | No inventar datos; explicar las puntuaciones; resistir a *prompt injection*; indicar que el contenido es generado por IA |
| RNF-12 | Portabilidad | Arranque local con `docker compose up`; configuración solo por variables de entorno |

## 7. Casos de uso principales

### CU-01 · Encontrar ofertas a partir del CV
1. El candidato sube su CV, o el PDF de su perfil de LinkedIn, y acepta el consentimiento.
2. El sistema extrae el perfil y lo muestra para revisarlo.
3. El candidato corrige lo que haga falta y define sus preferencias.
4. El sistema busca en las fuentes, preselecciona con embeddings y puntúa con Claude.
5. El candidato ve las ofertas ordenadas por encaje, cada una con su explicación.

*Alternativas:*
- **4a.** Una fuente no responde: se continúa con las demás y se avisa de ello.
- **2a.** El CV no se puede leer (por ejemplo, un PDF escaneado): se pide otro archivo o rellenar el perfil a mano.

### CU-02 · Preparar y enviar una candidatura
1. El candidato elige una oferta y pulsa "Preparar candidatura".
2. El sistema propone la versión del CV, genera la carta, prepara las respuestas al formulario (si la fuente las da) y sugiere cómo adaptar el CV.
3. El candidato revisa y edita, y copia o descarga lo que necesite.
4. El candidato pulsa "Ir a la oferta" y envía la candidatura **en la web original**.
5. De vuelta en JobPilot, marca la candidatura como "Aplicada" y, más adelante, actualiza su estado.

*Alternativas:*
- **2a.** La IA no tiene datos suficientes para una respuesta: la deja en blanco y la marca para que el candidato la complete. Nunca inventa.
- **4a.** La oferta ya no está publicada: se avisa y se marca como caducada.

### CU-03 · Recibir alertas diarias
1. El candidato crea una alerta (preferencias, frecuencia y puntuación mínima).
2. Cada día el planificador lanza la búsqueda y se puntúan solo las ofertas nuevas.
3. Si hay ofertas por encima del umbral, se envía un resumen por email.
4. El candidato entra desde el email y sigue el flujo del CU-02.

### CU-04 · Mejorar el CV
1. El candidato abre las sugerencias de una versión de su CV.
2. El sistema analiza las ofertas recogidas y genera sugerencias justificadas y priorizadas.
3. El candidato acepta o descarta cada una.
4. Opcionalmente, crea una nueva versión del CV con las sugerencias aceptadas.

## 8. Modelo de dominio (preliminar)

```
User 1─* CvVersion (origin: upload | linkedin_pdf | tailored) 1─1 CvProfile
User 1─1 Preferences
User 1─* JobAlert 1─* AlertRun
Job (normalizada, con source, external_id, url y embedding) *─* User  →  JobMatch (score, explanation, best_cv_version)
JobMatch 1─0..1 Application (status, cover_letter, form_answers, notes, status_history[])
CvVersion 1─* CvSuggestion
Source (name, enabled, attribution), TrackedCompany (ats, slug)
Consent, AuditLog
```

El diseño detallado (ERD y diagramas de secuencia) se hace en el Sprint 1.

## 9. Riesgos

| ID | Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|---|
| R1 | Las condiciones de las plataformas impiden el envío automático | **Confirmado → resuelto** | — | Se elimina el envío en nombre del usuario ([ADR-0003](adr/0003-sin-envio-automatico.md)) |
| R2 | Cobertura de ofertas insuficiente sin LinkedIn ni InfoJobs | Media | Alto | Agregadores (Adzuna, Jooble) + plataformas de selección con una lista amplia de empresas; medir la cobertura por fuente en la evaluación |
| R3 | Una API de empleo cambia, cae o limita el uso | Media | Medio | Patrón adapter, varias fuentes, caché, tests con mocks |
| R4 | El coste de la IA supera el presupuesto | Baja | Medio | Haiku, filtro previo con embeddings, caché de prompts, topes y alerta de gasto |
| R5 | Calidad del matching insuficiente | Media | Alto | Conjunto de evaluación desde el Sprint 3 e iteración de prompts |
| R6 | Desviación del calendario de 15 semanas | Media | Alto | Tests a la vez que el código; recorte ordenado (RF-44 y RF-46 primero) |
| R7 | *Prompt injection* desde ofertas o CVs | Media | Alto | Separar datos e instrucciones, salida estructurada validada; la IA no tiene herramientas con efectos externos |
| R9 | El formato del PDF de LinkedIn cambia | Media | Bajo | El parsing lo hace la IA (no reglas fijas) y hay tests con varios PDF de ejemplo |
| R8 | Fuga de datos personales | Baja | Muy alto | Cifrado, control de acceso por usuario, tests de autorización, revisión OWASP |
