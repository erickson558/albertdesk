# Arquitectura de AlbertDesk

Mapa de qué hace cada módulo y cómo se comunican entre sí. Para el detalle de un
archivo concreto, usa el agente `code-explainer` (`.claude/agents/code-explainer.md`).

## Vista general

```
main.py                          → punto de entrada, crea QApplication y la ventana principal
albertdesk/
├── backend/
│   ├── core/
│   │   ├── config.py             → carga/guarda rustdesk_config.json y hosts.json
│   │   ├── logger.py             → configuración de logging (archivo + consola)
│   │   └── utils.py              → helpers puros: IDs, passwords, compresión,
│   │                                framing de mensajes, deserialización segura
│   └── network/
│       ├── connection_manager.py → servidor/cliente P2P, captura de pantalla,
│       │                            inyección de input, transferencia de archivos
│       ├── input_handler.py      → inyección de mouse/teclado en Windows (ctypes)
│       └── cloudflare_tunnel.py  → gestiona el proceso `cloudflared` (instalar/
│                                    iniciar/detener el tunnel, capturar su URL)
├── frontend/
│   ├── ui/main_window.py         → ventana principal PyQt5, conecta señales del
│   │                                backend a la UI, arma las pestañas
│   └── widgets/
│       ├── remote_desktop_widget.py → visor de la pantalla remota (QLabel + eventos
│       │                               de mouse/teclado convertidos a mensajes)
│       └── fullscreen_window.py     → modo pantalla completa con overlay flotante
└── i18n/__init__.py              → diccionarios de traducción ES/EN + tr()
```

## Modelo de concurrencia (la parte que más confunde)

AlbertDesk es una app PyQt5: **todo lo que toca widgets debe correr en el hilo
principal (hilo de la GUI)**. El networking es bloqueante (sockets síncronos), así
que corre en hilos de fondo (`threading.Thread`, todos `daemon=True`):

| Qué | Hilo | Notas |
|---|---|---|
| Servidor aceptando conexiones (`ConnectionManager.start_server`) | fondo (lanzado desde `AlbertDeskWindow.__init__`) | un hilo nuevo por conexión entrante |
| Envío de screenshots al cliente conectado | fondo (dentro de `handle_incoming_connection`) | bucle con `time.sleep(SCREENSHOT_DELAY)` |
| Recepción de eventos de mouse/teclado en el servidor | fondo (`receive_remote_events_server`) | un hilo separado del de screenshots |
| Conexión/recepción de frames como cliente (`connect_to_host`) | fondo (lanzado desde el botón "Conectar") | bucle de recv() de frames |
| Envío de archivos (`send_file`) | fondo desde V1.3.2 | antes bloqueaba la GUI (bug corregido, ver `specs/1.3.2-stability-and-security/plan.md`) |
| Instalación/arranque de `cloudflared` | fondo | subprocess + hilo lector de stdout/stderr |
| Actualizar un widget Qt desde cualquiera de los hilos de arriba | **nunca directo** | se usa `pyqtSignal` (p. ej. `connection_status`, `frame_received`, `_tunnel_status_signal`) — Qt encola la entrega de la señal al hilo dueño del receptor, así que emitir desde un hilo de fondo hacia un slot que vive en el hilo de la GUI es seguro |

Estado compartido entre hilos a tener en cuenta si tocas `connection_manager.py`:
`self.socket`, `self.is_connected`, `self.screens`, `self.current_screen`,
`self._receiving_files`, `self.tunnel_process` (en `cloudflare_tunnel.py`). No hay
un mutex general — desde V1.3.2 se rechaza una conexión entrante nueva si ya hay
una sesión activa, precisamente para evitar que dos hilos de sesión escriban ese
estado a la vez.

## Protocolo de red (resumen)

Formato de mensaje: 4 bytes big-endian con el tamaño (`pack_message`/
`unpack_message_size` en `utils.py`) seguidos del payload.

1. **Handshake**: el cliente manda la contraseña en texto plano; el servidor
   responde `auth_ok` o `auth_failed` (comparación con `hmac.compare_digest`,
   tamaño acotado a `MAX_AUTH_MESSAGE_SIZE` antes de validar — ver `SECURITY.md`).
2. **Info de pantallas**: el servidor manda un dict `{'type': 'screens', ...}`
   serializado con `pickle.dumps` (el servidor controla qué serializa, es seguro).
3. **Screenshots**: JPEG comprimido con zlib (`compress_data`), sin pickle.
4. **Eventos de entrada** (mouse/teclado) y **transferencia de archivos**: dicts
   serializados con pickle. El lado receptor SIEMPRE usa `safe_pickle_loads()`
   (nunca `pickle.loads` directo) porque vienen de la red — ver `SECURITY.md`.

No hay TLS: todo esto viaja en texto plano sobre el socket TCP. Es una limitación
conocida documentada en `SECURITY.md`, no un descuido.

## Build y distribución

`build.py` compila con PyInstaller usando el Python del `.venv` del proyecto
(garantiza que se empaquete la versión correcta de PyQt5), embebe el ícono
`Albertdesk.ico` y deja `AlbertDesk.exe` en la raíz del repo. El `.exe` nunca se
commitea (`.gitignore`); en GitHub, `.github/workflows/release.yml` lo recompila en
un runner limpio de Windows cada vez que se pushea un tag `vX.Y.Z`/`VX.Y.Z`, y lo
adjunta al GitHub Release automáticamente.
