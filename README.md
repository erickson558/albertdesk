# 🖥️ AlbertDesk - Professional Remote Desktop Control

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![Version 1.2.0](https://img.shields.io/badge/version-1.2.0-brightgreen.svg)
[![GitHub release](https://img.shields.io/github/v/release/erickson558/albertdesk)](https://github.com/erickson558/albertdesk/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/erickson558/albertdesk)

Una aplicación profesional de control remoto de escritorio similar a RustDesk y AnyDesk, con soporte para conectividad LAN e Internet a través de Cloudflare Tunnel. Desarrollado con PyQt5 y arquitectura limpia separando backend/frontend.

<p align="center">
  <img src="https://img.shields.io/badge/PyQt5-5.15+-green.svg" alt="PyQt5">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Cloudflare-Tunnel-orange.svg" alt="Cloudflare">
</p>

## ✨ Características

### Funcionalidad Principal
- 🖥️ **Compartir Pantalla en Tiempo Real** - Visualización y control de escritorio en vivo
- 🖱️ **Control de Mouse y Teclado** - Inyección completa de entrada (input injection)
- 📁 **Transferencia de Archivos** - Compartir archivos bidireccional
- 🌐 **Soporte Multi-Pantalla** - Cambiar entre múltiples monitores
- 🔐 **Conexión Segura** - Comunicación protegida con contraseña
- 💾 **Gestión de Hosts** - Guardar y conectar rápidamente a dispositivos favoritos
- 🖼️ **Modo Pantalla Completa** - Control flotante con auto-ocultación

### Opciones de Conectividad
- **🔗 LAN Directa** - Conexión P2P en redes locales
- **🌐 Internet (Cloudflare Tunnel)** - Conexión desde cualquier lugar con Cloudflare Tunnel gratuito
- **📡 Sin Configuración de Router** - No necesitas abrir puertos ni configurar NAT

### Interfaz de Usuario (Nueva en v1.1.0)
- **Terminal CLI Embebida** 🆕 - Terminal integrada para instalación de Cloudflare desde la app
- **Modern PyQt5 UI** - Interfaz limpia e intuitiva con pestañas
- **Salida en Tiempo Real** - Visualización de logs de cloudflared en el terminal
- **Tema Oscuro** - Fácil para la vista durante uso prolongado
- **Indicadores de Estado** - Estado de conexión y red en tiempo real

## 🚀 Inicio Rápido

### Opción 1: Descargar Ejecutable (Más Fácil)

1. Ve a [Releases](https://github.com/erickson558/albertdesk/releases/latest)
2. Descarga `AlbertDesk.exe` (Windows)
3. Ejecuta el archivo (no requiere instalación)

### Opción 2: Desde el Código Fuente

#### Requisitos Previos
- Python 3.8+ ([Descargar aquí](https://www.python.org/downloads/))
- Git ([Descargar aquí](https://git-scm.com/downloads))

#### Paso 1: Clonar el Repositorio
```bash
git clone https://github.com/erickson558/albertdesk.git
cd albertdesk
```

#### Paso 2: Crear Entorno Virtual (Recomendado)
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

#### Paso 3: Instalar Dependencias
```bash
pip install -r requirements.txt
```

#### Paso 4: Ejecutar la Aplicación
```bash
python main.py
```

### Compilar Ejecutable Standalone

Para crear tu propio ejecutable:

```bash
# Instalar PyInstaller
pip install pyinstaller

# Compilar
python build.py
```

El ejecutable `AlbertDesk.exe` se generará en la carpeta raíz del proyecto.

**Nota:** El proceso de compilación puede tardar 2-3 minutos.

## 🌐 Usar Cloudflare Tunnel (Conexión por Internet)

**Nuevo en v1.1.0:** Ahora puedes ver las instrucciones de instalación directamente en la app usando el terminal embebido.

Para conectividad por internet sin configurar el router:

### Paso 1: Instalar Cloudflare Tunnel

**Desde la App (Nuevo):**
1. Abre AlbertDesk
2. Ve a la pestaña "🌐 Internet (Tunnel)"
3. Haz clic en "📥 Instalar Cloudflare Tunnel"
4. Sigue las instrucciones que aparecen en el terminal integrado

**Instalación Manual:**

**Windows:**
```powershell
# Opción 1: Con Scoop
scoop install cloudflared

# Opción 2: Descarga directa
# https://github.com/cloudflare/cloudflared/releases
# Descarga cloudflared-windows-amd64.exe y renómbralo a cloudflared.exe
# Muévelo a una carpeta en tu PATH
```

**macOS:**
```bash
brew install cloudflared
```

**Linux (Debian/Ubuntu):**
```bash
curl -L https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/linux focal main' | sudo tee /etc/apt/sources.list.d/cloudflare-main.list
sudo apt-get update && sudo apt-get install cloudflared
```

### Paso 2: Activar Tunnel en AlbertDesk

1. Ve a la pestaña "🌐 Internet (Tunnel)"
2. Haz clic en "▶️ Iniciar Tunnel"
3. Espera a que aparezca la URL en el terminal (ejemplo: `https://xxxxx.trycloudflare.com`)
4. Comparte esta URL con otros usuarios

**Nota:** La URL del tunnel cambia cada vez que lo inicias. Es temporal y gratuito.

### Paso 3: Conectarse desde Otro Dispositivo

1. En el otro dispositivo, abre AlbertDesk
2. Ve a la pestaña "Conectar"
3. Ingresa la URL del tunnel en el campo "Destino" (ejemplo: `https://xxxxx.trycloudflare.com`)
4. Ingresa la contraseña y haz clic en "Conectar"

### Solución de Problemas

**El tunnel no inicia:**
- Verifica que cloudflared esté instalado: `cloudflared --version`
- Revisa el terminal embebido en la app para ver los errores
- Asegúrate de tener conexión a internet

**La URL no aparece:**
- Espera 10-15 segundos después de iniciar el tunnel
- Verifica los logs en el terminal de la app
- Reinicia el tunnel con el botón "⏹️ Detener Tunnel" y vuelve a intentar

## 📁 Project Structure

```
albertdesk/
├── backend/              # Core business logic
│   ├── core/
│   │   ├── config.py    # Configuration management
│   │   ├── logger.py    # Logging system
│   │   └── utils.py     # Helper functions
│   └── network/
│       ├── connection_manager.py     # P2P networking
│       ├── input_handler.py          # Input injection (Windows)
│       └── cloudflare_tunnel.py      # Tunnel integration
├── frontend/             # User interface
│   ├── ui/
│   │   └── main_window.py    # Main application window
│   └── widgets/
│       ├── remote_desktop_widget.py   # Screen viewer
│       └── fullscreen_window.py       # Fullscreen mode
├── main.py              # Application entry point
├── build.py             # PyInstaller build script
└── requirements.txt     # Python dependencies
```

## 🔒 Security Notes

- Passwords are hashed and transmitted securely
- Communication uses compression and error detection
- Optional password saving (user preference)
- No telemetry or data collection

## 🛠️ Configuration

Configuration is stored in `rustdesk_config.json`:

```json
{
    "id": "123456789",
    "password": "your_password",
    "port": 6969,
    "remember_passwords": true,
    "auto_connect": false,
    "saved_passwords": {}
}
```

## 📝 System Requirements

- **Python**: 3.8 or higher
- **OS**: Windows, macOS, or Linux
- **RAM**: 256 MB minimum
- **Screen**: 1366x768 or higher (recommended)

## 🤝 Contribuir

Las contribuciones son bienvenidas! Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

Por favor lee [CONTRIBUTING.md](CONTRIBUTING.md) para más detalles sobre nuestro código de conducta y proceso de desarrollo.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🌟 Roadmap

### v1.2.0 (Próximo)
- [ ] Sincronización de portapapeles
- [ ] Chat integrado
- [ ] Grabación de sesiones

### v2.0.0 (Futuro)
- [ ] Servidor relay personalizado
- [ ] Cifrado end-to-end
- [ ] Transferencia de audio/video
- [ ] Aplicación móvil (Android/iOS)
- [ ] Interfaz web
- [ ] Modo VPN integrado (ZeroTier)
- [ ] Soporte para múltiples sesiones simultáneas

### Completado ✅
- [x] v1.1.0: Terminal CLI embebida
- [x] v1.1.0: Instalación de Cloudflare desde la app
- [x] v1.1.0: GitHub Actions para releases automáticos
- [x] v1.0.0: Control remoto básico
- [x] v1.0.0: Transferencia de archivos
- [x] v1.0.0: Cloudflare Tunnel integration

## 🐛 Reportar Bugs

¿Encontraste un bug? Por favor abre un [issue en GitHub](https://github.com/erickson558/albertdesk/issues) con:

- **Descripción del problema:** Qué esperabas vs qué sucedió
- **Pasos para reproducir:** Lista detallada de pasos
- **Logs:** Si es posible, incluye los logs de la carpeta `logs/`
- **Tu configuración:**
  - Sistema operativo y versión
  - Versión de Python
  - Versión de AlbertDesk
- **Screenshots:** Si aplica

## 📧 Soporte y Contacto

- **Issues:** [GitHub Issues](https://github.com/erickson558/albertdesk/issues)
- **Discussions:** [GitHub Discussions](https://github.com/erickson558/albertdesk/discussions)
- **Wiki:** [Documentación](https://github.com/erickson558/albertdesk/wiki)

## 📚 Recursos Adicionales

- [CHANGELOG.md](CHANGELOG.md) - Historial de versiones
- [CONTRIBUTING.md](CONTRIBUTING.md) - Guía para contribuidores
- [LICENSE](LICENSE) - Licencia MIT

## ⭐ ¿Te Gusta el Proyecto?

Si AlbertDesk te resulta útil:
- ⭐ Dale una estrella al repositorio
- 🐛 Reporta bugs que encuentres
- 💡 Sugiere nuevas características
- 🤝 Contribuye con código
- 📢 Compártelo con otros

---

<p align="center">
  <strong>Hecho con ❤️ por Albert</strong><br>
  <sub>© 2026 AlbertDesk - Licencia MIT</sub>
</p>

<p align="center">
  <a href="https://github.com/erickson558/albertdesk/stargazers">⭐ Star</a> •
  <a href="https://github.com/erickson558/albertdesk/issues">🐛 Issues</a> •
  <a href="https://github.com/erickson558/albertdesk/releases">📥 Releases</a>
</p>
