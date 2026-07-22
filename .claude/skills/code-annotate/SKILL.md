---
name: code-annotate
description: Explica y/o comenta qué hace cada parte del código de AlbertDesk. Usar cuando el usuario pida entender un archivo/función, pida "comenta el código", o pida un mapa general del proyecto (arquitectura, módulos, quién llama a quién).
---

# Explicar y comentar el código de AlbertDesk

Objetivo: que cualquiera (incluido el propio usuario en 6 meses) pueda abrir un
archivo y entender qué hace sin tener que releer todo el proyecto.

## Dos modos, no los mezcles sin que te lo pidan
1. **Explicar (por defecto, no modifica archivos)**: responde en el chat qué hace
   el código, con cita `archivo:línea`. Usa este modo salvo que el usuario diga
   explícitamente "coméntalo en el código" / "agrega comentarios".
2. **Comentar en el código (modifica archivos)**: sólo cuando se pida explícitamente,
   o cuando acabas de escribir/tocar código nuevo cuyo PORQUÉ no es obvio.

## Mapa de referencia del proyecto
Antes de explicar nada, orienta con `docs/ARCHITECTURE.md` (qué hace cada carpeta:
`backend/core`, `backend/network`, `frontend/ui`, `frontend/widgets`, `i18n`) y
confirma contra el código real — si el doc quedó desactualizado, dilo y corrígelo.

## Reglas para comentarios inline (cuando sí tocas código)
- Comenta el **PORQUÉ**, nunca el QUÉ. `# incrementa el contador` sobre `x += 1` es
  ruido — bórralo si lo ves. Un comentario vale la pena sólo si sin él un lector
  razonable se equivocaría o se confundiría (invariante no obvio, workaround de un
  bug específico de una librería/API, decisión de concurrencia, por qué NO se hizo
  la alternativa obvia).
- Docstrings: este proyecto ya tiene el estilo Google-style con `Args:`/`Returns:` en
  casi todas las funciones de `albertdesk/` — síguelo, no inventes otro formato.
  Si una función pública no tiene docstring, agrégale una en ese estilo.
- No escribas párrafos. Una o dos líneas por comentario, salvo un docstring de módulo
  que resuma su propósito en 2-3 líneas.
- Nunca dupliques en el comentario lo que el nombre de la variable/función ya dice.
- Idioma: sigue la convención existente del archivo (este proyecto comenta
  mayormente en español, con nombres de identificadores en inglés). No mezcles.

## Al explicar módulos de red/concurrencia (el punto más confuso del proyecto)
Aclara siempre:
- Qué corre en el hilo principal de Qt (UI) vs. en `threading.Thread` de fondo.
- Qué señales (`pyqtSignal`) cruzan ese límite de hilos y por qué eso es seguro
  (Qt encola la entrega de señales al hilo dueño del receptor).
- Qué estado es compartido entre hilos (`self.socket`, `self.is_connected`,
  `self._receiving_files`, `self.tunnel_process`) y qué garantías (o falta de ellas)
  existen sobre acceso concurrente — ver `specs/constitution.md` § Seguridad y los
  hallazgos de `specs/1.3.2-stability-and-security/plan.md` para el estado actual.

## Al explicar algo con implicaciones de seguridad
Sé preciso sobre qué está mitigado y qué es limitación conocida — no digas "es
seguro" ni "es inseguro" en abstracto. Ver `SECURITY.md`.
