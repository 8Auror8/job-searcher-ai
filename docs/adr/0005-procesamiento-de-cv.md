# ADR-0005: Procesamiento del CV con IA

- **Estado:** Aceptado
- **Fecha:** 13/11/2026 (Sprint 2)

## Contexto

El usuario sube su CV (PDF o DOCX) o el PDF de su perfil de LinkedIn, y la IA lo convierte en un perfil estructurado. El CV contiene datos personales y el resultado de la IA no puede inventar información (RNF-11).

## Decisión

1. **No se guarda el archivo original.** Solo se guarda el texto extraído (necesario para volver a analizarlo y, en el Sprint 3, para el matching) y el perfil estructurado. Es una medida de minimización de datos (art. 5.1.c del RGPD): no hay archivos en disco ni en almacenamiento externo.
2. **Lectura segura del documento:**
   - El tipo de archivo se detecta por sus bytes y no por su nombre.
   - Límites: 5 MB, 20 páginas y 60.000 caracteres.
   - Se detectan las bombas zip en los DOCX.
   - Si el texto es demasiado largo se rechaza; **nunca se trunca en silencio**.
3. **Extracción con Claude mediante salidas estructuradas** (`messages.parse` con un modelo Pydantic):
   - Todos los campos son obligatorios y admiten `null`, para que el modelo pueda decir "no está en el CV" en lugar de inventar.
   - El modelo por defecto es `claude-haiku-5-5`, por ser una tarea de volumen y coste bajo (ADR-0001). Se puede configurar con `AI_MODEL_EXTRACTION`.
4. **Prompt versionado** en `backend/app/prompts/cv_extraction_v1.md`. El CV va dentro de `<cv_document>` y se trata como dato, no como instrucciones; se escapa cualquier intento de cerrar la etiqueta.
5. **Comprobación de anclaje (*grounding*):**
   - Cada habilidad, empresa, centro de estudios y certificación que devuelve la IA tiene que aparecer literalmente en el texto del CV. La comparación ignora mayúsculas, acentos y signos, y exige palabras completas.
   - Lo que no aparece **se retira del perfil** y se muestra al usuario como "propuesto pero no verificado", para que decida si lo añade.
6. **La IA es opcional:** sin `ANTHROPIC_API_KEY`, o si la IA falla, la versión del CV se crea igualmente y el usuario rellena el perfil a mano. Después puede reintentar el análisis.
7. **Control de coste y uso:**
   - Cada llamada se registra en `ai_usage` con el modelo, los tokens, la latencia y si tuvo éxito.
   - Límite de `AI_DAILY_CALLS_PER_USER` llamadas al día por usuario (20 por defecto), más un rate limit por IP en la subida.
8. **Consentimiento explícito** antes del primer análisis, registrado en `consents` con la versión de la política (art. 7 del RGPD).

## Consecuencias

- ✅ Menos datos personales almacenados y ningún archivo que proteger.
- ✅ La IA no puede introducir habilidades o empresas inexistentes sin que el usuario lo vea.
- ✅ La app funciona sin clave de IA (desarrollo, demo y tests).
- ⚠️ El usuario no puede volver a descargar su archivo original desde la app.
- ⚠️ El anclaje es estricto: si el CV dice "JS" y la IA normaliza a "JavaScript", se marca como no verificado. El prompt pide copiar los términos tal cual para reducirlo.
- ⚠️ El texto de PDFs escaneados (imágenes) no se puede leer. El usuario recibe un mensaje claro y puede crear el perfil a mano.
