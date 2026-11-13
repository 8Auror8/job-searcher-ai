# Revisión legal y protección de datos

> Sprint 0 · Versión 1.0 · 13/11/2026
> Este documento **no es asesoramiento jurídico**. Recoge la revisión de condiciones de uso realizada para el TFM y las decisiones de diseño derivadas. Las condiciones de terceros pueden cambiar: se revisarán de nuevo antes de la entrega (Sprint 6).

## 1. Principios que guían el proyecto

1. **Solo fuentes que permiten el acceso automatizado** (API oficial o condiciones que lo autoricen). Nada de scraping de LinkedIn, Indeed u otras webs que lo prohíban.
2. **Humano en el bucle:** ninguna candidatura se envía sin la aprobación explícita del usuario, oferta a oferta.
3. **Nunca se eluden controles:** ni CAPTCHAs, ni logins, ni límites de uso. Si aparecen, el flujo se detiene y pasa a manual.
4. **Atribución y enlace al origen** en todas las ofertas mostradas.
5. **Privacidad desde el diseño** (art. 25 RGPD): mínimos datos, cifrado, borrado real.

## 2. Revisión de fuentes de ofertas

| Fuente | Acceso | Lo que dicen sus condiciones | Decisión |
|---|---|---|---|
*Revisión ampliada el 13/11/2026 con la documentación oficial de cada fuente. Leyenda: ✅ confirmado en fuente oficial · 🟡 utilizable con reservas o pendiente de confirmar · ❌ no utilizable.*

### 2.1 Agregadores y portales de empleo

| Fuente | Acceso | Lo que dice la documentación oficial | Decisión |
|---|---|---|---|
| **Adzuna API** | API key gratuita | Hay dos versiones de las condiciones. La del portal de desarrolladores permite cualquier uso tras un periodo de prueba de 14 días. La del PDF de enero de 2026 solo permite publicar ofertas, publicar estimaciones salariales y la investigación personal o de grado; el uso comercial requiere acuerdo previo. Exige un badge de atribución con enlace y prohíbe contactar con los proveedores de contenido de Adzuna. | ✅ **Usar** (proyecto académico, sin ánimo de lucro) con el badge "Jobs by Adzuna". Pendiente: confirmar el uso académico por email. |
| **Jooble API** | API key mediante formulario | Dirigida a webmasters de portales o buscadores que quieran mostrar resultados de Jooble en su web. La página no indica precio ni límites, y las condiciones están en otra página que no se ha leído. | 🟡 **Solicitar key** y revisar las condiciones al recibirla. |
| **Arbeitnow API** | Pública, sin key | Gratuita y abierta. Se pide enlazar al origen. | ✅ **Usar** con enlace a la oferta original. |
| **Jobicy API** | Pública, sin key | Permite expresamente agregadores, productos de IA y uso comercial. Obliga a atribuir la fuente, a enlazar a la página original de Jobicy y a no sincronizar más de una vez por hora. | ✅ **Usar.** |
| **Himalayas API** | Pública; key gratuita opcional | Permite expresamente alimentar buscadores y agentes de IA. Obliga a enlazar al origen, a no modificar el enlace de candidatura y a no pasar las ofertas a otros portales, agregadores ni Google Jobs. Con key: 60 peticiones por minuto. | ✅ **Usar** solo dentro de la app, sin exponer las ofertas a otros sitios. |
| **RemoteOK API** | Pública, sin key | Obliga a citar a RemoteOK como fuente y a enlazar a cada oferta sin `nofollow`. No se puede usar su logo sin permiso. | ✅ **Usar** con atribución y enlace. |
| **InfoJobs API** | Registro de app de desarrollador + OAuth2 del candidato | Las condiciones de uso de la API (versión de noviembre de 2012, facilitadas por el usuario) dicen: **✅ inscribir al usuario en ofertas está permitido** si se le pide permiso siempre antes de hacerlo. **❌ Pero prohíben** las "aplicaciones que sean agregadores de ofertas", las que "promocionen servicios de la competencia", las que compitan con el modelo de negocio de InfoJobs y las que tengan como función principal sacar a los candidatos de InfoJobs. Además, almacenar datos de InfoJobs exige el programa de Partners (gestiondatos@infojobs.net). | ❌ **No se puede integrar como una fuente más en un agregador** sin autorización escrita de InfoJobs. Pendiente de la decisión sobre el alcance (ver sección 3.1). |
| **Remotive API** | Pública, sin key | Según fuentes secundarias: unas 4 consultas al día como máximo, ofertas con 24 h de retraso y prohibición de pasar sus ofertas a terceros. | ❌ **Excluir.** |
| LinkedIn / Indeed / Glassdoor | — | Prohíben expresamente el scraping y los bots. | ❌ **Fuera del alcance.** |

### 2.2 Plataformas de selección de empresas (ATS)

Estas APIs se consultan **empresa por empresa** (no permiten buscar en todas las empresas de la plataforma a la vez), así que hace falta mantener una lista de empresas objetivo.

