---
name: spec-driven-change
description: Aplica Spec-Driven Development a AlbertDesk — escribe spec/plan/tasks en specs/ ANTES de implementar cualquier cambio no trivial (feature nueva, fix de riesgo medio/alto, refactor). Usar cuando el usuario pida una funcionalidad nueva, un cambio arquitectónico, o diga explícitamente "aplica SDD" / "sigue el spec-driven development".
---

# Spec-Driven Development para AlbertDesk

Este proyecto sigue SDD: **el spec se escribe antes que el código**, vive en el repo
junto al código (`specs/`), y es la fuente de verdad de "qué se decidió y por qué" —
no un documento desechable. Las reglas globales del proyecto están en
`specs/constitution.md`; léelo primero, tus decisiones no pueden contradecirlo.

## Cuándo usar este flujo completo vs. cuándo no
- **Sí**: nueva funcionalidad visible al usuario, cambio de protocolo de red, cambio
  de arquitectura, cambio de licencia/infraestructura del repo, cualquier cosa que
  toque más de un módulo de forma no obvia.
- **No hace falta el spec completo**: un typo, un ajuste de estilo, un bug de una
  línea con causa raíz obvia — para bugs usa mejor [[debug-release-cycle]], que ya
  incluye su propio análisis de causa raíz (equivalente a un mini-spec).

## Estructura de un spec
Crea `specs/<versión-o-slug-descriptivo>/`:

1. **`spec.md`** — QUÉ y POR QUÉ, nunca CÓMO:
   - Contexto: por qué se necesita este cambio ahora.
   - Requisitos: lista verificable de lo que debe cumplirse.
   - Fuera de alcance: qué NO se va a hacer en este cambio y por qué (evita que
     "mientras estamos aquí" se convierta en scope creep).
   - Criterio de aceptación: cómo se sabe que terminó.

2. **`plan.md`** — CÓMO, con el análisis de causa raíz si aplica:
   - Diseño técnico: qué archivos cambian y por qué esa es la forma correcta.
   - Si hay alternativas descartadas, una línea de por qué se descartaron.
   - Orden de implementación (qué depende de qué).

3. **`tasks.md`** — checklist accionable derivado de `plan.md`, con casillas
   `- [ ]` que se van marcando `- [x]` a medida que se completa cada una. Este
   archivo es lo que sobrevive entre sesiones de Claude Code — si el trabajo se
   interrumpe, la próxima sesión retoma leyendo `tasks.md`, no adivinando.

## Reglas
- No escribas código de la feature hasta tener `spec.md` con requisitos y "fuera de
  alcance" explícitos — la sección "fuera de alcance" es tan importante como los
  requisitos, es lo que evita sobre-ingeniería.
- Si durante la implementación descubres que el plan estaba mal, actualiza `plan.md`
  (no lo dejes desactualizado) y explica el cambio en `tasks.md` bajo una nota, no
  lo escondas.
- Al terminar, añade una línea en `specs/constitution.md` § "Historial de specs"
  apuntando al nuevo spec.
- Enlaza specs relacionados con `[[nombre-de-carpeta]]` en vez de repetir contenido.
