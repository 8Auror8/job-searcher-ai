# ADR-0003: Sin envío de candidaturas en nombre del usuario; importación de LinkedIn

- **Estado:** Aceptado
- **Fecha:** 13/11/2026
- **Sustituye a:** [ADR-0002](0002-aplicacion-automatica.md)

## Contexto

La revisión legal ([legal.md](../legal.md)) concluyó que:
- Ningún portal real verificado permite que un tercero envíe candidaturas automáticamente dentro de un agregador. Greenhouse y Lever exigen la API key de la empresa y MyGreenhouse prohíbe los bots.
- InfoJobs permite inscribir al candidato con su permiso, pero prohíbe las apps agregadoras.
- LinkedIn prohíbe el scraping y lo persigue judicialmente (por ejemplo, la demanda contra Proxycurl, que cerró en 2025). Sus APIs de empleo no están disponibles para leer ofertas.

Con la ADR-0002, el envío automático real solo funcionaba en un portal de demostración. El agente añadía complejidad (Playwright en el servidor, Gmail OAuth) y riesgo legal sin aportar valor en portales reales.

## Decisión

1. **La IA no envía candidaturas** en nombre del usuario: ni por formulario ni por email. Se eliminan el agente de Playwright, el portal de demostración y la integración con Gmail.
2. **La IA prepara la candidatura** y el usuario la envía en la web original:
   - Carta de presentación personalizada.
   - Respuestas a las preguntas del formulario, cuando la fuente las expone (Greenhouse `?questions=true`).
   - Sugerencias para adaptar el CV a esa oferta.
   - Botón con **enlace directo a la oferta original**.
3. **El seguimiento de candidaturas es manual:** el usuario marca la candidatura como aplicada, en entrevista, descartada u oferta recibida, y puede añadir notas.
4. **Importación de LinkedIn:** el usuario puede subir el PDF de su perfil de LinkedIn ("Guardar en PDF") como alternativa al CV. Son sus propios datos y los aporta él, sin acceder a LinkedIn.
5. **Fuentes:** solo las APIs verificadas en `legal.md`. LinkedIn, Indeed, Glassdoor, InfoJobs y Remotive quedan fuera.
6. **Calendario:** se mantienen las 15 semanas. Las 2 semanas que deja libres el agente se dedican a la importación de LinkedIn, a una evaluación más rigurosa de la IA y a calidad.

## Consecuencias

- ✅ No queda ninguna zona gris legal en el núcleo del producto: la app solo lee APIs autorizadas y nunca actúa en nombre del usuario en sitios de terceros.
- ✅ Arquitectura más simple: no hace falta Chromium en el servidor, lo que elimina el riesgo de memoria del plan gratuito. Tampoco se guardan tokens de Gmail.
- ✅ El RGPD se simplifica: menos datos sensibles y menos encargados del tratamiento.
- ⚠️ Se pierde el componente "agente autónomo". Se compensa con la IA en la preparación de candidaturas y con la evaluación de la calidad (que no invente datos).
- 🔁 **Trabajo futuro:** si InfoJobs autorizara por escrito su integración, se podría añadir la inscripción vía OAuth (permitida por sus condiciones con permiso del usuario en cada oferta).
