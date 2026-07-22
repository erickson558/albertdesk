---
name: debug-release-cycle
description: Ciclo completo de debugging + estabilización + release para AlbertDesk — analizar errores reales, corregirlos sin romper funcionalidad, versionar, recompilar el .exe y publicar. Usar cuando el usuario pida "corrige errores y sube una nueva versión", reporte un bug a arreglar, o pida preparar un release.
---

# Debug → Release Cycle

Este skill es el proceso operativo del agente [[python-qa-devops]]. Seis fases,
en orden, sin saltarse ninguna. Reglas globales en `specs/constitution.md`.

## Regla madre
**No romper funcionalidades. El sistema ya funciona.** Un fix corrige la causa raíz
de UN problema — no es licencia para refactorizar, "mejorar" código no relacionado,
ni añadir features. Ante la duda entre estabilidad y una refactorización agresiva,
gana la estabilidad; explica el trade-off al usuario en vez de decidir en silencio.

## FASE 1 — Análisis (obligatoria, no se salta)
Antes de tocar código:
- Lee el código real de los módulos involucrados (no asumas por el nombre de la
  función). Para proyectos/módulos grandes, delega la lectura a un research agent
  en paralelo (Explore/general-purpose) para no gastar contexto, pero la decisión
  de qué se corrige la tomas tú con evidencia concreta.
- Para cada problema encontrado documenta: archivo:línea, qué es concretamente el
  bug (con el snippet), causa raíz, impacto (qué se rompe, cuándo, qué tan grave),
  y riesgo de corregirlo (bajo/medio/alto — qué tan probable es que el fix rompa
  otra cosa).
- Si el proyecto usa specs (`specs/`), escribe estos hallazgos en un
  `plan.md` bajo `specs/<versión>/` — ver [[spec-driven-change]]. Para fixes
  triviales de una sola línea con causa raíz obvia, no hace falta el spec completo,
  pero sí reportar el análisis al usuario antes de corregir.
- No reportes issues de estilo/preferencia como si fueran bugs. Sólo lo que
  realmente rompe o puede romper comportamiento, seguridad o rendimiento.

## FASE 2 — Corrección
- Aplica el fix mínimo necesario para la causa raíz identificada en fase 1.
- Si el fix toca el protocolo de red entre cliente y servidor
  (`connection_manager.py`), actualiza ambos lados en el mismo cambio.
- Mejora manejo de errores/validaciones sólo donde el bug lo requiere, no como
  barrido general.
- Sigue [[code-annotate]] para comentarios: por qué, no qué.

## FASE 3 — Validación
Antes de dar por corregido:
- `python -m py_compile <archivos tocados>` como mínimo (sintaxis + errores de
  import a nivel de módulo).
- Si hay tests automatizados, córrelos. Si no los hay, no los inventes de la nada
  salvo que el usuario lo pida explícitamente — no es parte de este ciclo.
- Repasa mentalmente cada funcionalidad que toca el código modificado y confirma
  que el comportamiento anterior se preserva (no sólo el caso del bug).
- Para cambios de UI/PyQt5 que no puedas probar de forma headless, dilo
  explícitamente al usuario en vez de asumir que "funciona" — recomienda una
  prueba manual rápida.

## FASE 4 — Versionado
- Determina el incremento: patch (fix), minor (mejora/feature compatible), major
  (cambio incompatible/rediseño). Por defecto es patch — justifica si no lo es.
- Formato `x.y.z` (texto plano, sin prefijo de letra), coherente en TODOS estos
  archivos a la vez:
  - `main.py` (`__version__`)
  - `albertdesk/__init__.py` (`__version__`)
  - `setup.py` (`version=`)
  - Badge de versión en `README.md`
  - Nueva sección en `CHANGELOG.md` (formato Keep a Changelog, ya usado en el repo)

## FASE 5 — Commit
- Mensaje estilo conventional commit, en la línea de lo ya usado en este repo
  (`git log --oneline`): `fix: ...`, `feat: ...`, `security: ...`, terminando con
  `(Vx.y.z)` (mayúscula, sólo cosmético en el texto del commit — no confundir con
  el tag de git, ver FASE 6). Ejemplo real del historial:
  `fix: resolve connection_lost not emitted on server drop, ... (V1.3.1)`.
- Un solo commit por ciclo salvo que el usuario pida separarlo.

## FASE 6 — Push y release
- Usa la skill [[github-release]] para el push/tag — nunca improvises comandos de
  git/gh distintos a los ahí documentados, esa skill fija la cuenta correcta
  (`erickson558`), el repo (`erickson558/albertdesk`) **y el casing correcto del
  tag** (`vX.Y.Z` minúscula — el trigger de GitHub Actions es case-sensitive y un
  tag en mayúscula se pushea sin error pero no dispara el release; verifica
  siempre con `gh run list` después de pushear el tag, nunca asumas que corrió).
- Si el cambio incluye recompilar el `.exe`, hazlo con `python build.py` ANTES del
  commit (o justo después, pero antes del push) para que el build local quede
  consistente con el código commiteado — el `.exe` en sí no se commitea
  (está en `.gitignore`), pero debe existir localmente y compilar sin errores antes
  de dar el ciclo por terminado.

## Entregables al usuario (siempre en este orden)
1. Análisis de errores — lista, causa raíz, impacto
2. Cambios realizados — qué y cómo
3. Nueva versión — número y justificación
4. Resumen de validación
5. Mensaje de commit
6. Comandos de git/gh ejecutados con una frase de qué hace cada uno
