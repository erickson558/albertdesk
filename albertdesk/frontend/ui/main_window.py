"""
Main application window for AlbertDesk.
"""

import os
import sys
import threading
import uuid
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLineEdit, QLabel, QStatusBar, QGroupBox, QGridLayout,
    QMessageBox, QInputDialog, QFileDialog, QListWidget, QListWidgetItem,
    QCheckBox, QScrollArea
)
from PyQt5.QtGui import QFont, QDesktopServices
from PyQt5.QtCore import Qt, QTimer, QUrl, pyqtSlot, threading as qtthreading
from PyQt5.QtCore import QMetaObject, Q_ARG

from ...backend.core.config import Config, load_json, save_json
from ...backend.core.logger import get_logger
from ...backend.core.utils import generate_id, generate_password, get_available_ips
from ...backend.network.connection_manager import ConnectionManager, RECEIVED_DIR
from ...backend.network.cloudflare_tunnel import CloudflareTunnelManager
from ...frontend.widgets.remote_desktop_widget import RemoteDesktopWidget
from ...frontend.widgets.fullscreen_window import RemoteFullscreenWindow

logger = get_logger(__name__)

HOSTS_FILE = "hosts.json"


class AlbertDeskWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.setWindowTitle("AlbertDesk - Remote Desktop Control")
        self.setGeometry(100, 100, 1300, 850)
        self.setFont(QFont("Segoe UI", 10))
        
        # Configuration
        self.config = Config()
        self.hosts = load_json(HOSTS_FILE, {})
        
        # Connection manager
        self.conn_manager = ConnectionManager(self.config.data)
        self.conn_manager_thread = threading.Thread(
            target=self.conn_manager.start_server,
            daemon=True
        )
        self.conn_manager_thread.start()
        
        # Cloudflare Tunnel manager
        self.tunnel_manager = CloudflareTunnelManager(
            on_status_change=self._on_tunnel_status_change
        )
        
        # Fullscreen window
        self._fs_win: Optional[RemoteFullscreenWindow] = None
        
        # Connection state
        self._last_target_label: Optional[str] = None
        self._last_target_ip: Optional[str] = None
        self._last_password: str = ""
        
        # UI Components
        self.tabs: Optional[QTabWidget] = None
        self.status_bar: Optional[QStatusBar] = None
        self.remote_screen: Optional[RemoteDesktopWidget] = None
        
        # Initialize UI
        self._init_ui()
        self._setup_connections()
        
        logger.info("AlbertDesk window initialized")
    
    def _init_ui(self) -> None:
        """Initialize user interface."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.tabs.addTab(self._create_my_id_tab(), "🆔 Mi ID")
        self.tabs.addTab(self._create_connect_tab(), "🔗 Conectar")
        self.tabs.addTab(self._create_remote_screen_tab(), "🖥️ Pantalla Remota")
        self.tabs.addTab(self._create_tunnel_tab(), "🌐 Internet (Tunnel)")
        self.tabs.addTab(self._create_settings_tab(), "⚙️ Configuración")
        self.tabs.addTab(self._create_network_info_tab(), "📡 Red")
    
    def _create_my_id_tab(self) -> QWidget:
        """Create 'Mi ID' tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        group = QGroupBox("Dispositivo Local")
        grid = QGridLayout()
        
        # ID
        id_layout = QHBoxLayout()
        self.id_label = QLabel(f"🆔 ID: {self.config['id']}")
        self.id_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.id_label.setFont(QFont("Courier", 10))
        copy_id_btn = QPushButton("📋 Copiar")
        copy_id_btn.clicked.connect(lambda: self._copy_to_clipboard(self.config['id']))
        id_layout.addWidget(self.id_label, 1)
        id_layout.addWidget(copy_id_btn)
        
        # Password
        pwd_layout = QHBoxLayout()
        self.pwd_label = QLabel(f"🔐 Contraseña: {self.config['password']}")
        self.pwd_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.pwd_label.setFont(QFont("Courier", 10))
        copy_pwd_btn = QPushButton("📋 Copiar")
        copy_pwd_btn.clicked.connect(lambda: self._copy_to_clipboard(self.config['password']))
        generate_pwd_btn = QPushButton("🔄 Generar")
        generate_pwd_btn.clicked.connect(self._generate_new_password)
        pwd_layout.addWidget(self.pwd_label, 1)
        pwd_layout.addWidget(copy_pwd_btn)
        pwd_layout.addWidget(generate_pwd_btn)
        
        # Port
        self.port_label = QLabel(f"🚪 Puerto: {self.config['port']}")
        self.port_label.setFont(QFont("Courier", 10))
        
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.clicked.connect(self._update_local_info)
        
        grid.addLayout(id_layout, 0, 0)
        grid.addLayout(pwd_layout, 1, 0)
        grid.addWidget(self.port_label, 2, 0)
        grid.addWidget(refresh_btn, 3, 0)
        
        group.setLayout(grid)
        layout.addWidget(group)
        layout.addStretch()
        tab.setLayout(layout)
        
        return tab
    
    def _create_connect_tab(self) -> QWidget:
        """Create connection tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Target input
        layout.addWidget(QLabel("Destino (IP o ID del equipo remoto):"))
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("192.168.1.100 o ID del equipo")
        layout.addWidget(self.target_input)
        
        # Known hosts
        layout.addWidget(QLabel("Equipos conocidos:"))
        self.hosts_list = QListWidget()
        self.hosts_list.itemClicked.connect(self._on_host_selected)
        self._update_hosts_list()
        layout.addWidget(self.hosts_list)
        
        # Connection status
        self.connection_status_lbl = QLabel("🔴 Desconectado")
        self.connection_status_lbl.setStyleSheet("font-weight: bold; font-size: 12px;")
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("🔗 Conectar")
        self.connect_btn.clicked.connect(self._connect_to_target)
        self.disconnect_btn = QPushButton("⛔ Desconectar")
        self.disconnect_btn.clicked.connect(self._disconnect_from_host)
        self.disconnect_btn.setEnabled(False)
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.disconnect_btn)
        
        layout.addWidget(self.connection_status_lbl)
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def _create_remote_screen_tab(self) -> QWidget:
        """Create remote desktop viewer tab."""
        tab = QWidget()
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        
        # Control bar
        ctrl_bar = QWidget()
        ctrl_layout = QHBoxLayout(ctrl_bar)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)
        
        self.send_file_btn = QPushButton("📤 Enviar archivo")
        self.send_file_btn.clicked.connect(self._choose_and_send_file)
        
        self.open_recv_btn = QPushButton("📥 Carpeta descargas")
        self.open_recv_btn.clicked.connect(self._open_received_folder)
        
        self.remote_disconnect_btn = QPushButton("⛔ Desconectar")
        self.remote_disconnect_btn.clicked.connect(self._disconnect_from_host)
        self.remote_disconnect_btn.setEnabled(False)
        
        self.fullscreen_btn = QPushButton("⛶ Pantalla Completa")
        self.fullscreen_btn.clicked.connect(self._enter_remote_fullscreen)
        
        ctrl_layout.addWidget(self.send_file_btn)
        ctrl_layout.addWidget(self.open_recv_btn)
        ctrl_layout.addWidget(self.remote_disconnect_btn)
        ctrl_layout.addWidget(self.fullscreen_btn)
        ctrl_layout.addStretch()
        
        outer.addWidget(ctrl_bar)
        
        # Remote screen viewer
        self.remote_screen = RemoteDesktopWidget()
        self.remote_screen.setStyleSheet("background-color: black;")
        self.remote_screen.request_fullscreen.connect(self._enter_remote_fullscreen)
        
        outer.addWidget(self.remote_screen, 1)
        
        return tab
    
    def _create_tunnel_tab(self) -> QWidget:
        """Create Cloudflare Tunnel tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        group = QGroupBox("🌐 Cloudflare Tunnel - Conecta por Internet")
        grid = QGridLayout()
        
        info_label = QLabel(
            "Usa Cloudflare Tunnel para conectarte a través de internet sin necesidad "
            "de un servidor propio. Completamente gratis."
        )
        info_label.setWordWrap(True)
        
        self.tunnel_status_lbl = QLabel("❓ No configurado")
        self.tunnel_status_lbl.setStyleSheet("font-weight: bold; font-size: 11px;")
        
        # Check installation
        self.install_tunnel_btn = QPushButton("📥 Instalar Cloudflare Tunnel")
        self.install_tunnel_btn.clicked.connect(self._show_tunnel_install_instructions)
        
        self.start_tunnel_btn = QPushButton("▶️ Iniciar Tunnel")
        self.start_tunnel_btn.clicked.connect(self._start_tunnel)
        
        self.stop_tunnel_btn = QPushButton("⏹️ Detener Tunnel")
        self.stop_tunnel_btn.clicked.connect(self._stop_tunnel)
        self.stop_tunnel_btn.setEnabled(False)
        
        self.tunnel_url_lbl = QLabel("URL: (esperando...)")
        self.tunnel_url_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.tunnel_url_lbl.setFont(QFont("Courier", 9))
        
        copy_tunnel_btn = QPushButton("📋 Copiar URL")
        copy_tunnel_btn.clicked.connect(self._copy_tunnel_url)
        
        grid.addWidget(info_label, 0, 0, 1, 2)
        grid.addWidget(self.tunnel_status_lbl, 1, 0, 1, 2)
        grid.addWidget(self.install_tunnel_btn, 2, 0, 1, 2)
        grid.addWidget(self.start_tunnel_btn, 3, 0)
        grid.addWidget(self.stop_tunnel_btn, 3, 1)
        grid.addWidget(self.tunnel_url_lbl, 4, 0, 1, 2)
        grid.addWidget(copy_tunnel_btn, 5, 0, 1, 2)
        
        group.setLayout(grid)
        layout.addWidget(group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def _create_settings_tab(self) -> QWidget:
        """Create settings tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        group = QGroupBox("⚙️ Configuración")
        grid = QGridLayout()
        
        self.remember_passwords_chk = QCheckBox("Recordar contraseñas")
        self.remember_passwords_chk.setChecked(self.config.get("remember_passwords", True))
        
        self.auto_connect_chk = QCheckBox("Auto-conectar a hosts conocidos")
        self.auto_connect_chk.setChecked(self.config.get("auto_connect", False))
        
        # Port settings
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Puerto:"))
        self.port_input = QLineEdit(str(self.config.get("port", 6969)))
        self.port_input.setMaximumWidth(100)
        port_layout.addWidget(self.port_input)
        port_layout.addStretch()
        
        save_btn = QPushButton("💾 Guardar Configuración")
        save_btn.clicked.connect(self._save_settings)
        
        grid.addWidget(self.remember_passwords_chk, 0, 0)
        grid.addWidget(self.auto_connect_chk, 1, 0)
        grid.addLayout(port_layout, 2, 0)
        grid.addWidget(save_btn, 3, 0)
        
        group.setLayout(grid)
        layout.addWidget(group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def _create_network_info_tab(self) -> QWidget:
        """Create network information tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        group = QGroupBox("📡 Información de Red")
        grid = QGridLayout()
        
        self.ip_list = QListWidget()
        self.ip_list.setSelectionMode(QListWidget.NoSelection)
        self._update_network_info()
        
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.clicked.connect(self._update_network_info)
        
        grid.addWidget(QLabel("Direcciones IP disponibles:"), 0, 0)
        grid.addWidget(self.ip_list, 1, 0)
        grid.addWidget(refresh_btn, 2, 0)
        
        group.setLayout(grid)
        layout.addWidget(group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def _setup_connections(self) -> None:
        """Setup signal connections."""
        self.conn_manager.connection_status.connect(self._on_connection_status)
        self.conn_manager.connection_established.connect(self._on_connection_established)
        self.conn_manager.connection_lost.connect(self._on_connection_lost)
        self.conn_manager.frame_received.connect(self.remote_screen.display_frame)
        self.conn_manager.screens_received.connect(self._on_screens_received)
        self.conn_manager.auth_required.connect(self._request_password)
        
        self.remote_screen.mouse_event.connect(self._send_mouse_event)
        self.remote_screen.keyboard_event.connect(self._send_keyboard_event)
    
    @pyqtSlot(str)
    def _on_connection_status(self, status: str) -> None:
        """Update connection status display."""
        self.connection_status_lbl.setText(status)
        self.status_bar.showMessage(status, 5000)
    
    @pyqtSlot(object)
    def _on_connection_established(self, sock) -> None:
        """Handle successful connection."""
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.remote_disconnect_btn.setEnabled(True)
        self.connection_status_lbl.setText("🟢 Conectado")
        self.tabs.setCurrentIndex(2)  # Switch to remote screen tab
        self.remote_screen.setFocus()
        
        # Save connection info
        if self._last_target_ip:
            self._remember_host(
                self._last_target_label or self._last_target_ip,
                self._last_target_ip
            )
            if self.config.get('remember_passwords', True) and self._last_password:
                saved_pwd = self.config.get('saved_passwords', {})
                saved_pwd[self._last_target_label] = self._last_password
                self.config['saved_passwords'] = saved_pwd
                self.config.save()
    
    @pyqtSlot()
    def _on_connection_lost(self) -> None:
        """Handle connection lost."""
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.remote_disconnect_btn.setEnabled(False)
        self.connection_status_lbl.setText("🔴 Desconectado")
        self.remote_screen.set_connection_status("failed")
        QTimer.singleShot(1200, lambda: self.remote_screen.set_connection_status("waiting"))
        
        if self._fs_win:
            try:
                self._fs_win.close()
            except Exception:
                self._fs_win = None
    
    def _connect_to_target(self) -> None:
        """Connect to a remote host."""
        target = self.target_input.text().strip()
        if not target:
            QMessageBox.warning(self, "Error", "Ingresa una IP o ID")
            return
        
        # Determine IP and ID
        if target in self.hosts:
            ip = self.hosts[target]
            host_id = target
        else:
            ip = target
            host_id = ""
        
        # Get password
        key_for_pwd = host_id if host_id else ip
        password = ""
        
        if self.remember_passwords_chk.isChecked():
            saved_pwd = self.config.get('saved_passwords', {}).get(key_for_pwd, "")
            if saved_pwd:
                password = saved_pwd
        
        if not password:
            password, ok = QInputDialog.getText(
                self,
                "Autenticación",
                f"Contraseña para {target}:",
                QLineEdit.Password
            )
            if not ok or not password:
                return
        
        # Save connection state
        self._last_target_label = key_for_pwd
        self._last_target_ip = ip
        self._last_password = password
        
        # Update UI
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.remote_disconnect_btn.setEnabled(True)
        self.connection_status_lbl.setText("🟡 Conectando...")
        self.remote_screen.set_connection_status("connecting")
        
        # Connect in thread
        threading.Thread(
            target=self.conn_manager.connect_to_host,
            args=(ip, self.config['port'], password, host_id),
            daemon=True
        ).start()
    
    def _disconnect_from_host(self) -> None:
        """Disconnect from remote host."""
        self.conn_manager.disconnect()
    
    @pyqtSlot(str)
    def _request_password(self, target_id: str) -> None:
        """Request password retry."""
        QMetaObject.invokeMethod(
            self, "_show_password_dialog", Qt.QueuedConnection, Q_ARG(str, target_id)
        )
    
    @pyqtSlot(str)
    def _show_password_dialog(self, target_id: str) -> None:
        """Show password dialog for failed authentication."""
        password, ok = QInputDialog.getText(
            self,
            "Autenticación Fallida",
            f"Contraseña incorrecta para {target_id}.",
            QLineEdit.Password
        )
        if ok and password:
            ip = self.hosts.get(target_id, target_id)
            self._last_target_label = target_id
            self._last_target_ip = ip
            self._last_password = password
            threading.Thread(
                target=self.conn_manager.connect_to_host,
                args=(ip, self.config['port'], password, target_id),
                daemon=True
            ).start()
    
    def _update_hosts_list(self) -> None:
        """Update known hosts list."""
        self.hosts_list.clear()
        for name, ip in self.hosts.items():
            item = QListWidgetItem(f"{name} ({ip})")
            self.hosts_list.addItem(item)
    
    def _on_host_selected(self, item: QListWidgetItem) -> None:
        """Handle host selection from list."""
        text = item.text()
        name = text.split(" (")[0].strip() if " (" in text else text
        self.target_input.setText(name)
    
    def _remember_host(self, name: str, ip: str) -> None:
        """Save a host to known hosts."""
        self.hosts[name] = ip
        save_json(HOSTS_FILE, self.hosts)
        self._update_hosts_list()
    
    def _choose_and_send_file(self) -> None:
        """Choose and send file to remote."""
        if not self.conn_manager.is_connected:
            QMessageBox.information(self, "Error", "Conéctate primero a un equipo remoto")
            return
        
        path, _ = QFileDialog.getOpenFileName(self, "Selecciona archivo para enviar")
        if path:
            if self.conn_manager.send_file(path):
                self.status_bar.showMessage("✅ Archivo enviado", 3000)
            else:
                QMessageBox.warning(self, "Error", "No se pudo enviar el archivo")
    
    def _open_received_folder(self) -> None:
        """Open received files folder."""
        os.makedirs(RECEIVED_DIR, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(RECEIVED_DIR)
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(RECEIVED_DIR)))
        except Exception as e:
            QMessageBox.information(self, "Carpeta", f"Ubicación: {os.path.abspath(RECEIVED_DIR)}")
    
    def _enter_remote_fullscreen(self) -> None:
        """Enter fullscreen mode for remote desktop."""
        if self._fs_win:
            try:
                self._fs_win.close()
            except Exception:
                pass
        
        self._fs_win = RemoteFullscreenWindow(
            self.remote_screen,
            self._exit_full_screen
        )
        self._fs_win.showFullScreen()
    
    def _exit_full_screen(self, widget) -> None:
        """Exit fullscreen mode."""
        self._fs_win = None
        self.tabs.setCurrentIndex(2)
    
    @pyqtSlot(bytes)
    def _send_mouse_event(self, event_data: bytes) -> None:
        """Send mouse event to remote."""
        if self.conn_manager.is_connected and self.conn_manager.socket:
            try:
                from ...backend.core.utils import pack_message
                self.conn_manager.socket.sendall(pack_message(event_data))
            except Exception as e:
                logger.error(f"Error sending mouse event: {e}")
    
    @pyqtSlot(bytes)
    def _send_keyboard_event(self, event_data: bytes) -> None:
        """Send keyboard event to remote."""
        if self.conn_manager.is_connected and self.conn_manager.socket:
            try:
                from ...backend.core.utils import pack_message
                self.conn_manager.socket.sendall(pack_message(event_data))
            except Exception as e:
                logger.error(f"Error sending keyboard event: {e}")
    
    @pyqtSlot(list)
    def _on_screens_received(self, screens: list) -> None:
        """Handle screens list received from server."""
        logger.debug(f"Screens received: {len(screens)}")
    
    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard."""
        from PyQt5.QtWidgets import QApplication
        QApplication.clipboard().setText(text)
        self.status_bar.showMessage(f"📋 Copiado: {text}", 3000)
    
    def _generate_new_password(self) -> None:
        """Generate a new password."""
        self.config['password'] = generate_password()
        self.pwd_label.setText(f"🔐 Contraseña: {self.config['password']}")
        self.config.save()
        self.status_bar.showMessage("🔄 Nueva contraseña generada", 3000)
    
    def _save_settings(self) -> None:
        """Save application settings."""
        try:
            port = int(self.port_input.text())
            if port != self.config['port']:
                self.config['port'] = port
                self.port_label.setText(f"🚪 Puerto: {port}")
                self.config.save()
                self.status_bar.showMessage("⚠️ Reinicia la app para aplicar nuevo puerto", 5000)
        except ValueError:
            QMessageBox.warning(self, "Error", "Puerto debe ser un número válido")
            return
        
        self.config['remember_passwords'] = self.remember_passwords_chk.isChecked()
        self.config['auto_connect'] = self.auto_connect_chk.isChecked()
        self.config.save()
        self._update_network_info()
        self.status_bar.showMessage("✅ Configuración guardada", 3000)
    
    def _update_network_info(self) -> None:
        """Update network information display."""
        self.ip_list.clear()
        ips = get_available_ips()
        for ip in ips:
            item = QListWidgetItem(f"🌐 {ip}")
            self.ip_list.addItem(item)
    
    def _update_local_info(self) -> None:
        """Update local device information."""
        self._update_network_info()
        self.status_bar.showMessage("🔄 Información actualizada", 3000)
    
    def _show_tunnel_install_instructions(self) -> None:
        """Show installation instructions for Cloudflare Tunnel."""
        instructions = self.tunnel_manager.get_installation_instructions()
        QMessageBox.information(self, "Instalar Cloudflare Tunnel", instructions)
    
    def _start_tunnel(self) -> None:
        """Start Cloudflare Tunnel."""
        if not self.tunnel_manager.is_cloudflare_installed():
            QMessageBox.warning(
                self,
                "Cloudflare no instalado",
                "Por favor instala Cloudflare Tunnel primero.\n\n" +
                self.tunnel_manager.get_installation_instructions()
            )
            return
        
        if self.tunnel_manager.start_tunnel(self.config['port']):
            self.start_tunnel_btn.setEnabled(False)
            self.stop_tunnel_btn.setEnabled(True)
            self.tunnel_status_lbl.setText("🟢 Tunnel activo")
        else:
            QMessageBox.critical(self, "Error", "No se pudo iniciar Cloudflare Tunnel")
    
    def _stop_tunnel(self) -> None:
        """Stop Cloudflare Tunnel."""
        self.tunnel_manager.stop_tunnel()
        self.start_tunnel_btn.setEnabled(True)
        self.stop_tunnel_btn.setEnabled(False)
        self.tunnel_status_lbl.setText("🔴 Tunnel detenido")
        self.tunnel_url_lbl.setText("URL: (detenido)")
    
    def _on_tunnel_status_change(self, status: str) -> None:
        """Handle tunnel status change."""
        self.tunnel_status_lbl.setText(status)
        if "https://" in status:
            self.tunnel_url_lbl.setText(f"URL: {status.split('URL Tunnel: ')[-1] if 'URL Tunnel: ' in status else status}")
    
    def _copy_tunnel_url(self) -> None:
        """Copy tunnel URL to clipboard."""
        url = self.tunnel_manager.get_tunnel_url()
        if url:
            self._copy_to_clipboard(url)
        else:
            QMessageBox.information(self, "Error", "No hay URL de tunnel disponible")
    
    def closeEvent(self, event):
        """Handle window close."""
        if self._fs_win:
            try:
                self._fs_win.close()
            except Exception:
                pass
        
        self.tunnel_manager.stop_tunnel()
        self.conn_manager.stop()
        event.accept()
        logger.info("AlbertDesk window closed")
