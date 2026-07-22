---
name: github-release
description: Publica commits/tags/releases de AlbertDesk en GitHub, SIEMPRE en la cuenta erickson558 y el repo erickson558/albertdesk. Usar para cualquier "sube a GitHub", "haz push", "crea el release", "publica la nueva versión".
---

# Publicar AlbertDesk en GitHub (cuenta erickson558)

Este repo se publica exclusivamente en `github.com/erickson558/albertdesk`, cuenta
de GitHub **erickson558**. La máquina puede tener otras cuentas de `gh` autenticadas
(por ejemplo una cuenta corporativa) — nunca asumas que la cuenta activa es la
correcta sin verificarlo primero.

## 0. Verificar cuenta y remoto ANTES de pushear (siempre)
```bash
gh auth status                              # confirma qué cuentas hay autenticadas
gh auth switch --user erickson558           # fuerza erickson558 como cuenta activa
git remote -v                               # debe apuntar a erickson558/albertdesk
```
Si `git remote -v` no apunta a `github.com/erickson558/albertdesk`, PARA y pregunta
al usuario — no reconfigures el remoto sin confirmar, podría estar apuntando a un
fork intencional.

Nota de entorno: si `git` falla con "detected dubious ownership" (típico en repos
sincronizados por OneDrive), usa `git -c safe.directory='*' <comando>` en vez de
modificar la config global de git.

## 1. Revisar qué se va a subir
```bash
git -c safe.directory='*' status
git -c safe.directory='*' diff --stat origin/main..HEAD
```
Confirma que no hay archivos que no deberían subirse (secretos, `rustdesk_config.json`,
`hosts.json`, `.cloudflare/`, `logs/`, `*.exe` — todos ya en `.gitignore`, pero
verifica que un `git add` amplio no los haya colado igual).

## 2. Commit (si no se hizo ya en la fase de release)
```bash
git add <archivos específicos, nunca -A/. a ciegas>
git commit -m "$(cat <<'EOF'
<tipo>: <resumen> (Vx.y.z)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

## 3. Tag y push
**El tag debe ser `vX.Y.Z` con "v" MINÚSCULA** — `.github/workflows/release.yml`
dispara con `on.push.tags: 'v*.*.*'`, y GitHub Actions compara patrones de tag de
forma case-sensitive. Un tag `V1.3.2` (mayúscula) se pushea sin error pero **no
dispara nada y no avisa** — la única forma de notarlo es que no aparece ningún run
nuevo en `gh run list`. Esto ya pasó una vez en este repo (ver
`specs/1.3.2-stability-and-security/tasks.md`), no lo repitas.
```bash
git tag vx.y.z
git push origin main
git push origin vx.y.z
```
El push del tag dispara `.github/workflows/release.yml` en GitHub Actions, que
recompila el `.exe` en un runner limpio de Windows y crea el GitHub Release
automáticamente adjuntando `AlbertDesk.exe`, `README.md`, `CHANGELOG.md`, `LICENSE`.
**No crees el release manualmente con `gh release create`** salvo que el workflow
haya fallado — es redundante y puede producir dos releases para el mismo tag.

## 4. Verificar que el release se disparó (obligatorio, no asumir)
```bash
gh run list --repo erickson558/albertdesk --workflow=release.yml --limit 3
```
Si tu tag no aparece como el run más reciente en menos de ~30 segundos, algo no
disparó el workflow (casing del tag, patrón del trigger cambiado, etc.) — investiga
antes de dar el release por hecho. Si aparece pero termina en `failure`, usa
`gh run view <id> --log-failed` MIENTRAS el run es reciente (los logs expiran a los
~90 días, ver el mismo archivo de tasks.md para un caso real donde esto impidió
diagnosticar fallos históricos).

## Reglas
- Nunca hagas `push --force` a `main` sin confirmación explícita del usuario para
  ese push en concreto.
- Si existen tags locales que nunca se publicaron (p. ej. quedaron de un ciclo
  anterior interrumpido), no los pushees automáticamente sólo por existir — confirma
  con el usuario si esas versiones realmente deben publicarse o si el ciclo actual
  las consolida en un tag más nuevo (ver `specs/1.3.2-stability-and-security/tasks.md`
  para un ejemplo real de esta situación).
- Un tag ya pusheado a `origin` es inmutable en la práctica (dispara un release
  público) — si te equivocaste de versión, sube un tag nuevo corregido, no
  fuerces/borres el tag público sin que el usuario lo pida explícitamente.
