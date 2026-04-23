"""
Internationalization (i18n) support for AlbertDesk.
Supports Spanish (es) and English (en).
Usage: from albertdesk.i18n import tr, set_language, get_language
"""

# Idioma activo por defecto
_CURRENT_LANG = "es"

# Diccionario completo de traducciones
TRANSLATIONS = {
    "es": {
        # Título de ventana
        "window_title": "AlbertDesk - Control de Escritorio Remoto",
        # Pestañas
        "tab_my_id": "🆔 Mi ID",
        "tab_connect": "🔗 Conectar",
        "tab_remote_screen": "🖥️ Pantalla Remota",
        "tab_tunnel": "🌐 Internet (Tunnel)",
        "tab_settings": "⚙️ Configuración",
        "tab_network": "📡 Red",
        # Pestaña Mi ID
        "group_local_device": "Dispositivo Local",
        "btn_copy": "📋 Copiar",
        "btn_generate": "🔄 Generar",
        "btn_refresh": "🔄 Actualizar",
        # Pestaña Conectar
        "label_target": "Destino (IP o ID del equipo remoto):",
        "placeholder_target": "192.168.1.100 o ID del equipo",
        "label_known_hosts": "Equipos conocidos:",
        "status_disconnected": "🔴 Desconectado",
        "btn_connect": "🔗 Conectar",
        "btn_disconnect": "⛔ Desconectar",
        # Pestaña Pantalla Remota
        "btn_send_file": "📤 Enviar archivo",
        "btn_recv_folder": "📥 Carpeta descargas",
        "btn_fullscreen": "⛶ Pantalla Completa",
        # Pestaña Tunnel
        "group_tunnel": "🌐 Cloudflare Tunnel - Conecta por Internet",
        "tunnel_info": (
            "Usa Cloudflare Tunnel para conectarte a través de internet sin necesidad "
            "de un servidor propio. Completamente gratis."
        ),
        "tunnel_status_unconfigured": "❓ No configurado",
        "btn_install_tunnel": "📥 Instalar Cloudflare Tunnel",
        "btn_start_tunnel": "▶️ Iniciar Tunnel",
        "btn_stop_tunnel": "⏹️ Detener Tunnel",
        "tunnel_url_waiting": "URL: (esperando...)",
        "btn_copy_url": "📋 Copiar URL",
        "group_terminal": "💻 Terminal / Instalación",
        "terminal_placeholder": (
            "Terminal de instalación y salida de Cloudflare Tunnel...\n\n"
            "Haz clic en 'Instalar Cloudflare Tunnel' para ver las instrucciones."
        ),
        "btn_clear_terminal": "🗑️ Limpiar Terminal",
        # Pestaña Configuración
        "group_settings": "⚙️ Configuración",
        "chk_remember_passwords": "Recordar contraseñas",
        "chk_auto_connect": "Auto-conectar a hosts conocidos",
        "label_port": "Puerto:",
        "btn_save_settings": "💾 Guardar Configuración",
        "label_language": "Idioma / Language:",
        # Pestaña Red
        "group_network": "📡 Información de Red",
        "label_available_ips": "Direcciones IP disponibles:",
        # Donación
        "group_donate": "❤️ Apoyar el Proyecto",
        "donate_label": "Si AlbertDesk te es útil, ¡invítame una cerveza!",
        "btn_donate": "🍺 Cómprame una cerveza",
        "donate_tooltip": "¡Apoya el desarrollo de AlbertDesk con una donación en PayPal!",
        # Mensajes de estado
        "msg_copied": "📋 Copiado: {}",
        "msg_new_password": "🔄 Nueva contraseña generada",
        "msg_settings_saved": "✅ Configuración guardada",
        "msg_network_updated": "🔄 Información actualizada",
        "msg_file_sent": "✅ Archivo enviado",
        "msg_restart_port": "⚠️ Reinicia la app para aplicar nuevo puerto",
        # Errores
        "err_enter_ip": "Ingresa una IP o ID",
        "err_invalid_port": "Puerto debe ser un número válido",
        "err_no_connection_file": "Conéctate primero a un equipo remoto",
        "err_cannot_send_file": "No se pudo enviar el archivo",
        "err_no_tunnel_url": "No hay URL de tunnel disponible",
        # Diálogos de autenticación
        "auth_title": "Autenticación",
        "auth_label": "Contraseña para {}:",
        "auth_failed_title": "Autenticación Fallida",
        "auth_failed_label": "Contraseña incorrecta para {}.",
        # Tunnel
        "tunnel_not_installed_title": "Cloudflare no instalado",
        "tunnel_not_installed_msg": "Por favor instala Cloudflare Tunnel primero.\n\n{}",
        "tunnel_error": "No se pudo iniciar Cloudflare Tunnel",
        "tunnel_already_installed_title": "Ya instalado",
        "tunnel_already_installed_msg": (
            "✅ Cloudflared ya está instalado en tu sistema.\n\n"
            "Puedes usar el botón 'Iniciar Tunnel' directamente."
        ),
        "tunnel_install_confirm_title": "Instalar Cloudflare Tunnel",
        "tunnel_install_confirm_msg": (
            "¿Deseas instalar Cloudflare Tunnel automáticamente?\n\n"
            "La app descargará e instalará cloudflared desde GitHub.\n"
            "El proceso tomará unos minutos."
        ),
        "tunnel_installing_text": "⏳ Instalando...",
        "tunnel_install_success_title": "Instalación Completada",
        "tunnel_install_success_msg": (
            "✅ ¡Cloudflared instalado exitosamente!\n\n"
            "ℹ️ IMPORTANTE:\n"
            "Cierra y vuelve a abrir AlbertDesk para que los cambios\n"
            "en el PATH del sistema surtan efecto.\n\n"
            "Después podrás usar 'Iniciar Tunnel' sin problemas."
        ),
        "tunnel_stopped_status": "🔴 Tunnel detenido",
        "tunnel_url_stopped": "URL: (detenido)",
        "tunnel_active_status": "🟢 Tunnel activo",
        "status_connecting": "🟡 Conectando...",
        "install_manual_header": "INSTALACIÓN MANUAL DE CLOUDFLARE TUNNEL",
        "install_starting": "🚀 Iniciando instalación de Cloudflare Tunnel...",
        # Información de carpeta
        "folder_location": "Ubicación: {}",
    },
    "en": {
        # Window title
        "window_title": "AlbertDesk - Remote Desktop Control",
        # Tabs
        "tab_my_id": "🆔 My ID",
        "tab_connect": "🔗 Connect",
        "tab_remote_screen": "🖥️ Remote Screen",
        "tab_tunnel": "🌐 Internet (Tunnel)",
        "tab_settings": "⚙️ Settings",
        "tab_network": "📡 Network",
        # My ID tab
        "group_local_device": "Local Device",
        "btn_copy": "📋 Copy",
        "btn_generate": "🔄 Generate",
        "btn_refresh": "🔄 Refresh",
        # Connect tab
        "label_target": "Target (IP or remote device ID):",
        "placeholder_target": "192.168.1.100 or device ID",
        "label_known_hosts": "Known devices:",
        "status_disconnected": "🔴 Disconnected",
        "btn_connect": "🔗 Connect",
        "btn_disconnect": "⛔ Disconnect",
        # Remote screen tab
        "btn_send_file": "📤 Send file",
        "btn_recv_folder": "📥 Downloads folder",
        "btn_fullscreen": "⛶ Full Screen",
        # Tunnel tab
        "group_tunnel": "🌐 Cloudflare Tunnel - Connect via Internet",
        "tunnel_info": (
            "Use Cloudflare Tunnel to connect over the internet without needing "
            "your own server. Completely free."
        ),
        "tunnel_status_unconfigured": "❓ Not configured",
        "btn_install_tunnel": "📥 Install Cloudflare Tunnel",
        "btn_start_tunnel": "▶️ Start Tunnel",
        "btn_stop_tunnel": "⏹️ Stop Tunnel",
        "tunnel_url_waiting": "URL: (waiting...)",
        "btn_copy_url": "📋 Copy URL",
        "group_terminal": "💻 Terminal / Installation",
        "terminal_placeholder": (
            "Installation terminal and Cloudflare Tunnel output...\n\n"
            "Click 'Install Cloudflare Tunnel' to see installation instructions."
        ),
        "btn_clear_terminal": "🗑️ Clear Terminal",
        # Settings tab
        "group_settings": "⚙️ Settings",
        "chk_remember_passwords": "Remember passwords",
        "chk_auto_connect": "Auto-connect to known hosts",
        "label_port": "Port:",
        "btn_save_settings": "💾 Save Settings",
        "label_language": "Idioma / Language:",
        # Network tab
        "group_network": "📡 Network Information",
        "label_available_ips": "Available IP addresses:",
        # Donation
        "group_donate": "❤️ Support the Project",
        "donate_label": "If AlbertDesk is useful to you, buy me a beer!",
        "btn_donate": "🍺 Buy me a beer",
        "donate_tooltip": "Support AlbertDesk development with a PayPal donation!",
        # Status messages
        "msg_copied": "📋 Copied: {}",
        "msg_new_password": "🔄 New password generated",
        "msg_settings_saved": "✅ Settings saved",
        "msg_network_updated": "🔄 Information updated",
        "msg_file_sent": "✅ File sent",
        "msg_restart_port": "⚠️ Restart the app to apply new port",
        # Errors
        "err_enter_ip": "Enter an IP or ID",
        "err_invalid_port": "Port must be a valid number",
        "err_no_connection_file": "Connect to a remote device first",
        "err_cannot_send_file": "Could not send the file",
        "err_no_tunnel_url": "No tunnel URL available",
        # Auth dialogs
        "auth_title": "Authentication",
        "auth_label": "Password for {}:",
        "auth_failed_title": "Authentication Failed",
        "auth_failed_label": "Wrong password for {}.",
        # Tunnel
        "tunnel_not_installed_title": "Cloudflare not installed",
        "tunnel_not_installed_msg": "Please install Cloudflare Tunnel first.\n\n{}",
        "tunnel_error": "Could not start Cloudflare Tunnel",
        "tunnel_already_installed_title": "Already installed",
        "tunnel_already_installed_msg": (
            "✅ Cloudflared is already installed on your system.\n\n"
            "You can use the 'Start Tunnel' button directly."
        ),
        "tunnel_install_confirm_title": "Install Cloudflare Tunnel",
        "tunnel_install_confirm_msg": (
            "Do you want to install Cloudflare Tunnel automatically?\n\n"
            "The app will download and install cloudflared from GitHub.\n"
            "The process will take a few minutes."
        ),
        "tunnel_installing_text": "⏳ Installing...",
        "tunnel_install_success_title": "Installation Complete",
        "tunnel_install_success_msg": (
            "✅ Cloudflared installed successfully!\n\n"
            "ℹ️ IMPORTANT:\n"
            "Close and reopen AlbertDesk for the PATH changes to take effect.\n\n"
            "Then you can use 'Start Tunnel' without issues."
        ),
        "tunnel_stopped_status": "🔴 Tunnel stopped",
        "tunnel_url_stopped": "URL: (stopped)",
        "tunnel_active_status": "🟢 Tunnel active",
        "status_connecting": "🟡 Connecting...",
        "install_manual_header": "MANUAL CLOUDFLARE TUNNEL INSTALLATION",
        "install_starting": "🚀 Starting Cloudflare Tunnel installation...",
        "folder_location": "Location: {}",
    },
}


def set_language(lang: str) -> None:
    """Establece el idioma activo. Valores válidos: 'es', 'en'."""
    global _CURRENT_LANG
    if lang in TRANSLATIONS:
        _CURRENT_LANG = lang


def get_language() -> str:
    """Devuelve el código del idioma actual."""
    return _CURRENT_LANG


def tr(key: str, *args) -> str:
    """
    Traduce una clave al idioma actual.
    Si la clave no existe en el idioma actual, cae a español.
    Si no existe en ninguno, devuelve la clave tal cual.
    """
    lang_dict = TRANSLATIONS.get(_CURRENT_LANG, TRANSLATIONS["es"])
    text = lang_dict.get(key, TRANSLATIONS["es"].get(key, key))
    if args:
        return text.format(*args)
    return text
