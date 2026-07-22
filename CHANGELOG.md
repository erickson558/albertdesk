# Changelog

All notable changes to AlbertDesk will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.2] - 2026-07-22

### Security
- **Deserialización insegura (RCE vía pickle)** 🔒 - Se reemplazó `pickle.loads` por
  `safe_pickle_loads` (Unpickler restringido) en todos los puntos que reciben datos
  de un peer de red; bloquea la reconstrucción de clases/funciones arbitrarias
  manteniendo el mismo formato de wire para los mensajes reales (dict/list/str/int/bytes)
- **Path traversal en transferencia de archivos** - El nombre de archivo recibido se
  sanea con `os.path.basename()` antes de escribirse a disco
- **DoS por tamaño no acotado en el handshake de autenticación** - `auth_size`/`resp_size`
  ahora están acotados a `MAX_AUTH_MESSAGE_SIZE` (4 KiB) antes de validar la contraseña
- **Handshake de autenticación con lectura corta** - Se reemplazó un único `recv()` por
  `recv_exact()` (loop-read), evitando fallos de auth espurios en streams TCP fragmentados
- **Comparación de contraseña no constante en tiempo** - Ahora usa `hmac.compare_digest`

### Fixed
- **Pantalla remota en blanco tras salir de pantalla completa** 🖥️ - `remote_screen`
  quedaba huérfano al reparentarse a `RemoteFullscreenWindow`; ahora se reinserta en
  el layout original de la pestaña al salir
- **Envío de archivos congelaba la GUI** - `send_file()` ahora corre en un hilo de
  fondo; el progreso/errores ya fluían de forma thread-safe por `connection_status`
- **Condición de carrera con conexiones entrantes concurrentes** - El servidor ahora
  rechaza una nueva conexión si ya hay una sesión activa, evitando corrupción de
  estado compartido (`socket`, `screens`, `_receiving_files`)
- **Condición de carrera en la captura de la URL del tunnel** - `_capture_tunnel_url`
  usa una referencia local al proceso en vez de `self.tunnel_process`, evitando un
  `AttributeError` intermitente si `stop_tunnel()` corre en paralelo
- **Coordenadas de mouse desalineadas en multi-monitor con DPI mixto** - Se usa
  `SetProcessDpiAwarenessContext` (Per-Monitor v2) con fallback a la API legacy
- **Inconsistencia de versión** - `albertdesk/__init__.py` seguía en `1.3.0` y con
  `__license__ = "MIT"` mientras `main.py` ya estaba en `1.3.1`; ahora coinciden

### Changed
- **Licencia: MIT → Apache License 2.0** - Repo público sin cambios de visibilidad
- Documentación: `SECURITY.md` (nuevo), `docs/ARCHITECTURE.md` (nuevo),
  `CONTRIBUTING.md` (nuevo), `README.md` actualizado (dependencias, arquitectura,
  licencia, donación, i18n)
- Infraestructura de desarrollo: Spec-Driven Development (`specs/`), agentes
  (`.claude/agents/python-qa-devops.md`, `.claude/agents/code-explainer.md`) y
  skills (`spec-driven-change`, `code-annotate`, `debug-release-cycle`,
  `github-release`) documentados en `.claude/`

## [1.3.1] - 2026-04-23 (documentado retroactivamente)

### Fixed
- **`connection_lost` no se emitía cuando el servidor cerraba la sesión** - La UI
  quedaba atascada en estado "Conectado" para siempre; se agregó la bandera
  `_session_established` para emitir `connection_lost` correctamente y evitar
  reintento automático tras una sesión ya establecida
- **Fuga de file handles en transferencias incompletas** - Se agregó
  `_cleanup_receiving_files()` para cerrar archivos abiertos al desconectar/detener
- **Bug de emoji en `pwd_label`** - Un slice `tr('btn_copy')[:2]` producía "📋 " en
  vez de "C" (mostraba "🔐 📋 ontraseña:"); se agregó la clave i18n `label_password`
- **Strings hardcodeados en español que no cambiaban con el idioma** - `port_label`,
  `_generate_new_password`, `_save_settings` y el estado de conexión ahora usan `tr()`
- **`build.py` compilaba con el Python de sistema (podía traer PyQt6)** - Ahora
  detecta y usa `.venv/Scripts/python.exe` si existe, valida dependencias antes de
  compilar (`check_dependencies`) y añade `--hidden-import PyQt5.sip`

## [1.3.0] - 2026-04-23 (documentado retroactivamente)

### Added
- **Multi-idioma (Español/Inglés)** 🌐 - Módulo `albertdesk/i18n` con selector de
  idioma persistente en la pestaña de Configuración
- **Botón de donación** ☕ - "Cómprame una cerveza" con enlace a PayPal en la
  pestaña de Configuración

### Fixed
- `receive_remote_events_server` cerraba el hilo de control silenciosamente tras
  5s de inactividad (timeout demasiado corto); ahora usa 30s
- `connect_to_host` reintentaba con la misma contraseña incorrecta tras un fallo de
  autenticación; ahora deja que `auth_required` gestione el nuevo intento
- Actualización de un `QLabel` directamente desde un hilo no-GUI en el estado del
  tunnel; ahora usa una señal Qt interna thread-safe
- `_last_target_label` podía ser `None` al usarse como clave en `saved_passwords`
- El launcher `.bat` generado por `build.py` apuntaba a `dist\AlbertDesk.exe` en vez
  de `AlbertDesk.exe` (raíz)

