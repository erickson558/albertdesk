# Changelog

All notable changes to AlbertDesk will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
