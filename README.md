# AlbertDesk - Professional Remote Desktop Control

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![Version 1.0.0](https://img.shields.io/badge/version-1.0.0-brightgreen.svg)

A professional remote desktop control application similar to RustDesk and AnyDesk, with support for both LAN and internet connectivity through Cloudflare Tunnel.

## ✨ Features

### Core Functionality
- 🖥️ **Real-time Screen Sharing** - Live desktop viewing and control
- 🖱️ **Mouse & Keyboard Control** - Full input injection
- 📁 **File Transfer** - Bi-directional file sharing
- 🌐 **Multi-Screen Support** - Switch between multiple displays
- 🔐 **Secure Connection** - Password-protected communication
- 💾 **Host Management** - Save and quickly connect to favorite devices

### Connectivity Options
- **🔗 LAN Direct** - P2P connection on local networks
- **🌐 Internet (Cloudflare Tunnel)** - Connect anywhere with free Cloudflare Tunnel
- **Optional Relay** - Support for custom relay servers (planned)

### User Interface
- **Modern PyQt5 UI** - Clean, intuitive interface with tabs
- **Fullscreen Mode** - Floating control overlay with auto-hide
- **Status Indicator** - Real-time connection and network status
- **Dark Theme** - Easy on the eyes for extended use

## 🚀 Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/albertdesk.git
   cd albertdesk
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

### Building Standalone Executable

```bash
pip install pyinstaller
python build.py
```

The executable will be created in the `dist/` folder.

## 🌐 Using Cloudflare Tunnel (Internet)

For internet connectivity without port forwarding:

1. **Install Cloudflare Tunnel**
   - Windows: `scoop install cloudflare-warp`
   - macOS: `brew install cloudflare/warp/cloudflared`
   - Linux: See [Cloudflare docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/)

2. **Enable Tunnel in AlbertDesk**
   - Go to "🌐 Internet (Tunnel)" tab
   - Click "▶️ Iniciar Tunnel"
   - Share the generated URL with other users

3. **Connect from Another Device**
   - Input the tunnel URL in the "Destino" field
   - Enter the password and connect

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

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🌟 Roadmap

- [ ] Custom relay server support
- [ ] End-to-end encryption
- [ ] Clipboard synchronization
- [ ] Audio/Video transfer
- [ ] Mobile app support
- [ ] Web interface
- [ ] Built-in VPN mode (ZeroTier integration)

## 🐛 Bug Reports

Found a bug? Please open an issue on GitHub with:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Your setup (OS, Python version, etc.)

## 📧 Support

For questions and support, please open an issue on GitHub.

---

Made with ❤️ by Albert
