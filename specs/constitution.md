# AlbertDesk — Constitution (Spec-Driven Development)

Este documento define las reglas no negociables del proyecto. Todo cambio no trivial
(feature, fix de riesgo medio/alto, refactor) debe pasar primero por un spec en
`specs/<version-o-slug>/spec.md` antes de tocar código. Ver [[spec-driven-change]] skill.

## 1. Compatibilidad ante todo
- Nunca romper una funcionalidad existente para arreglar otra.
- Un fix de bug no es licencia para refactorizar código no relacionado.
- Si una corrección requiere cambiar el protocolo de red (formato de mensajes entre
  cliente/servidor), ambos lados (`connection_manager.py` server y client) deben
  actualizarse juntos en el mismo cambio — son un único despliegue (misma versión
  del `.exe` en ambos extremos), no hay compatibilidad hacia atrás entre versiones
  de protocolo distintas.

## 2. Versionado semántico (SemVer) — formato `x.y.z`
- **Major (X)**: cambios incompatibles o rediseño de arquitectura/protocolo.
- **Minor (Y)**: nuevas funcionalidades compatibles hacia atrás.
- **Patch (Z)**: bug fixes, hardening de seguridad, mejoras internas sin nueva feature.
- La versión debe coincidir SIEMPRE en: `main.py` (`__version__`), `albertdesk/__init__.py`,
  `setup.py`, badge de `README.md` y `CHANGELOG.md` — todos como texto plano `x.y.z`,
  SIN prefijo de letra (p. ej. `1.3.2`, no `V1.3.2`).
- El **tag de git es distinto y debe ser `vX.Y.Z` con "v" MINÚSCULA** —
  `.github/workflows/release.yml` sólo dispara con `on.push.tags: 'v*.*.*'`, y los
  patrones de tag de GitHub Actions son case-sensitive. Un tag `V1.3.2` (mayúscula)
  NO dispara el release y no lo avisa — falla en silencio (nunca aparece un run en
  `gh run list`). Verificar esto es responsabilidad de [[github-release]], no
  asumirlo. (Los tags `V1.3.0`/`V1.3.1` que quedaron localmente de un ciclo anterior
  usaban mayúscula por error y nunca se hubieran disparado tampoco si se hubiesen
  pusheado — ver nota en `specs/1.3.2-stability-and-security/tasks.md`.)
- Cada tag `vX.Y.Z` pusheado a `origin` dispara `.github/workflows/release.yml`,
  que recompila el `.exe` en CI y publica un GitHub Release. No pushear un tag salvo
  que esa versión esté realmente lista para publicarse.

## 3. Proceso obligatorio para bugs/hardening: Análisis → Fix → Validación → Versión → Commit → Push
Ver [[debug-release-cycle]] skill — encapsula las 6 fases (análisis de causa raíz,
corrección mínima necesaria, validación de no-regresión, bump de versión, commit
convencional, push). No saltarse el análisis de causa raíz antes de tocar código.

## 4. Seguridad
- El protocolo P2P actual (`connection_manager.py`) no tiene TLS: es texto plano sobre
  TCP. Esto es una limitación conocida documentada en `SECURITY.md`, no un bug oculto.
- Toda deserialización de datos que llegan por red debe pasar por `safe_pickle_loads`
  (unpickler restringido en `albertdesk/backend/core/utils.py`) — nunca `pickle.loads`
  directo sobre datos de un peer remoto.
- Nombres de archivo recibidos por transferencia de archivos deben sanearse con
  `os.path.basename` antes de usarse en una ruta local (previene path traversal).
- No commitear secretos, tokens ni contraseñas. `rustdesk_config.json`, `hosts.json`,
  `.cloudflare/` y `logs/` están en `.gitignore` a propósito.

## 5. Repositorio y licencia
- Repo público: `github.com/erickson558/albertdesk`, cuenta de GitHub `erickson558`.
- Licencia: Apache License 2.0 (todo el código nuevo se licencia igual).
- Todo push/release lo hace la skill [[github-release]], que fuerza la cuenta correcta.

## 6. Idioma y UI
- Código, commits y specs: español (idioma del autor). Identificadores de código: inglés
  (convención ya usada en el repo).
- UI de la aplicación: multi-idioma vía `albertdesk/i18n` (`tr()`), actualmente ES/EN.
  Cualquier string nuevo visible en la UI debe añadirse a AMBOS diccionarios de
  `TRANSLATIONS`, nunca hardcodeado.

## 7. Build y distribución
- `build.py` compila con PyInstaller usando el `.venv` del proyecto (nunca el Python
  de sistema) y el ícono `Albertdesk.ico`, dejando `AlbertDesk.exe` en la raíz del repo
  (mismo directorio que los `.py`). El `.exe` nunca se commitea (ver `.gitignore`); el
  artefacto distribuible oficial es el que genera GitHub Actions en cada release.

## Historial de specs
- [`1.3.2-stability-and-security/spec.md`](1.3.2-stability-and-security/spec.md) —
  hardening de seguridad/estabilidad, licencia Apache 2.0, infraestructura SDD/agentes/skills.
