# Plan: Análisis de causa raíz y estrategia de fix

Auditoría realizada leyendo íntegros: `connection_manager.py`, `cloudflare_tunnel.py`,
`input_handler.py`, `main_window.py`, `fullscreen_window.py`, `remote_desktop_widget.py`,
`utils.py`, `config.py`, `logger.py`, más `git log`/diff de los commits ya aplicados
localmente (`aa18351` ya corrigió correctamente el leak de file handles y el bug de
`connection_lost` no emitido — verificado, no se re-reporta).

## Hallazgos y decisión de fix

| # | Bug | Causa raíz | Impacto | Riesgo del fix | Decisión |
|---|-----|-----------|---------|-----------------|----------|
| 1 | RCE vía `pickle.loads` sobre datos de red no confiables (`connection_manager.py`) | El protocolo deserializa cualquier payload con `pickle`, que ejecuta código arbitrario si el stream contiene un opcode `GLOBAL/REDUCE` | Un peer malicioso conectado (posible vía Cloudflare Tunnel expuesto a internet) ejecuta código en la máquina remota | Bajo — un `Unpickler` restringido que bloquea `find_class` no cambia el formato de wire; los mensajes reales son sólo dict/list/str/int/bytes, que nunca invocan `find_class` | **Fix**: `safe_pickle_loads()` en `utils.py`, usado en todos los puntos que deserializan datos de un peer |
| 2 | Path traversal en recepción de archivos (`_handle_file_message`) | `name` del mensaje `file_begin` se usa tal cual en `os.path.join` sin sanear | Peer conectado escribe archivos fuera de `received_files/` | Bajo — `os.path.basename()` | **Fix** |
| 3 | DoS por tamaño de `recv()` no acotado en el handshake de auth (antes de verificar password) | `auth_size`/`resp_size` vienen del header de 4 bytes sin límite superior | Cualquier TCP client puede anunciar tamaños absurdos antes de autenticarse | Bajo — cota `MAX_AUTH_MESSAGE_SIZE` | **Fix** |
| 4 | Handshake de auth no hace *loop-read* (asume un único `recv()` trae todo el payload) | Falta el patrón de acumulación que sí se usa en los bucles de eventos/frames | Password/respuesta truncados en streams TCP fragmentados → fallos de auth espurios | Bajo — reutilizar patrón de acumulación ya existente (`recv_exact`) | **Fix** |
| 5 | Ventana "Pantalla remota" queda huérfana/en blanco tras salir de pantalla completa | `RemoteFullscreenWindow` reparenta `remote_screen` a su propio layout; al salir nadie lo reinserta en el layout original de la pestaña | Regresión funcional 100% reproducible tras el primer uso de fullscreen | Bajo — guardar referencia al layout original y reinsertar el widget al salir | **Fix** |
| 6 | Envío de archivo bloquea la GUI (`_choose_and_send_file` llama `send_file()` directo en el hilo Qt) | `send_file()` hace `socket.sendall()` síncrono por cada chunk de 256 KiB | UI congelada durante toda la transferencia | Bajo-medio — mover a `threading.Thread`; el feedback ya fluye por la señal `connection_status` existente (thread-safe) | **Fix** |
| 7 | Estado compartido sin guarda ante conexiones entrantes concurrentes (`socket`, `is_connected`, `screens`, `_receiving_files`) | Cada conexión aceptada lanza un hilo nuevo sin verificar si ya hay una sesión activa | Reconexión + conexión nueva casi simultáneas corrompen el estado de sesión | Bajo — rechazar conexión entrante si ya hay una sesión activa (guarda simple, sin necesidad de mutex para este caso) | **Fix** |
| 8 | Comparación de password con `!=` (no constante en tiempo) | No es un problema por sí solo, pero es hardening trivial y gratis | Ataque de timing teóricamente posible para adivinar la contraseña carácter a carácter | Bajo — `hmac.compare_digest` | **Fix** |
| 9 | Carrera de hilos en `_capture_tunnel_url` vs `stop_tunnel()` sobre `self.tunnel_process` | Un hilo lee `self.tunnel_process.stderr` mientras otro lo pone a `None` | `AttributeError` silencioso (capturado por except genérico), no crash pero indica estado no sincronizado | Bajo — capturar referencia local al proceso al iniciar el bucle | **Fix** |
| 10 | `SetProcessDPIAware` (legacy) en vez de Per-Monitor v2 | API legacy no soporta DPI distinto por monitor | Coordenadas de mouse desalineadas en setups multi-monitor con escalado mixto (común hoy) | Bajo-medio — intentar `SetProcessDpiAwarenessContext(-4)` con fallback a la API legacy si falla | **Fix** |
| — | Cifrado de transporte (TLS) / passwords en disco sin cifrar | Protocolo diseñado sin capa de cifrado desde el inicio | Confidencialidad de datos/contraseñas si hay MITM o acceso al disco | Alto — rediseño de protocolo, no aplica a un patch | **Diferido**, documentado en `SECURITY.md` (ver `spec.md` fuera de alcance) |

## Orden de implementación
1. `utils.py`: `safe_pickle_loads`, `recv_exact` (helpers puros, sin dependientes aún).
2. `connection_manager.py`: aplicar #1, #2, #3, #4, #7, #8 (todos dependen de los
   helpers del paso 1).
3. `cloudflare_tunnel.py`: #9 (independiente).
4. `input_handler.py`: #10 (independiente).
5. `main_window.py`: #5, #6 (independientes entre sí y del resto).
6. Validación: `py_compile` de los 5 módulos + smoke-import.
7. Documentación + versión + build + commit/tag/push (ver `tasks.md`).