| Fuente | Acceso | Lo que dice la documentación oficial | Decisión |
|---|---|---|---|
| **Greenhouse Job Board API** | GET público | Los GET son públicos y `?questions=true` devuelve los campos del formulario. El POST para enviar candidaturas exige la API key de la empresa. | ✅ **Leer ofertas y preguntas.** ❌ Envío por API. |
| **Lever Postings API** | GET público | La documentación dice expresamente que las ofertas publicadas son visibles públicamente y que "pueden ser extraídas por terceros". El *apply* exige una key emitida por la empresa. | ✅ **Leer ofertas.** ❌ Envío por API. |
| **Ashby Job Posting API** | GET público (sin key en los ejemplos) | Pensada para que la empresa alimente su propia página de empleo. No menciona condiciones ni límites. La candidatura se hace en su `applyUrl`. | 🟡 **Leer ofertas** con poca frecuencia y enlace al origen. |
| **Personio (feed XML)** | Feed público por empresa | Pensado para integrar las ofertas en la web de la empresa. Sin condiciones publicadas. Muchos clientes europeos. | 🟡 **Leer ofertas** con poca frecuencia y enlace al origen. |
| **Recruitee Careers Site API** | No consta | La documentación es incompleta: no aclara autenticación ni condiciones. | 🟡 Verificar antes de integrar. |
| **Workable (endpoint del widget)** | Público, pero sin documentación oficial encontrada | Solo hay fuentes de terceros; puede cambiar sin aviso. | 🟡 Opcional, de última prioridad. |
| **SmartRecruiters Posting API** | API key u OAuth del **cliente** | Pensada para que los clientes construyan su propia página de empleo. | ❌ No accesible sin ser cliente. |

### 2.3 Resumen

- **7 fuentes confirmadas** en documentación oficial: Adzuna, Arbeitnow, Jobicy, Himalayas, RemoteOK, Greenhouse y Lever.
- **6 utilizables con reservas o pendientes de confirmar:** Jooble, InfoJobs, Ashby, Personio, Recruitee y Workable.
- **Descartadas:** SmartRecruiters, Remotive, LinkedIn, Indeed y Glassdoor.

## 3. Aplicación automática: hallazgo clave

> **Decisión final ([ADR-0003](adr/0003-sin-envio-automatico.md), 13/11/2026):** JobPilot **no envía candidaturas en nombre del usuario**. La IA prepara la candidatura y el usuario la envía en la web original. Para LinkedIn solo se usa el PDF que el usuario descarga y sube, porque LinkedIn prohíbe el scraping y lo persigue judicialmente (por ejemplo, la demanda contra Proxycurl, que cerró en julio de 2025). Esta sección se conserva como registro del análisis que llevó a esa decisión.

La idea original era que un agente con IA rellenara y **enviara** directamente el formulario de la oferta. La revisión muestra que:

- Los portales de empresa (Greenhouse, Lever) **solo admiten el envío programático con una API key que pertenece a la empresa**. No están pensados para que un tercero envíe candidaturas en nombre de candidatos.
- El acuerdo de usuario de **MyGreenhouse** (cuenta de candidato) prohíbe acceder o usar el servicio por medios automatizados (*spiders, robots, crawlers*). No aclara si la prohibición alcanza a los portales públicos de empleo, así que, por prudencia, se trata como **no permitido**.
- Además, varias empresas reportan problemas con candidaturas enviadas por bots, que es justo el riesgo reputacional que queremos evitar.

**Decisión (ver [ADR-0002](adr/0002-aplicacion-automatica.md)):** el agente se construye completo, pero el modo de envío depende de cada plataforma:

| Modo | Cuándo | Qué hace la IA |
|---|---|---|
| **Automático** | Plataformas con permiso explícito: el **portal ATS de demostración del propio proyecto** y, en el futuro, empresas que se den de alta voluntariamente. | El agente (Playwright + Claude) rellena el formulario, muestra un resumen, el usuario confirma y se envía. Se guarda captura y log. |
| **Asistido** | Greenhouse, Lever y cualquier plataforma sin permiso confirmado. | Lee los campos del formulario por la API pública (Greenhouse `?questions=true`), Claude prepara todas las respuestas y la carta, y el usuario abre el formulario oficial con todo listo para copiar y enviar él mismo. |
| **Email** | La oferta incluye un contacto de candidatura. | Envía el CV y la carta generada desde el Gmail del usuario (OAuth, permiso `gmail.send`), tras aprobación. |

Cada plataforma tiene un indicador `auto_submit_allowed` en la configuración, que **solo se activa tras una revisión legal documentada**.

### 3.1 InfoJobs: única vía encontrada de envío automático legal

Las condiciones de uso de la API de InfoJobs exigen "pedir permiso siempre al usuario antes de inscribirle a una oferta". Es decir, **permiten que una app inscriba al candidato** en nombre propio vía OAuth, con su permiso para cada oferta. Esto encaja exactamente con el flujo de aprobación de JobPilot.

