# Tasks: V1.3.2

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
- [x] `CHANGELOG.md`: backfill V1.3.0/V1.3.1 + nueva sección V1.3.2
- [x] `README.md` actualizado (licencia, versión, dependencias, donación, i18n, arquitectura)
- [x] `SECURITY.md` nuevo (política de seguridad + limitaciones conocidas documentadas)
- [x] `docs/ARCHITECTURE.md` nuevo (qué hace cada módulo del proyecto)
- [x] Version bump a `1.3.2` en `main.py`, `albertdesk/__init__.py`, `setup.py`
- [x] Validación: `py_compile` de módulos tocados sin errores
- [x] `build.py` ejecutado → `AlbertDesk.exe` regenerado en la raíz
- [x] Commit convencional + tag `V1.3.2` + push a `origin main` y al tag (cuenta `erickson558`)

## Notas para la próxima sesión
- Los tags `V1.3.0`/`V1.3.1` existen solo localmente (nunca se pushearon). Se decidió
  no publicarlos retroactivamente — ver "Fuera de alcance" en `spec.md`.
- TLS/cifrado end-to-end del protocolo P2P sigue pendiente como ítem de roadmap
  (ver `SECURITY.md`), sería un cambio de versión major.
- Idiomas adicionales a ES/EN: el framework lo soporta trivialmente
  (`albertdesk/i18n/__init__.py`), pendiente si el usuario lo pide.
