# Spec: Hardening de estabilidad/seguridad + infraestructura SDD (v1.3.2)

## Contexto
`main`/HEAD tenía 3 commits sin publicar (i18n ES/EN, botón de donación, varios
bugfixes de V1.3.0/V1.3.1) que nunca llegaron a `origin` ni a un release de GitHub.
Antes de publicar, se pidió una auditoría completa de errores reales (no estilo) y
la creación de infraestructura de Spec-Driven Development (specs, agentes, skills)
para que este tipo de ciclo se repita de forma consistente en el futuro.

## Requisitos (qué debe cumplirse)
1. Ningún fix debe cambiar comportamiento observable existente, salvo el bug corregido.
2. Todo bug corregido debe tener causa raíz identificada antes de tocar código
   (ver `plan.md`).
3. Los fixes de protocolo de red deben mantener client/server en sincronía (no hay
   versiones mixtas en producción: un único `.exe` corre en ambos lados).
4. Licencia del repo pasa de MIT a Apache License 2.0; repo permanece público.
5. Versión coherente `1.3.2` (texto plano) en `main.py`, `albertdesk/__init__.py`,
   `setup.py`, `README.md`, `CHANGELOG.md`, y tag de git `v1.3.2` (minúscula —
   requisito funcional, no cosmético: ver hallazgo en `tasks.md`).
6. `.exe` recompilado con `build.py` usando el `.venv` del proyecto y `Albertdesk.ico`,
   generado en la raíz del repo.
7. Commit convencional + tag `v1.3.2` + push a `origin main` en la cuenta de GitHub
   `erickson558` (repo `erickson558/albertdesk`).
8. Documentación actualizada: README (dependencias, arquitectura, licencia, donación,
   multi-idioma), CHANGELOG (incluye backfill de V1.3.0/V1.3.1 nunca documentadas),
   `SECURITY.md` nuevo, `docs/ARCHITECTURE.md` nuevo.

## Fuera de alcance (explícitamente diferido, no "olvidado")
- **TLS/cifrado end-to-end del protocolo P2P**: es un rediseño de arquitectura
  (major version), no un patch. Se documenta como limitación conocida en
  `SECURITY.md` y roadmap de `CHANGELOG.md`.
- **Idiomas adicionales a ES/EN**: el framework de i18n ya soporta agregar más
  (`albertdesk/i18n/__init__.py`), pero no se añaden traducciones no verificadas en
  este pase para no introducir strings de baja calidad.
- **Republicar tags `V1.3.0`/`V1.3.1` a origin**: quedaron como hitos de desarrollo
  local nunca liberados (además con casing incorrecto — mayúscula — que tampoco
  hubiera disparado el release, ver hallazgo en `tasks.md`); se documentan en el
  CHANGELOG pero solo se publica el tag consolidado `v1.3.2` para evitar releases
  redundantes de versiones que nunca se distribuyeron.
- Eliminar `rustdeskclone.py` (prototipo monolítico legado en la raíz, no importado
  por `main.py` ni el paquete `albertdesk/`): no se toca porque no fue pedido
  explícitamente y podría conservarse como referencia histórica.

## Criterio de aceptación
- La app arranca sin excepción en el import chain (`python -m py_compile` limpio en
  todos los módulos tocados).
- `build.py` termina con código de salida 0 y genera `AlbertDesk.exe` en la raíz.
- `git push` a `main` y al tag `v1.3.2` completado sin errores, usando la cuenta
  `erickson558`.
