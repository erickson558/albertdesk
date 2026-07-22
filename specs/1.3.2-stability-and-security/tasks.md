# Tasks: v1.3.2

- [x] Infraestructura SDD: `specs/constitution.md`, este spec/plan/tasks
- [x] Agentes: `.claude/agents/python-qa-devops.md`, `.claude/agents/code-explainer.md`
- [x] Skills: `spec-driven-change`, `code-annotate`, `debug-release-cycle`, `github-release`
- [x] Fix #1 RCE pickle → `safe_pickle_loads` en `utils.py` + uso en `connection_manager.py`
- [x] Fix #2 path traversal en recepción de archivos
- [x] Fix #3 DoS por tamaño no acotado en handshake de auth
- [x] Fix #4 short-read en handshake de auth (`recv_exact`)
- [x] Fix #5 widget huérfano al salir de pantalla completa
- [x] Fix #6 envío de archivo bloqueando la GUI
- [x] Fix #7 guarda contra conexiones entrantes concurrentes
- [x] Fix #8 comparación de password con `hmac.compare_digest`
- [x] Fix #9 carrera de hilos en captura de URL del tunnel
- [x] Fix #10 DPI awareness per-monitor v2 con fallback
- [x] Licencia MIT → Apache License 2.0 (LICENSE, README, setup.py)
- [x] `CHANGELOG.md`: backfill 1.3.0/1.3.1 + nueva sección 1.3.2
- [x] `README.md` actualizado (licencia, versión, dependencias, donación, i18n, arquitectura)
- [x] `SECURITY.md` nuevo (política de seguridad + limitaciones conocidas documentadas)
- [x] `docs/ARCHITECTURE.md` nuevo (qué hace cada módulo del proyecto)
- [x] Version bump a `1.3.2` en `main.py`, `albertdesk/__init__.py`, `setup.py`
- [x] Validación: `py_compile` de módulos tocados sin errores
- [x] `build.py` ejecutado → `AlbertDesk.exe` regenerado en la raíz
- [x] Commit convencional + tag `v1.3.2` + push a `origin main` y al tag (cuenta `erickson558`)
- [x] Verificado con `gh run list`/`gh release view` que el GitHub Release v1.3.2 se
      creó correctamente con `AlbertDesk.exe` adjunto

## Hallazgo durante el release (importante, ya corregido)
Se pusheó primero un tag `V1.3.2` (mayúscula, siguiendo lo que parecía ser la
convención de los tags locales `V1.3.0`/`V1.3.1` de un ciclo anterior). El tag se
pusheó sin error pero **no disparó** `.github/workflows/release.yml` — su trigger es
`on.push.tags: 'v*.*.*'`, y los patrones de tag de GitHub Actions son
case-sensitive. No hubo ningún mensaje de error; la única señal fue que
`gh run list` no mostraba ningún run nuevo. Se corrigió borrando el tag remoto y
local y re-creando `v1.3.2` en minúscula, que sí disparó el release correctamente
(run exitoso, release publicado con `AlbertDesk.exe` adjunto).

Conclusión: los tags `V1.3.0`/`V1.3.1` que quedaron sólo locales de un ciclo
anterior tenían el mismo problema de casing y **tampoco hubieran disparado el
release** si se hubiesen pusheado tal cual — no era una convención válida, era un
error que nunca se detectó porque esos tags nunca llegaron a `origin`. La
convención correcta y ya corregida en `specs/constitution.md` y
`.claude/skills/github-release/SKILL.md`: los números de versión en archivos van
sin prefijo (`1.3.2`), el tag de git va en minúscula (`v1.3.2`).

Nota aparte (no bloqueante, ya resuelta): los 4 runs históricos del workflow
(v1.1.0 a v1.2.2, de 2026-03-02/03) habían fallado todos en el paso "Build
executable" — sus logs ya expiraron (>90 días) así que no se pudo confirmar la
causa exacta, pero el run de v1.3.2 con el `build.py` ya mejorado (auto-detección
de `.venv`, `check_dependencies`, `--hidden-import PyQt5.sip` del commit
`c8eb036`) completó ese mismo paso sin problema. Si un futuro release vuelve a
fallar en "Build executable", diagnosticar con `gh run view <id> --log-failed`
INMEDIATAMENTE (antes de que expiren los logs), no asumir que ya está resuelto.

## Notas para la próxima sesión
- TLS/cifrado end-to-end del protocolo P2P sigue pendiente como ítem de roadmap
  (ver `SECURITY.md`), sería un cambio de versión major.
- Idiomas adicionales a ES/EN: el framework lo soporta trivialmente
  (`albertdesk/i18n/__init__.py`), pendiente si el usuario lo pide.
