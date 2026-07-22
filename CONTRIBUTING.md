# Contribuir a AlbertDesk

¡Gracias por tu interés en contribuir! Esta guía resume el flujo de trabajo esperado.

## Antes de empezar
- Para cambios no triviales (features, cambios de arquitectura/protocolo), este
  proyecto sigue Spec-Driven Development: escribe primero un spec en
  `specs/<nombre>/spec.md` (contexto, requisitos, fuera de alcance, criterio de
  aceptación) antes de escribir código. Ver `specs/constitution.md` y la skill
  `.claude/skills/spec-driven-change/SKILL.md`.
- Para bugs, sigue el proceso de `.claude/skills/debug-release-cycle/SKILL.md`:
  analiza la causa raíz antes de corregir, no rompas funcionalidad existente.

## Flujo de contribución
1. Haz fork del repositorio.
2. Crea una rama descriptiva: `git checkout -b feature/mi-cambio` o `fix/mi-bug`.
3. Sigue el estilo del código existente: docstrings estilo Google
   (`Args:`/`Returns:`), comentarios en español explicando el *por qué* (no el qué),
   type hints en las firmas de función.
4. Si tu cambio agrega texto visible en la UI, añádelo a **ambos** diccionarios de
   `albertdesk/i18n/__init__.py` (`es` y `en`) — nunca lo dejes hardcodeado.
5. Valida que el proyecto compila y arranca:
   ```bash
   python -m py_compile $(git diff --name-only --diff-filter=ACM -- '*.py')
   python main.py
   ```
6. Commit con formato [Conventional Commits](https://www.conventionalcommits.org/):
   `fix: ...`, `feat: ...`, `docs: ...`, `security: ...`.
7. Abre un Pull Request describiendo qué cambia y por qué.

## Reportar bugs
Abre un [issue](https://github.com/erickson558/albertdesk/issues) con: qué esperabas
vs. qué pasó, pasos para reproducir, logs de la carpeta `logs/` si aplica, tu sistema
operativo y versión de AlbertDesk.

## Seguridad
Si encuentras una vulnerabilidad, por favor repórtala de forma privada en vez de
abrir un issue público — ver [SECURITY.md](SECURITY.md).

## Licencia
Al contribuir, aceptas que tu contribución se licencie bajo la [Apache License 2.0](LICENSE)
de este proyecto.