## [1.2.2] - 2026-03-02

### Fixed
- **Modo silent para cloudflared** 🔇 - Ya no mostrarán ventanas CMD
- Ocultadas ventanas de consola al verificar cloudflared instalado
- Ocultadas ventanas de consola al iniciar cloudflared tunnel
- En Windows: usa `subprocess.CREATE_NO_WINDOW` para limpieza visual
- Mantiene comportamiento normal en macOS/Linux

## [1.2.1] - 2026-03-02

### Fixed
- **Detección mejorada de Cloudflare instalado** 🔧 - Ya no pide reinstalar después de instalar
- Verifica directamente en las ubicaciones de instalación en lugar de solo usar el comando
- Comprueba `Program Files\cloudflared\cloudflared.exe`
- Comprueba `AppData\Local\Programs\cloudflared\cloudflared.exe`
- Mantiene verificación por comando como fallback para PATH actualizado
- Soluciona problema donde el PATH no se actualizaba en el proceso actual sin reiniciar

## [1.2.0] - 2026-03-02

### Added
- **Instalación Automática de Cloudflare Tunnel** 🚀 - Windows ahora puede instalar cloudflared automáticamente
- Descarga automática desde GitHub releases oficial de Cloudflare
- Instalación en carpeta de usuario (no requiere permisos de administrador)
- Actualización automática del PATH del sistema
- Barra de progreso durante la descarga
- Notificación del sistema cuando se actualiza el PATH

### Changed
- Botón "Instalar Cloudflare Tunnel" ahora ejecuta la instalación en lugar de solo mostrar instrucciones
- Mejoradas las instrucciones de instalación para todos los sistemas operativos
- El proceso de instalación se ejecuta en un hilo separado para no bloquear la UI
- Mejor feedback visual durante el proceso de instalación

### Technical
- Agregado método `install_cloudflared()` en CloudflareTunnelManager
- Agregado método `_install_windows()` para instalación automática en Windows
- Uso de urllib.request para descarga de archivos
- Uso de winreg para modificar PATH del usuario
- Uso de ctypes para notificar cambios en variables de entorno
- Thread-safe UI updates durante instalación

### User Experience
- Los usuarios de Windows ahora pueden instalar cloudflared con un solo clic
- No es necesario buscar y descargar manualmente el ejecutable
- No se requieren conocimientos técnicos para la instalación
- El terminal muestra el progreso en tiempo real

---

## [1.1.0] - 2026-03-02

### Added
- **Terminal CLI Embebida** - Ventana de terminal integrada en el tab de Cloudflare Tunnel
- Instalación de Cloudflare desde la app sin salir de la interfaz
- Visualización en tiempo real de la salida de cloudflared en el terminal
- Botón para limpiar el terminal embebido
- Instrucciones de instalación mostradas directamente en el terminal

### Changed
- El ejecutable ahora se genera en la carpeta raíz en lugar de dist/
- Las instrucciones de instalación de Cloudflare se muestran en terminal en lugar de diálogo modal
- Mejorada la experiencia de usuario para instalación de Cloudflare Tunnel

### Technical
- Agregado QPlainTextEdit para terminal con tema oscuro
- Modificado CloudflareTunnelManager para soportar callback on_output
- Thread-safe updates del terminal usando QMetaObject.invokeMethod
- Terminal limitado a 1000 líneas para optimizar memoria

---

## [1.0.0] - 2026-03-02

### Added
- **Initial Release** - Professional remote desktop control application
- Core remote desktop functionality (screen sharing, mouse/keyboard control)
- File transfer support (bi-directional)
- LAN connectivity with P2P connection
- Cloudflare Tunnel integration for internet connectivity without port forwarding
- Modern PyQt5 user interface with multiple tabs
- Fullscreen mode with floating control overlay
- Host management and password saving
- Multi-screen support
- Logging system with file and console output
- Configuration management system
- Windows input injection using ctypes
- Screenshot capture with configurable quality
- Type hints throughout codebase
- Comprehensive docstrings and comments
- Clean architecture with separated backend/frontend
- PyInstaller build script for standalone executable

### Features
- 🖥️ Real-time screen sharing and viewing
- 🖱️ Full mouse and keyboard control
- 📁 Bi-directional file transfer
- 🌐 Internet connectivity via Cloudflare Tunnel
- 🔐 Password-protected connections
- 💾 Host history and quick access
- 🎨 Modern dark-themed UI
- ⛶ Fullscreen viewing mode

### Technical Improvements
- Proper module structure (backend/frontend separation)
- Clean code organization with type annotations
- Comprehensive logging for debugging
- Configuration stored in JSON files
- Thread-safe network operations
- Error handling and graceful degradation
- Modularized network protocol handling

---

## Versioning

- **Major (X.0.0)**: Breaking changes or major new features
- **Minor (1.X.0)**: New features, backward compatible
- **Patch (1.0.X)**: Bug fixes and minor improvements

## Planned Features (Roadmap)

- [ ] Custom relay server support
- [ ] End-to-end encryption (TLS)
- [ ] Clipboard synchronization
- [ ] Audio/video transfer
- [ ] Mobile app support
- [ ] Web-based interface
- [ ] ZeroTier VPN integration
- [ ] Wake-on-LAN support
- [ ] System tray icon
- [ ] Connection history and analytics