El conflicto es que las mismas condiciones prohíben las apps que agregan ofertas o promocionan a la competencia, y JobPilot es, por diseño, un agregador multifuente. Se plantean tres opciones:
1. **Excluir InfoJobs** y mantener el agregador multifuente.
2. **Pedir autorización expresa** a InfoJobs (programa de Partners) para integrarlo como fuente con inscripción.
3. **Reorientar el proyecto a InfoJobs como fuente única**, con matching por IA e inscripción automática legal.

Crear una app "para InfoJobs" separada pero conectada al agregador **se descarta**, porque eludiría el espíritu de las condiciones.

## 4. Protección de datos (RGPD / LOPDGDD)

| Aspecto | Medida |
|---|---|
| Base jurídica | Consentimiento explícito (art. 6.1.a) al subir el CV o el PDF de LinkedIn y al activar alertas por email. Es granular y revocable. |
| Datos tratados | Identificación y contacto, CV (formación, experiencia, skills), preferencias, historial de candidaturas. **No** se piden datos de categorías especiales; las preguntas demográficas opcionales de los formularios nunca las rellena la IA. |
| Minimización | Solo se extrae del CV lo necesario para el matching. Los logs no guardan el contenido del CV. |
| Encargados del tratamiento | Anthropic (Claude API), Voyage AI (embeddings), Neon (BD), Render y Vercel (hosting) y Resend (email). Google solo interviene en el login y no recibe datos del CV. Todos se documentan en la política de privacidad, incluidas las transferencias internacionales. |
| Derechos | Acceso y portabilidad (exportar en JSON), rectificación (perfil editable) y supresión (borrar cuenta, CVs, embeddings y tokens). |
| Conservación | Los CVs se conservan mientras la cuenta esté activa; las cuentas inactivas se avisan a los 12 meses y se borran a los 13. |
| Decisiones automatizadas (art. 22) | La IA **recomienda**; la decisión de aplicar es siempre del usuario. La puntuación de encaje va acompañada de una explicación. |
| Comunicaciones (LSSI) | Los emails de alertas requieren alta voluntaria e incluyen baja con un clic (enlace firmado). |
| Seguridad (art. 32) | Ver `docs/seguridad.md` (Sprint 1): cifrado en tránsito y en reposo, y control de acceso por usuario. |

## 5. Uso responsable de la IA

- La IA **nunca inventa** experiencia, títulos ni datos: el prompt lo prohíbe y la evaluación lo comprueba.
- Las cartas y respuestas generadas se muestran **siempre** antes de enviarse y son editables.
- El texto de ofertas y CVs se trata como **dato, no como instrucciones**, para evitar *prompt injection*.
- Se informa al usuario de que el contenido está generado por IA (transparencia, Reglamento Europeo de IA).

## 6. Tareas legales pendientes

- [x] **InfoJobs:** queda fuera del alcance (ADR-0003). Trabajo futuro: pedir autorización a gestiondatos@infojobs.net.
- [ ] Escribir a Adzuna para confirmar el uso académico y los límites de llamadas.
- [ ] Solicitar la API key de Jooble y revisar sus condiciones.
- [ ] Confirmar la autenticación y las condiciones de Recruitee, y si Ashby y Personio admiten la lectura por terceros.
- [ ] Redactar la política de privacidad y los textos de consentimiento (Sprint 5).
- [ ] Revisión final de todas las condiciones (Sprint 6).

## Fuentes consultadas

- [Adzuna – Terms of service](https://developer.adzuna.com/docs/terms_of_service)
- [Greenhouse – Job Board API](https://docs.greenhouse.io/job-board.html)
- [MyGreenhouse User Agreement](https://my.greenhouse.io/users/agreement)
- [Lever API guide (100hires)](https://100hires.com/lever-api.html)
- [Arbeitnow – Job Board API](https://www.arbeitnow.com/blog/job-board-api)
- [Remotive – Public API](https://remotive.com/remote-jobs/api)
- [Free job APIs in 2026 (jobspipe)](https://jobspipe.dev/blog/free-job-api)
- [Jooble – REST API documentation](https://jooblehelpcenter.freshdesk.com/en/support/solutions/articles/60001448238-rest-api-documentation)
- [Jooble – API](https://jooble.org/api/about)
- [InfoJobs – portal de desarrolladores](https://developer.infojobs.net/) · [lista de operaciones](https://developer.infojobs.net/documentation/operation-list/index.xhtml) · [OAuth2 de usuario](https://developer.infojobs.net/documentation/user-oauth2/index.xhtml)
- [Lever – Postings API (GitHub oficial)](https://github.com/lever/postings-api)
- [Ashby – Public Job Posting API](https://developers.ashbyhq.com/docs/public-job-posting-api)
- [SmartRecruiters – Posting API](https://developers.smartrecruiters.com/docs/posting-api)
- [Personio – Retrieving open job positions](https://developer.personio.de/docs/retrieving-open-job-positions)
- [Recruitee – Careers Site API](https://docs.recruitee.com/reference/intro-to-careers-site-api)
- [Himalayas – API](https://himalayas.app/api)
- [Jobicy – Jobs API](https://jobicy.com/jobs-rss-feed)
- [RemoteOK – API](https://remoteok.com/api)
