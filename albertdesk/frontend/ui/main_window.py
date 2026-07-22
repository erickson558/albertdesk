"""
Main application window for AlbertDesk.
Supports multi-language (ES/EN) via the i18n module.
"""

import os
import sys
import threading
import webbrowser
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLineEdit, QLabel, QStatusBar, QGroupBox, QGridLayout,
    QMessageBox, QInputDialog, QFileDialog, QListWidget, QListWidgetItem,
    QCheckBox, QComboBox, QPlainTextEdit, QApplication
)
from PyQt5.QtGui import QFont, QDesktopServices
from PyQt5.QtCore import Qt, QTimer, QUrl, pyqtSlot, pyqtSignal, QMetaObject, Q_ARG

from ...backend.core.config import Config, load_json, save_json
from ...backend.core.logger import get_logger
from ...backend.core.utils import generate_id, generate_password, get_available_ips
from ...backend.network.connection_manager import ConnectionManager, RECEIVED_DIR
from ...backend.network.cloudflare_tunnel import CloudflareTunnelManager
from ...frontend.widgets.remote_desktop_widget import RemoteDesktopWidget
from ...frontend.widgets.fullscreen_window import RemoteFullscreenWindow
from ...i18n import tr, set_language, get_language

logger = get_logger(__name__)

# Archivo de hosts conocidos
HOSTS_FILE = "hosts.json"

# URL de donación PayPal
DONATE_URL = "https://www.paypal.com/donate/?hosted_button_id=ZABFRXC2P3JQN"


