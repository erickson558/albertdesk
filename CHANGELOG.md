# Changelog

All notable changes to AlbertDesk will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