class AlbertDeskWindow(QMainWindow):
    """Ventana principal de AlbertDesk con soporte multi-idioma."""

    # Señal interna para actualizar el estado del tunnel de forma thread-safe.
    # El callback de CloudflareTunnelManager se llama desde un hilo secundario,
    # por lo que no podemos tocar widgets Qt directamente desde él.
    _tunnel_status_signal = pyqtSignal(str)

    def __init__(self):
        """Inicializa la ventana principal."""
        super().__init__()
        self.setGeometry(100, 100, 1300, 850)
        self.setFont(QFont("Segoe UI", 10))

        # Configuración persistente
        self.config = Config()
        self.hosts = load_json(HOSTS_FILE, {})

        # Aplicar idioma guardado en config (si existe)
        saved_lang = self.config.get("language", "es")
        set_language(saved_lang)

        # Gestor de conexiones — inicia el servidor en hilo daemon
        self.conn_manager = ConnectionManager(self.config.data)
        self.conn_manager_thread = threading.Thread(
            target=self.conn_manager.start_server,
            daemon=True
        )
        self.conn_manager_thread.start()

        # Gestor del tunnel Cloudflare
        self.tunnel_manager = CloudflareTunnelManager(
            on_status_change=self._on_tunnel_status_change,
            on_output=self._on_tunnel_output
        )

        # Ventana de pantalla completa (opcional)
        self._fs_win: Optional[RemoteFullscreenWindow] = None

        # Estado de la última conexión iniciada
        self._last_target_label: Optional[str] = None
        self._last_target_ip: Optional[str] = None
        self._last_password: str = ""

        # Componentes principales de la UI (se asignan en _init_ui)
        self.tabs: Optional[QTabWidget] = None
        self.status_bar: Optional[QStatusBar] = None
        self.remote_screen: Optional[RemoteDesktopWidget] = None

        # Conectar la señal thread-safe del tunnel a su slot en el hilo GUI
        self._tunnel_status_signal.connect(self._update_tunnel_status_ui)

        # Construir interfaz y conectar señales
        self._init_ui()
        self._setup_connections()

        logger.info("AlbertDesk window initialized")

    # ─────────────────────────────────────────────────────────────────────────
    # CONSTRUCCIÓN DE LA UI
    # ─────────────────────────────────────────────────────────────────────────

    def _init_ui(self) -> None:
        """Construye la interfaz de usuario completa."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Crear pestañas
        self.tabs.addTab(self._create_my_id_tab(), "")
        self.tabs.addTab(self._create_connect_tab(), "")
        self.tabs.addTab(self._create_remote_screen_tab(), "")
        self.tabs.addTab(self._create_tunnel_tab(), "")
        self.tabs.addTab(self._create_settings_tab(), "")
        self.tabs.addTab(self._create_network_info_tab(), "")

        # Aplicar todos los textos según el idioma activo
        self._retranslate_ui()

    def _create_my_id_tab(self) -> QWidget:
        """Pestaña que muestra el ID, contraseña y puerto del dispositivo local."""
        tab = QWidget()
        layout = QVBoxLayout()

        # Grupo principal
        self._grp_local_device = QGroupBox()
        grid = QGridLayout()

        # Fila ID
        id_layout = QHBoxLayout()
        self.id_label = QLabel(f"🆔 ID: {self.config['id']}")
        self.id_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.id_label.setFont(QFont("Courier", 10))
        self._copy_id_btn = QPushButton()
        self._copy_id_btn.clicked.connect(lambda: self._copy_to_clipboard(self.config['id']))
        id_layout.addWidget(self.id_label, 1)
        id_layout.addWidget(self._copy_id_btn)

        # Fila contraseña
        pwd_layout = QHBoxLayout()
        self.pwd_label = QLabel(f"🔐 {tr('label_password')}: {self.config['password']}")
        self.pwd_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.pwd_label.setFont(QFont("Courier", 10))
        self._copy_pwd_btn = QPushButton()
        self._copy_pwd_btn.clicked.connect(
            lambda: self._copy_to_clipboard(self.config['password'])
        )
        self._generate_pwd_btn = QPushButton()
        self._generate_pwd_btn.clicked.connect(self._generate_new_password)
        pwd_layout.addWidget(self.pwd_label, 1)
        pwd_layout.addWidget(self._copy_pwd_btn)
        pwd_layout.addWidget(self._generate_pwd_btn)

        # Puerto
        self.port_label = QLabel(f"🚪 {tr('label_port')} {self.config['port']}")
        self.port_label.setFont(QFont("Courier", 10))

        # Botón actualizar
        self._refresh_id_btn = QPushButton()
        self._refresh_id_btn.clicked.connect(self._update_local_info)

        grid.addLayout(id_layout, 0, 0)
        grid.addLayout(pwd_layout, 1, 0)
        grid.addWidget(self.port_label, 2, 0)
        grid.addWidget(self._refresh_id_btn, 3, 0)

        self._grp_local_device.setLayout(grid)
        layout.addWidget(self._grp_local_device)
        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def _create_connect_tab(self) -> QWidget:
        """Pestaña para conectarse a un equipo remoto."""
        tab = QWidget()
        layout = QVBoxLayout()

        # Etiqueta destino
        self._lbl_target = QLabel()
        layout.addWidget(self._lbl_target)

        # Campo de entrada IP/ID
        self.target_input = QLineEdit()
        layout.addWidget(self.target_input)

        # Lista de hosts conocidos
        self._lbl_known_hosts = QLabel()
        layout.addWidget(self._lbl_known_hosts)

        self.hosts_list = QListWidget()
        self.hosts_list.itemClicked.connect(self._on_host_selected)
        self._update_hosts_list()
        layout.addWidget(self.hosts_list)

        # Estado de conexión
        self.connection_status_lbl = QLabel()
        self.connection_status_lbl.setStyleSheet("font-weight: bold; font-size: 12px;")

        # Botones conectar / desconectar
        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton()
        self.connect_btn.clicked.connect(self._connect_to_target)
        self.disconnect_btn = QPushButton()
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
        """Pestaña con el visor de escritorio remoto y controles."""
        tab = QWidget()
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)

        # Barra de controles
        ctrl_bar = QWidget()
        ctrl_layout = QHBoxLayout(ctrl_bar)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)

        self.send_file_btn = QPushButton()
        self.send_file_btn.clicked.connect(self._choose_and_send_file)

        self.open_recv_btn = QPushButton()
        self.open_recv_btn.clicked.connect(self._open_received_folder)

        self.remote_disconnect_btn = QPushButton()
        self.remote_disconnect_btn.clicked.connect(self._disconnect_from_host)
        self.remote_disconnect_btn.setEnabled(False)

        self.fullscreen_btn = QPushButton()
        self.fullscreen_btn.clicked.connect(self._enter_remote_fullscreen)

        ctrl_layout.addWidget(self.send_file_btn)
        ctrl_layout.addWidget(self.open_recv_btn)
        ctrl_layout.addWidget(self.remote_disconnect_btn)
        ctrl_layout.addWidget(self.fullscreen_btn)
        ctrl_layout.addStretch()

        outer.addWidget(ctrl_bar)

        # Widget de pantalla remota
        self.remote_screen = RemoteDesktopWidget()
        self.remote_screen.setStyleSheet("background-color: black;")
        self.remote_screen.request_fullscreen.connect(self._enter_remote_fullscreen)

        outer.addWidget(self.remote_screen, 1)
        # Se guarda para poder reinsertar remote_screen aquí al salir de
        # pantalla completa (RemoteFullscreenWindow lo reparenta a su propio
        # layout mientras dura el modo fullscreen).
        self._remote_tab_layout = outer
        return tab

    def _create_tunnel_tab(self) -> QWidget:
        """Pestaña para gestionar el túnel Cloudflare."""
        tab = QWidget()
        layout = QVBoxLayout()

        # Grupo principal del tunnel
        self._grp_tunnel = QGroupBox()
        grid = QGridLayout()

        self._tunnel_info_lbl = QLabel()
        self._tunnel_info_lbl.setWordWrap(True)

        self.tunnel_status_lbl = QLabel()
        self.tunnel_status_lbl.setStyleSheet("font-weight: bold; font-size: 11px;")

        self.install_tunnel_btn = QPushButton()
        self.install_tunnel_btn.clicked.connect(self._show_tunnel_install_instructions)

        self.start_tunnel_btn = QPushButton()
        self.start_tunnel_btn.clicked.connect(self._start_tunnel)

        self.stop_tunnel_btn = QPushButton()
        self.stop_tunnel_btn.clicked.connect(self._stop_tunnel)
        self.stop_tunnel_btn.setEnabled(False)

        self.tunnel_url_lbl = QLabel()
        self.tunnel_url_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.tunnel_url_lbl.setFont(QFont("Courier", 9))

        self._copy_tunnel_btn = QPushButton()
        self._copy_tunnel_btn.clicked.connect(self._copy_tunnel_url)

        grid.addWidget(self._tunnel_info_lbl, 0, 0, 1, 2)
        grid.addWidget(self.tunnel_status_lbl, 1, 0, 1, 2)
        grid.addWidget(self.install_tunnel_btn, 2, 0, 1, 2)
        grid.addWidget(self.start_tunnel_btn, 3, 0)
        grid.addWidget(self.stop_tunnel_btn, 3, 1)
        grid.addWidget(self.tunnel_url_lbl, 4, 0, 1, 2)
        grid.addWidget(self._copy_tunnel_btn, 5, 0, 1, 2)

        self._grp_tunnel.setLayout(grid)
        layout.addWidget(self._grp_tunnel)

        # Terminal de instalación / salida
        self._grp_terminal = QGroupBox()
        terminal_layout = QVBoxLayout()

        self.tunnel_terminal = QPlainTextEdit()
        self.tunnel_terminal.setReadOnly(True)
        self.tunnel_terminal.setMaximumBlockCount(1000)   # Límite de 1000 líneas para evitar memoria excesiva
        self.tunnel_terminal.setFont(QFont("Consolas", 9))
        self.tunnel_terminal.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
            }
        """)

        self._clear_terminal_btn = QPushButton()
        self._clear_terminal_btn.clicked.connect(lambda: self.tunnel_terminal.clear())

        terminal_layout.addWidget(self.tunnel_terminal)
        terminal_layout.addWidget(self._clear_terminal_btn)
        self._grp_terminal.setLayout(terminal_layout)
        layout.addWidget(self._grp_terminal, 1)   # Prioridad de expansión

        tab.setLayout(layout)
        return tab

    def _create_settings_tab(self) -> QWidget:
        """Pestaña de configuración general, idioma y donación."""
        tab = QWidget()
        layout = QVBoxLayout()

        # ── Grupo Configuración ──────────────────────────────────────────────
        self._grp_settings = QGroupBox()
        grid = QGridLayout()

        self.remember_passwords_chk = QCheckBox()
        self.remember_passwords_chk.setChecked(self.config.get("remember_passwords", True))

        self.auto_connect_chk = QCheckBox()
        self.auto_connect_chk.setChecked(self.config.get("auto_connect", False))

        # Puerto
        port_layout = QHBoxLayout()
        self._lbl_port = QLabel()
        self.port_input = QLineEdit(str(self.config.get("port", 6969)))
        self.port_input.setMaximumWidth(100)
        port_layout.addWidget(self._lbl_port)
        port_layout.addWidget(self.port_input)
        port_layout.addStretch()

        # Selector de idioma
        lang_layout = QHBoxLayout()
        self._lbl_language = QLabel()
        self._lang_combo = QComboBox()
        self._lang_combo.addItem("Español", "es")
        self._lang_combo.addItem("English", "en")
        current_lang = get_language()
        idx = self._lang_combo.findData(current_lang)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        self._lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_layout.addWidget(self._lbl_language)
        lang_layout.addWidget(self._lang_combo)
        lang_layout.addStretch()

        self._save_settings_btn = QPushButton()
        self._save_settings_btn.clicked.connect(self._save_settings)

        grid.addWidget(self.remember_passwords_chk, 0, 0)
        grid.addWidget(self.auto_connect_chk, 1, 0)
        grid.addLayout(port_layout, 2, 0)
        grid.addLayout(lang_layout, 3, 0)
        grid.addWidget(self._save_settings_btn, 4, 0)

        self._grp_settings.setLayout(grid)
        layout.addWidget(self._grp_settings)

        # ── Grupo Donación ───────────────────────────────────────────────────
        self._grp_donate = QGroupBox()
        donate_layout = QVBoxLayout()

        self._donate_info_lbl = QLabel()
        self._donate_info_lbl.setWordWrap(True)

        self._donate_btn = QPushButton()
        self._donate_btn.setStyleSheet("""
            QPushButton {
                background-color: #0070ba;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #005ea6;
            }
            QPushButton:pressed {
                background-color: #004f8f;
            }
        """)
        self._donate_btn.clicked.connect(self._open_donate_url)

        donate_layout.addWidget(self._donate_info_lbl)
        donate_layout.addWidget(self._donate_btn)
        donate_layout.addStretch()
        self._grp_donate.setLayout(donate_layout)
        layout.addWidget(self._grp_donate)

        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def _create_network_info_tab(self) -> QWidget:
        """Pestaña con información de red del dispositivo local."""
        tab = QWidget()
        layout = QVBoxLayout()

        self._grp_network = QGroupBox()
        grid = QGridLayout()

        self._lbl_available_ips = QLabel()
        self.ip_list = QListWidget()
        self.ip_list.setSelectionMode(QListWidget.NoSelection)
        self._update_network_info()

        self._refresh_net_btn = QPushButton()
        self._refresh_net_btn.clicked.connect(self._update_network_info)

        grid.addWidget(self._lbl_available_ips, 0, 0)
        grid.addWidget(self.ip_list, 1, 0)
        grid.addWidget(self._refresh_net_btn, 2, 0)

        self._grp_network.setLayout(grid)
        layout.addWidget(self._grp_network)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    # ─────────────────────────────────────────────────────────────────────────
    # TRADUCCIÓN DE LA UI
    # ─────────────────────────────────────────────────────────────────────────

    def _retranslate_ui(self) -> None:
        """
        Actualiza todos los textos de la UI al idioma activo.
        Se llama en el arranque y cada vez que el usuario cambia el idioma.
        """
        # Título de la ventana principal
        self.setWindowTitle(tr("window_title"))

        # Nombres de pestañas
        self.tabs.setTabText(0, tr("tab_my_id"))
        self.tabs.setTabText(1, tr("tab_connect"))
        self.tabs.setTabText(2, tr("tab_remote_screen"))
        self.tabs.setTabText(3, tr("tab_tunnel"))
        self.tabs.setTabText(4, tr("tab_settings"))
        self.tabs.setTabText(5, tr("tab_network"))

        # ── Pestaña Mi ID ────────────────────────────────────────────────────
        self._grp_local_device.setTitle(tr("group_local_device"))
        self._copy_id_btn.setText(tr("btn_copy"))
        self._copy_pwd_btn.setText(tr("btn_copy"))
        self._generate_pwd_btn.setText(tr("btn_generate"))
        self._refresh_id_btn.setText(tr("btn_refresh"))
        # Actualizar etiquetas dinámicas con el prefijo traducido al nuevo idioma
        self.pwd_label.setText(f"🔐 {tr('label_password')}: {self.config['password']}")
        self.port_label.setText(f"🚪 {tr('label_port')} {self.config['port']}")

        # ── Pestaña Conectar ─────────────────────────────────────────────────
        self._lbl_target.setText(tr("label_target"))
        self.target_input.setPlaceholderText(tr("placeholder_target"))
        self._lbl_known_hosts.setText(tr("label_known_hosts"))
        self.connection_status_lbl.setText(tr("status_disconnected"))
        self.connect_btn.setText(tr("btn_connect"))
        self.disconnect_btn.setText(tr("btn_disconnect"))

        # ── Pestaña Pantalla Remota ──────────────────────────────────────────
        self.send_file_btn.setText(tr("btn_send_file"))
        self.open_recv_btn.setText(tr("btn_recv_folder"))
        self.remote_disconnect_btn.setText(tr("btn_disconnect"))
        self.fullscreen_btn.setText(tr("btn_fullscreen"))

        # ── Pestaña Tunnel ───────────────────────────────────────────────────
        self._grp_tunnel.setTitle(tr("group_tunnel"))
        self._tunnel_info_lbl.setText(tr("tunnel_info"))
        self.tunnel_status_lbl.setText(tr("tunnel_status_unconfigured"))
        self.install_tunnel_btn.setText(tr("btn_install_tunnel"))
        self.start_tunnel_btn.setText(tr("btn_start_tunnel"))
        self.stop_tunnel_btn.setText(tr("btn_stop_tunnel"))
        self.tunnel_url_lbl.setText(tr("tunnel_url_waiting"))
        self._copy_tunnel_btn.setText(tr("btn_copy_url"))
        self._grp_terminal.setTitle(tr("group_terminal"))
        self.tunnel_terminal.setPlaceholderText(tr("terminal_placeholder"))
        self._clear_terminal_btn.setText(tr("btn_clear_terminal"))

        # ── Pestaña Configuración ────────────────────────────────────────────
        self._grp_settings.setTitle(tr("group_settings"))
        self.remember_passwords_chk.setText(tr("chk_remember_passwords"))
        self.auto_connect_chk.setText(tr("chk_auto_connect"))
        self._lbl_port.setText(tr("label_port"))
        self._lbl_language.setText(tr("label_language"))
        self._save_settings_btn.setText(tr("btn_save_settings"))

        self._grp_donate.setTitle(tr("group_donate"))
        self._donate_info_lbl.setText(tr("donate_label"))
        self._donate_btn.setText(tr("btn_donate"))
        self._donate_btn.setToolTip(tr("donate_tooltip"))

        # ── Pestaña Red ──────────────────────────────────────────────────────
        self._grp_network.setTitle(tr("group_network"))
        self._lbl_available_ips.setText(tr("label_available_ips"))
        self._refresh_net_btn.setText(tr("btn_refresh"))

    # ─────────────────────────────────────────────────────────────────────────
    # SEÑALES Y CONEXIONES
    # ─────────────────────────────────────────────────────────────────────────

    def _setup_connections(self) -> None:
        """Conecta señales del backend con slots de la UI."""
        self.conn_manager.connection_status.connect(self._on_connection_status)
        self.conn_manager.connection_established.connect(self._on_connection_established)
        self.conn_manager.connection_lost.connect(self._on_connection_lost)
        self.conn_manager.frame_received.connect(self.remote_screen.display_frame)
        self.conn_manager.screens_received.connect(self._on_screens_received)
        self.conn_manager.auth_required.connect(self._request_password)

        self.remote_screen.mouse_event.connect(self._send_mouse_event)
        self.remote_screen.keyboard_event.connect(self._send_keyboard_event)

    # ─────────────────────────────────────────────────────────────────────────
    # SLOTS DE CONEXIÓN
    # ─────────────────────────────────────────────────────────────────────────

    @pyqtSlot(str)
    def _on_connection_status(self, status: str) -> None:
        """Actualiza la barra de estado con mensajes del backend."""
        self.connection_status_lbl.setText(status)
        self.status_bar.showMessage(status, 5000)

    @pyqtSlot(object)
    def _on_connection_established(self, sock) -> None:
        """Maneja la conexión exitosa: actualiza UI y guarda credenciales."""
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.remote_disconnect_btn.setEnabled(True)
        self.connection_status_lbl.setText(tr("status_connected"))
        self.tabs.setCurrentIndex(2)   # Ir a pestaña de pantalla remota
        self.remote_screen.setFocus()

        # Guardar host y contraseña si están configurados
        if self._last_target_ip:
            label = self._last_target_label or self._last_target_ip
            self._remember_host(label, self._last_target_ip)
            if self.config.get("remember_passwords", True) and self._last_password and label:
                saved_pwd = self.config.get("saved_passwords", {})
                saved_pwd[label] = self._last_password
                self.config["saved_passwords"] = saved_pwd
                self.config.save()

    @pyqtSlot()
    def _on_connection_lost(self) -> None:
        """Maneja la desconexión: restaura botones y estado visual."""
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.remote_disconnect_btn.setEnabled(False)
        self.connection_status_lbl.setText(tr("status_disconnected"))
        self.remote_screen.set_connection_status("failed")
        QTimer.singleShot(1200, lambda: self.remote_screen.set_connection_status("waiting"))

        if self._fs_win:
            try:
                self._fs_win.close()
            except Exception:
                self._fs_win = None

    # ─────────────────────────────────────────────────────────────────────────
    # CONEXIÓN A HOST REMOTO
    # ─────────────────────────────────────────────────────────────────────────

    def _connect_to_target(self) -> None:
        """Inicia conexión al host indicado en el campo de texto."""
        target = self.target_input.text().strip()
        if not target:
            QMessageBox.warning(self, "Error", tr("err_enter_ip"))
            return

        # Resolver IP desde el alias del host (si aplica)
        if target in self.hosts:
            ip = self.hosts[target]
            host_id = target
        else:
            ip = target
            host_id = ""

        key_for_pwd = host_id if host_id else ip
        password = ""

        # Intentar usar contraseña guardada
        if self.remember_passwords_chk.isChecked():
            password = self.config.get("saved_passwords", {}).get(key_for_pwd, "")

        # Pedir contraseña si no hay guardada
        if not password:
            password, ok = QInputDialog.getText(
                self,
                tr("auth_title"),
                tr("auth_label", target),
                QLineEdit.Password
            )
            if not ok or not password:
                return

        # Guardar estado de la conexión en curso
        self._last_target_label = key_for_pwd
        self._last_target_ip = ip
        self._last_password = password

        # Actualizar UI
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.remote_disconnect_btn.setEnabled(True)
        self.connection_status_lbl.setText(tr("status_connecting"))
        self.remote_screen.set_connection_status("connecting")

        # Conectar en hilo secundario para no bloquear la UI
        threading.Thread(
            target=self.conn_manager.connect_to_host,
            args=(ip, self.config["port"], password, host_id),
            daemon=True
        ).start()

    def _disconnect_from_host(self) -> None:
        """Desconecta del host remoto activo."""
        self.conn_manager.disconnect()

    @pyqtSlot(str)
    def _request_password(self, target_id: str) -> None:
        """
        Recibe señal de autenticación fallida (desde hilo secundario).
        Delega la apertura del diálogo al hilo GUI mediante QueuedConnection.
        """
        QMetaObject.invokeMethod(
            self, "_show_password_dialog",
            Qt.QueuedConnection,
            Q_ARG(str, target_id)
        )

    @pyqtSlot(str)
    def _show_password_dialog(self, target_id: str) -> None:
        """Muestra diálogo para reintentar contraseña tras autenticación fallida."""
        password, ok = QInputDialog.getText(
            self,
            tr("auth_failed_title"),
            tr("auth_failed_label", target_id),
            QLineEdit.Password
        )
        if ok and password:
            ip = self.hosts.get(target_id, target_id)
            self._last_target_label = target_id
            self._last_target_ip = ip
            self._last_password = password
            threading.Thread(
                target=self.conn_manager.connect_to_host,
                args=(ip, self.config["port"], password, target_id),
                daemon=True
            ).start()

    # ─────────────────────────────────────────────────────────────────────────
    # GESTIÓN DE HOSTS CONOCIDOS
    # ─────────────────────────────────────────────────────────────────────────

    def _update_hosts_list(self) -> None:
        """Recarga la lista de hosts conocidos en la UI."""
        self.hosts_list.clear()
        for name, ip in self.hosts.items():
            self.hosts_list.addItem(QListWidgetItem(f"{name} ({ip})"))

    def _on_host_selected(self, item: QListWidgetItem) -> None:
        """Al seleccionar un host de la lista, pone su nombre en el campo de texto."""
        text = item.text()
        name = text.split(" (")[0].strip() if " (" in text else text
        self.target_input.setText(name)

    def _remember_host(self, name: str, ip: str) -> None:
        """Guarda un host en el archivo de hosts conocidos."""
        self.hosts[name] = ip
        save_json(HOSTS_FILE, self.hosts)
        self._update_hosts_list()

    # ─────────────────────────────────────────────────────────────────────────
    # TRANSFERENCIA DE ARCHIVOS
    # ─────────────────────────────────────────────────────────────────────────

    def _choose_and_send_file(self) -> None:
        """Abre diálogo para seleccionar y enviar un archivo al equipo remoto."""
        if not self.conn_manager.is_connected:
            QMessageBox.information(self, "Error", tr("err_no_connection_file"))
            return

        path, _ = QFileDialog.getOpenFileName(self, tr("btn_send_file"))
        if not path:
            return

        # send_file() hace socket.sendall() bloqueante por cada chunk de hasta
        # 256 KiB; llamarlo directo en el hilo de la GUI congelaba la ventana
        # durante toda la transferencia. El progreso y los errores ya llegan
        # de forma thread-safe vía la señal connection_status (ver
        # _setup_connections/_on_connection_status), así que no hace falta
        # esperar el resultado aquí para informar al usuario.
        threading.Thread(
            target=self.conn_manager.send_file,
            args=(path,),
            daemon=True
        ).start()

    def _open_received_folder(self) -> None:
        """Abre la carpeta de archivos recibidos en el explorador del sistema."""
        os.makedirs(RECEIVED_DIR, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(RECEIVED_DIR)
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(RECEIVED_DIR)))
        except Exception:
            QMessageBox.information(
                self, tr("btn_recv_folder"),
                tr("folder_location", os.path.abspath(RECEIVED_DIR))
            )

    # ─────────────────────────────────────────────────────────────────────────
    # PANTALLA COMPLETA
    # ─────────────────────────────────────────────────────────────────────────

    def _enter_remote_fullscreen(self) -> None:
        """Entra en modo pantalla completa para el escritorio remoto."""
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
        """Sale del modo pantalla completa y vuelve a la pestaña de escritorio."""
        self._fs_win = None
        # Sin esto, remote_screen quedaba huérfano dentro de la ventana de
        # fullscreen ya cerrada y la pestaña "Pantalla remota" se veía en
        # blanco permanentemente después del primer uso de fullscreen.
        if widget is not None and getattr(self, "_remote_tab_layout", None) is not None:
            self._remote_tab_layout.addWidget(widget, 1)
        self.tabs.setCurrentIndex(2)

    # ─────────────────────────────────────────────────────────────────────────
    # ENVÍO DE EVENTOS REMOTOS
    # ─────────────────────────────────────────────────────────────────────────

    @pyqtSlot(bytes)
    def _send_mouse_event(self, event_data: bytes) -> None:
        """Envía evento de ratón al equipo remoto."""
        # Capturamos el socket localmente para evitar condición de carrera
        # si se desconecta en otro hilo mientras enviamos.
        sock = self.conn_manager.socket
        if self.conn_manager.is_connected and sock:
            try:
                from ...backend.core.utils import pack_message
                sock.sendall(pack_message(event_data))
            except Exception as e:
                logger.debug(f"Error sending mouse event: {e}")

    @pyqtSlot(bytes)
    def _send_keyboard_event(self, event_data: bytes) -> None:
        """Envía evento de teclado al equipo remoto."""
        sock = self.conn_manager.socket
        if self.conn_manager.is_connected and sock:
            try:
                from ...backend.core.utils import pack_message
                sock.sendall(pack_message(event_data))
            except Exception as e:
                logger.debug(f"Error sending keyboard event: {e}")

    @pyqtSlot(list)
    def _on_screens_received(self, screens: list) -> None:
        """Recibe la lista de pantallas del servidor remoto."""
        logger.debug(f"Screens received: {len(screens)}")

    # ─────────────────────────────────────────────────────────────────────────
    # UTILIDADES DE UI
    # ─────────────────────────────────────────────────────────────────────────

    def _copy_to_clipboard(self, text: str) -> None:
        """Copia texto al portapapeles del sistema."""
        QApplication.clipboard().setText(text)
        self.status_bar.showMessage(tr("msg_copied", text), 3000)

    def _generate_new_password(self) -> None:
        """Genera una nueva contraseña aleatoria y la guarda."""
        self.config["password"] = generate_password()
        self.pwd_label.setText(f"🔐 {tr('label_password')}: {self.config['password']}")
        self.config.save()
        self.status_bar.showMessage(tr("msg_new_password"), 3000)

    def _save_settings(self) -> None:
        """Guarda la configuración de la pestaña de ajustes."""
        try:
            port = int(self.port_input.text())
            if port != self.config["port"]:
                self.config["port"] = port
                self.port_label.setText(f"🚪 {tr('label_port')} {port}")
                self.config.save()
                self.status_bar.showMessage(tr("msg_restart_port"), 5000)
        except ValueError:
            QMessageBox.warning(self, "Error", tr("err_invalid_port"))
            return

        self.config["remember_passwords"] = self.remember_passwords_chk.isChecked()
        self.config["auto_connect"] = self.auto_connect_chk.isChecked()
        self.config.save()
        self._update_network_info()
        self.status_bar.showMessage(tr("msg_settings_saved"), 3000)

    def _on_language_changed(self, index: int) -> None:
        """Cambia el idioma de la aplicación y actualiza todos los textos."""
        lang = self._lang_combo.currentData()
        set_language(lang)
        # Persiste la preferencia de idioma en la config
        self.config["language"] = lang
        self.config.save()
        self._retranslate_ui()

    def _update_network_info(self) -> None:
        """Actualiza la lista de IPs disponibles en la pestaña de red."""
        self.ip_list.clear()
        for ip in get_available_ips():
            self.ip_list.addItem(QListWidgetItem(f"🌐 {ip}"))

    def _update_local_info(self) -> None:
        """Refresca la información del dispositivo local."""
        self._update_network_info()
        self.status_bar.showMessage(tr("msg_network_updated"), 3000)

    def _open_donate_url(self) -> None:
        """Abre la URL de donación en el navegador por defecto."""
        try:
            QDesktopServices.openUrl(QUrl(DONATE_URL))
        except Exception:
            webbrowser.open(DONATE_URL)

    # ─────────────────────────────────────────────────────────────────────────
    # GESTIÓN DEL TUNNEL CLOUDFLARE
    # ─────────────────────────────────────────────────────────────────────────

    def _show_tunnel_install_instructions(self) -> None:
        """Instala cloudflared automáticamente o muestra instrucciones manuales."""
        if self.tunnel_manager.is_cloudflare_installed():
            QMessageBox.information(
                self,
                tr("tunnel_already_installed_title"),
                tr("tunnel_already_installed_msg")
            )
            return

        if sys.platform.startswith("win"):
            reply = QMessageBox.question(
                self,
                tr("tunnel_install_confirm_title"),
                tr("tunnel_install_confirm_msg"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.No:
                # Mostrar instrucciones manuales en el terminal
                instructions = self.tunnel_manager.get_installation_instructions()
                self.tunnel_terminal.clear()
                self.tunnel_terminal.appendPlainText("=" * 60)
                self.tunnel_terminal.appendPlainText(f"  {tr('install_manual_header')}")
                self.tunnel_terminal.appendPlainText("=" * 60)
                self.tunnel_terminal.appendPlainText(instructions)
                self.tunnel_terminal.appendPlainText("\n" + "=" * 60)
                return

        # Limpiar terminal e iniciar instalación
        self.tunnel_terminal.clear()
        self.tunnel_terminal.appendPlainText(tr("install_starting"))
        self.tunnel_terminal.appendPlainText("")

        # Deshabilitar botón durante la instalación
        self.install_tunnel_btn.setEnabled(False)
        self.install_tunnel_btn.setText(tr("tunnel_installing_text"))

        def install_thread():
            """Hilo de instalación para no bloquear la GUI."""
            success = self.tunnel_manager.install_cloudflared()

            # Restaurar botón en el hilo GUI
            QMetaObject.invokeMethod(
                self.install_tunnel_btn, "setEnabled",
                Qt.QueuedConnection, Q_ARG(bool, True)
            )
            QMetaObject.invokeMethod(
                self.install_tunnel_btn, "setText",
                Qt.QueuedConnection, Q_ARG(str, tr("btn_install_tunnel"))
            )

            if success and self.tunnel_manager.is_cloudflare_installed():
                QMetaObject.invokeMethod(
                    self, "_show_install_success",
                    Qt.QueuedConnection
                )

        threading.Thread(target=install_thread, daemon=True).start()

    @pyqtSlot()
    def _show_install_success(self) -> None:
        """Muestra mensaje de instalación exitosa (llamado desde el hilo GUI)."""
        QMessageBox.information(
            self,
            tr("tunnel_install_success_title"),
            tr("tunnel_install_success_msg")
        )

    def _start_tunnel(self) -> None:
        """Inicia el tunnel Cloudflare hacia el puerto local."""
        if not self.tunnel_manager.is_cloudflare_installed():
            QMessageBox.warning(
                self,
                tr("tunnel_not_installed_title"),
                tr("tunnel_not_installed_msg", self.tunnel_manager.get_installation_instructions())
            )
            return

        if self.tunnel_manager.start_tunnel(self.config["port"]):
            self.start_tunnel_btn.setEnabled(False)
            self.stop_tunnel_btn.setEnabled(True)
            self.tunnel_status_lbl.setText(tr("tunnel_active_status"))
        else:
            QMessageBox.critical(self, "Error", tr("tunnel_error"))

    def _stop_tunnel(self) -> None:
        """Detiene el tunnel Cloudflare activo."""
        self.tunnel_manager.stop_tunnel()
        self.start_tunnel_btn.setEnabled(True)
        self.stop_tunnel_btn.setEnabled(False)
        self.tunnel_status_lbl.setText(tr("tunnel_stopped_status"))
        self.tunnel_url_lbl.setText(tr("tunnel_url_stopped"))

    def _on_tunnel_status_change(self, status: str) -> None:
        """
        Callback llamado desde el hilo del tunnel (no-GUI).
        Emite señal interna para que la actualización ocurra en el hilo GUI.
        """
        self._tunnel_status_signal.emit(status)

    @pyqtSlot(str)
    def _update_tunnel_status_ui(self, status: str) -> None:
        """
        Actualiza la UI con el estado del tunnel.
        Siempre se ejecuta en el hilo GUI gracias a la señal.
        """
        self.tunnel_status_lbl.setText(status)
        # Extraer y mostrar la URL si viene incluida en el estado
        if "https://" in status:
            url_part = status.split("URL Tunnel: ")[-1] if "URL Tunnel: " in status else status
            self.tunnel_url_lbl.setText(f"URL: {url_part}")

    def _on_tunnel_output(self, line: str) -> None:
        """
        Recibe línea de salida del proceso cloudflared (hilo secundario).
        Usa invokeMethod para actualizar el terminal en el hilo GUI.
        """
        QMetaObject.invokeMethod(
            self.tunnel_terminal, "appendPlainText",
            Qt.QueuedConnection,
            Q_ARG(str, line)
        )

    def _copy_tunnel_url(self) -> None:
        """Copia la URL del tunnel al portapapeles."""
        url = self.tunnel_manager.get_tunnel_url()
        if url:
            self._copy_to_clipboard(url)
        else:
            QMessageBox.information(self, "Error", tr("err_no_tunnel_url"))

    # ─────────────────────────────────────────────────────────────────────────
    # CICLO DE VIDA
    # ─────────────────────────────────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        """Limpieza de recursos al cerrar la ventana."""
        if self._fs_win:
            try:
                self._fs_win.close()
            except Exception:
                pass

        self.tunnel_manager.stop_tunnel()
        self.conn_manager.stop()
        event.accept()
        logger.info("AlbertDesk window closed")
