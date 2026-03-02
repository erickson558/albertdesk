#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import zlib
import socket
import random
import string
import struct
import threading
import time
import pickle
import uuid
import platform
import ctypes
import signal
from io import BytesIO

from PIL import Image
import mss

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QTabWidget,
    QPushButton, QLineEdit, QStatusBar, QGroupBox, QGridLayout,
    QMessageBox, QInputDialog, QHBoxLayout, QCheckBox, QListWidget,
    QSizePolicy, QFileDialog, QScrollArea
)
from PyQt5.QtGui import QImage, QPixmap, QFont, QDesktopServices
from PyQt5.QtCore import (
    Qt, QMetaObject, Q_ARG, pyqtSlot, pyqtSignal, QObject, QPoint,
    QTimer, QUrl, QEvent, QSize
)

# ─── Configuración ──────────────────────────────────────────────────────────────
CONFIG_FILE = "rustdesk_config.json"
HOSTS_FILE = "hosts.json"
LOCAL_PORT = 6969
SCREENSHOT_DELAY = 0.05
BUFFER_SIZE = 131072
MAX_CONNECTION_ATTEMPTS = 3
CONNECTION_TIMEOUT = 5

RECEIVED_DIR = "received_files"
FILE_CHUNK_SIZE = 262144  # 256 KiB

# ─── Utilidades JSON ───────────────────────────────────────────────────────────
def load_json(file, default):
    try:
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error cargando {file}: {e}")
    return default

def save_json(file, data):
    try:
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error guardando {file}: {e}")

# ─── Utilidades varias ─────────────────────────────────────────────────────────
def generate_id():
    try:
        node = platform.node()
        mac = uuid.getnode()
        unique_str = f"{node}-{mac}"
        return str(abs(hash(unique_str)))[:9]
    except Exception:
        return ''.join(random.choices(string.digits, k=9))

def generate_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(chars, k=length))

def get_available_ips():
    ips = set()
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None):
            family, _, _, _, sockaddr = info
            if family == socket.AF_INET:
                ip = sockaddr[0]
                if ip != "127.0.0.1":
                    ips.add(ip)
    except Exception:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    return sorted(ips) or ["127.0.0.1"]

def compress_data(data, level=6):
    try:
        return zlib.compress(data, level)
    except Exception:
        return data

def decompress_data(data):
    try:
        return zlib.decompress(data)
    except Exception:
        return None

# ───────────────────────────────────────────────────────────────────────────────
# Inyección de entrada (Windows)
# ───────────────────────────────────────────────────────────────────────────────
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_short)]

class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT),
                ("ki", KEYBDINPUT),
                ("hi", HARDWAREINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("union", INPUT_UNION)]

class WinInput:
    INPUT_MOUSE = 0
    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_UNICODE = 0x0004
    KEYEVENTF_SCANCODE = 0x0008
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010
    MOUSEEVENTF_MIDDLEDOWN = 0x0020
    MOUSEEVENTF_MIDDLEUP = 0x0040
    MOUSEEVENTF_WHEEL = 0x0800
    MOUSEEVENTF_ABSOLUTE = 0x8000
    MOUSEEVENTF_VIRTUALDESK = 0x4000

    def __init__(self):
        self.user32 = ctypes.windll.user32
        try:
            self.user32.SetProcessDPIAware()
        except Exception:
            pass

    def _send(self, inputs):
        n = len(inputs)
        arr = (INPUT * n)(*inputs)
        self.user32.SendInput(n, ctypes.byref(arr), ctypes.sizeof(INPUT))

    def move_mouse_px(self, x, y):
        self.user32.SetCursorPos(int(x), int(y))

    def mouse_button(self, button, down=True):
        flags = {
            "left": (self.MOUSEEVENTF_LEFTDOWN if down else self.MOUSEEVENTF_LEFTUP),
            "right": (self.MOUSEEVENTF_RIGHTDOWN if down else self.MOUSEEVENTF_RIGHTUP),
            "middle": (self.MOUSEEVENTF_MIDDLEDOWN if down else self.MOUSEEVENTF_MIDDLEUP),
        }[button]
        mi = MOUSEINPUT(0, 0, 0, flags, 0, None)
        self._send([INPUT(self.INPUT_MOUSE, INPUT_UNION(mi=mi))])

    def mouse_wheel(self, delta):
        mi = MOUSEINPUT(0, 0, ctypes.c_ulong(int(delta)), self.MOUSEEVENTF_WHEEL, 0, None)
        self._send([INPUT(self.INPUT_MOUSE, INPUT_UNION(mi=mi))])

    def key_vk(self, vk, down=True):
        ki = KEYBDINPUT(vk, 0, 0 if down else self.KEYEVENTF_KEYUP, 0, None)
        self._send([INPUT(self.INPUT_KEYBOARD, INPUT_UNION(ki=ki))])

    def key_unicode(self, char, down=True):
        ki = KEYBDINPUT(0, ord(char), self.KEYEVENTF_UNICODE | (0 if down else self.KEYEVENTF_KEYUP), 0, None)
        self._send([INPUT(self.INPUT_KEYBOARD, INPUT_UNION(ki=ki))])

# ─── Ventana de Fullscreen con controles flotantes ────────────────────────────
class RemoteFullscreenWindow(QWidget):
    """Ventana de pantalla completa con overlay de controles:
       - 📌 Pin (fijar/ocultar auto)
       - ⤢ Salir FS
       Overlay aparece al llevar el mouse al borde superior si no está fijado.
    """
    def __init__(self, remote_widget, on_exit):
        super().__init__()
        self.setWindowTitle("Pantalla remota")
        self.setWindowFlags(Qt.Window)
        self.setStyleSheet("background-color: black;")
        self.remote_widget = remote_widget
        self.on_exit = on_exit

        self._pinned = True
        self._overlay = None
        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setInterval(1600)
        self._auto_hide_timer.timeout.connect(self._maybe_auto_hide)

        # Layout principal (el visor ocupa todo)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.remote_widget)
        self.remote_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Capturar teclas (Esc/F11) y eventos del hijo
        self.installEventFilter(self)
        self.remote_widget.installEventFilter(self)

        # Construir overlay
        self._build_overlay()
        self._position_overlay()
        self._show_overlay()

    # ── Overlay ────────────────────────────────────────────────────────────────
    def _build_overlay(self):
        self._overlay = QWidget(self)
        self._overlay.setAttribute(Qt.WA_StyledBackground, True)
        self._overlay.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 180);
                border: 1px solid rgba(255,255,255,60);
                border-radius: 10px;
            }
            QPushButton {
                color: white;
                background: transparent;
                border: none;
                padding: 6px 12px;
                font-size: 14px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.08); border-radius: 8px; }
            QPushButton:checked { background: rgba(76,139,245,0.3); }
            QLabel { color: #eee; }
        """)
        lay = QHBoxLayout(self._overlay)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(6)

        self.pin_btn = QPushButton("📌")
        self.pin_btn.setCheckable(True)
        self.pin_btn.setChecked(True)  # fijado por defecto
        self.pin_btn.setToolTip("Fijar/ocultar controles")
        self.pin_btn.toggled.connect(self._on_pin_toggled)

        self.exit_btn = QPushButton("⤢ Salir")
        self.exit_btn.setToolTip("Salir de pantalla completa (Esc/F11)")
        self.exit_btn.clicked.connect(self.close)

        # Puedes agregar más controles si quieres (ej. selector rápido de pantallas)

        lay.addWidget(self.pin_btn)
        lay.addWidget(self.exit_btn)

        # También capturar teclas en overlay
        self._overlay.installEventFilter(self)
        self._overlay.show()

    def _position_overlay(self):
        if not self._overlay:
            return
        margin = 14
        self._overlay.adjustSize()
        size = self._overlay.sizeHint()
        w = size.width()
        h = size.height()
        self._overlay.setGeometry(self.width() - w - margin, margin, w, h)
        self._overlay.raise_()

    def _show_overlay(self):
        if self._overlay and not self._overlay.isVisible():
            self._overlay.show()
        self._overlay.raise_()
        if not self._pinned:
            self._auto_hide_timer.start()

    def _hide_overlay(self):
        if self._overlay and self._overlay.isVisible():
            self._overlay.hide()
        self._auto_hide_timer.stop()

    def _on_pin_toggled(self, checked):
        self._pinned = checked
        if self._pinned:
            self._show_overlay()
        else:
            # iniciar contador para ocultar
            self._auto_hide_timer.start()

    def _maybe_auto_hide(self):
        if not self._pinned:
            # oculta si el mouse no está en zona superior
            pos = self.mapFromGlobal(QCursor.pos())
            if pos.y() > 60:  # lejos del borde superior
                self._hide_overlay()

    # ── Eventos de ventana FS ──────────────────────────────────────────────────
    def mouseMoveEvent(self, e):
        # Si acercas el mouse al borde superior, mostrar overlay si no está fijado
        if not self._pinned and (e.pos().y() <= 30):
            self._show_overlay()
        super().mouseMoveEvent(e)

    def resizeEvent(self, e):
        self._position_overlay()
        super().resizeEvent(e)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Escape, Qt.Key_F11):
                self.close()
                return True
        elif event.type() == QEvent.MouseButtonDblClick and obj is self.remote_widget:
            # doble clic también alterna (cerrar)
            self.close()
            return True
        elif event.type() == QEvent.Enter or event.type() == QEvent.HoverEnter:
            if not self._pinned:
                self._show_overlay()
        return QWidget.eventFilter(self, obj, event)

    def closeEvent(self, event):
        try:
            if callable(self.on_exit):
                self.on_exit(self.remote_widget)
        except Exception:
            pass
        event.accept()

# ─── Visor de pantalla remota (widget) ────────────────────────────────────────
class RemoteDesktopWidget(QLabel):
    mouse_event = pyqtSignal(bytes)
    keyboard_event = pyqtSignal(bytes)
    request_fullscreen = pyqtSignal()  # doble clic

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.set_connection_status("waiting")
        self.last_frame_time = 0
        self.frame_count = 0
        self.fps = 0
        self.remote_size = QPoint(1, 1)
        self._last_move_emit = 0.0
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_connection_status(self, status):
        if status == "waiting":
            self.setText("🔲 Esperando conexión...")
            self.setStyleSheet("background-color: black; color: white;")
        elif status == "connecting":
            self.setText("🔄 Conectando...")
            self.setStyleSheet("background-color: #333; color: white;")
        elif status == "changing":
            self.setText("🔁 Cambiando de pantalla…")
            self.setStyleSheet("background-color: #222; color: white;")
        elif status == "failed":
            self.setText("❌ Conexión fallida")
            self.setStyleSheet("background-color: #330000; color: white;")
        elif status == "connected":
            self.setStyleSheet("background-color: black;")

    @pyqtSlot(object)
    def display_frame(self, frame_data):
        current_time = time.time()
        if self.last_frame_time > 0:
            self.frame_count += 1
            if current_time - self.last_frame_time >= 1.0:
                self.fps = self.frame_count
                self.frame_count = 0
                self.last_frame_time = current_time
        else:
            self.last_frame_time = current_time

        image = QImage.fromData(frame_data, "JPEG")
        if not image.isNull():
            self.set_connection_status("connected")
            self.remote_size = QPoint(image.width(), image.height())
            pixmap = QPixmap.fromImage(image)
            self.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.setToolTip(f"FPS: {self.fps}")

    def resizeEvent(self, event):
        if self.pixmap():
            self.setPixmap(self.pixmap().scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        super().resizeEvent(event)

    def mouseDoubleClickEvent(self, e):
        self.request_fullscreen.emit()

    def calculate_remote_position(self, local_pos):
        if not self.pixmap():
            return QPoint(0, 0)
        pixmap_size = self.pixmap().size()
        margin_x = (self.width() - pixmap_size.width()) / 2
        margin_y = (self.height() - pixmap_size.height()) / 2
        rel_x = local_pos.x() - margin_x
        rel_y = local_pos.y() - margin_y
        if rel_x < 0 or rel_y < 0 or rel_x > pixmap_size.width() or rel_y > pixmap_size.height():
            return QPoint(-1, -1)
        rx = int(rel_x * self.remote_size.x() / max(1, pixmap_size.width()))
        ry = int(rel_y * self.remote_size.y() / max(1, pixmap_size.height()))
        rx = max(0, min(rx, self.remote_size.x()))
        ry = max(0, min(ry, self.remote_size.y()))
        return QPoint(rx, ry)

    # Mouse
    def mouseMoveEvent(self, e):
        pos = self.calculate_remote_position(e.pos())
        if pos.x() < 0:
            return
        now = time.time()
        if now - self._last_move_emit >= 0.01:
            msg = {'type': 'mouse', 'event': 'move', 'x': pos.x(), 'y': pos.y()}
            self.mouse_event.emit(pickle.dumps(msg))
            self._last_move_emit = now

    def mousePressEvent(self, e):
        btn = 'left' if e.button() == Qt.LeftButton else 'right' if e.button() == Qt.RightButton else 'middle'
        pos = self.calculate_remote_position(e.pos())
        if pos.x() < 0:
            return
        msg = {'type': 'mouse', 'event': 'down', 'button': btn, 'x': pos.x(), 'y': pos.y()}
        self.mouse_event.emit(pickle.dumps(msg))

    def mouseReleaseEvent(self, e):
        btn = 'left' if e.button() == Qt.LeftButton else 'right' if e.button() == Qt.RightButton else 'middle'
        pos = self.calculate_remote_position(e.pos())
        if pos.x() < 0:
            return
        msg = {'type': 'mouse', 'event': 'up', 'button': btn, 'x': pos.x(), 'y': pos.y()}
        self.mouse_event.emit(pickle.dumps(msg))

    def wheelEvent(self, e):
        delta = e.angleDelta().y()
        msg = {'type': 'mouse', 'event': 'wheel', 'delta': int(delta)}
        self.mouse_event.emit(pickle.dumps(msg))

    # Teclado
    def keyPressEvent(self, e):
        txt = e.text()
        if txt:
            msg = {'type': 'key', 'event': 'down', 'text': txt}
            self.keyboard_event.emit(pickle.dumps(msg))
        else:
            special = self._special_from_qt(e.key())
            if special:
                msg = {'type': 'key', 'event': 'down', 'special': special}
                self.keyboard_event.emit(pickle.dumps(msg))

    def keyReleaseEvent(self, e):
        txt = e.text()
        if txt:
            msg = {'type': 'key', 'event': 'up', 'text': txt}
            self.keyboard_event.emit(pickle.dumps(msg))
        else:
            special = self._special_from_qt(e.key())
            if special:
                msg = {'type': 'key', 'event': 'up', 'special': special}
                self.keyboard_event.emit(pickle.dumps(msg))

    @staticmethod
    def _special_from_qt(qkey):
        mapping = {
            Qt.Key_Return: 'ENTER', Qt.Key_Enter: 'ENTER',
            Qt.Key_Escape: 'ESC', Qt.Key_Backspace: 'BACKSPACE',
            Qt.Key_Tab: 'TAB', Qt.Key_Left: 'LEFT', Qt.Key_Right: 'RIGHT',
            Qt.Key_Up: 'UP', Qt.Key_Down: 'DOWN', Qt.Key_Delete: 'DELETE',
            Qt.Key_Home: 'HOME', Qt.Key_End: 'END',
            Qt.Key_PageUp: 'PAGEUP', Qt.Key_PageDown: 'PAGEDOWN',
        }
        return mapping.get(qkey, None)

# ─── Manejador de conexiones con transferencia de archivos ─────────────────────
class ConnectionManager(QObject):
    connection_status = pyqtSignal(str)
    auth_required = pyqtSignal(str)
    connection_established = pyqtSignal(object)
    connection_lost = pyqtSignal()
    frame_received = pyqtSignal(object)
    screens_received = pyqtSignal(list)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.socket = None
        self.running = False
        self.client_active = False
        self.is_connected = False
        self.current_screen = 0
        self.screens = []
        self.injector = None
        self._receiving_files = {}  # file_id -> {fp, name, size, received}

        if sys.platform.startswith('win'):
            self.injector = WinInput()
        else:
            try:
                import pyautogui  # noqa
                self.injector = 'pyautogui'
            except Exception:
                self.injector = None

    # ── Servidor ───────────────────────────────────────────────────────────────
    def start_server(self):
        self.running = True
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind(('0.0.0.0', self.config["port"]))
                server.listen(1)
                server.settimeout(1)
                self.connection_status.emit("🟢 Servidor esperando conexiones...")

                while self.running:
                    try:
                        conn, addr = server.accept()
                        self.connection_status.emit(f"📡 Conexión entrante de {addr[0]}")
                        threading.Thread(
                            target=self.handle_incoming_connection,
                            args=(conn,),
                            daemon=True
                        ).start()
                    except socket.timeout:
                        continue
                    except Exception as e:
                        self.connection_status.emit(f"❌ Error en servidor: {str(e)}")
                        break
        except Exception as e:
            self.connection_status.emit(f"❌ No se pudo iniciar el servidor: {str(e)}")
        finally:
            self.running = False

    def handle_incoming_connection(self, conn):
        try:
            conn.settimeout(CONNECTION_TIMEOUT)

            header = conn.recv(4)
            if not header:
                conn.close()
                return
            auth_size = struct.unpack("!I", header)[0]
            auth_data = conn.recv(auth_size).decode().strip()

            if auth_data != self.config["password"]:
                conn.send(struct.pack("!I", len(b"auth_failed")) + b"auth_failed")
                self.connection_status.emit("❌ Autenticación fallida")
                conn.close()
                return

            conn.send(struct.pack("!I", len(b"auth_ok")) + b"auth_ok")
            self.is_connected = True
            self.socket = conn
            self.connection_status.emit("🔐 Conexión autenticada")
            self.connection_established.emit(conn)

            self.update_screens_info()
            screens_data = pickle.dumps({'type': 'screens', 'screens': self.screens})
            conn.sendall(struct.pack("!I", len(screens_data)) + screens_data)

            threading.Thread(
                target=self.receive_remote_events_server,
                args=(conn,),
                daemon=True
            ).start()

            while self.running and self.is_connected:
                screenshot = self.take_screenshot()
                if screenshot:
                    compressed = compress_data(screenshot)
                    try:
                        conn.sendall(struct.pack("!I", len(compressed)) + compressed)
                    except Exception:
                        break
                time.sleep(SCREENSHOT_DELAY)

        except Exception as e:
            self.connection_status.emit(f"❌ Error en conexión: {str(e)}")
        finally:
            self.is_connected = False
            try:
                conn.close()
            except Exception:
                pass
            self.socket = None
            self.connection_lost.emit()

    def receive_remote_events_server(self, conn):
        try:
            while self.running and self.is_connected:
                header = conn.recv(4)
                if not header:
                    break
                size = struct.unpack("!I", header)[0]
                payload = b""
                while len(payload) < size and self.running:
                    chunk = conn.recv(min(BUFFER_SIZE, size - len(payload)))
                    if not chunk:
                        break
                    payload += chunk

                # ¿Control o frame?
                try:
                    msg = pickle.loads(payload)
                except Exception:
                    continue

                if isinstance(msg, dict):
                    t = msg.get("type")
                    if t == "screen_change":
                        idx = int(msg.get("screen", 0))
                        if 0 <= idx < max(1, len(self.screens)):
                            self.current_screen = idx
                    elif t == "mouse":
                        self._handle_mouse(msg)
                    elif t == "key":
                        self._handle_key(msg)
                    elif t in ("file_begin", "file_chunk", "file_end"):
                        self._handle_file_message(msg)
                    elif t == "bye":
                        break
        except Exception:
            pass

    # ── Captura y control ──────────────────────────────────────────────────────
    def update_screens_info(self):
        self.screens = []
        with mss.mss() as sct:
            for i, monitor in enumerate(sct.monitors[1:], 1):
                self.screens.append({
                    'id': i,
                    'width': monitor['width'],
                    'height': monitor['height'],
                    'top': monitor['top'],
                    'left': monitor['left']
                })

    def take_screenshot(self):
        try:
            with mss.mss() as sct:
                monitors = sct.monitors
                n = len(monitors) - 1
                if n <= 0:
                    monitor = monitors[0]
                else:
                    index = 1 + (self.current_screen % n)
                    monitor = monitors[index]
                img = sct.grab(monitor)
                im = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
                buf = BytesIO()
                im.save(buf, format="JPEG", quality=80, optimize=True)
                return buf.getvalue()
        except Exception as e:
            print(f"Error capturando pantalla: {e}")
            return None

    def _handle_mouse(self, msg):
        x = int(msg.get('x', 0))
        y = int(msg.get('y', 0))
        if self.screens:
            mon = self.screens[min(self.current_screen, len(self.screens)-1)]
            gx = mon['left'] + x
            gy = mon['top'] + y
        else:
            gx, gy = x, y

        if sys.platform.startswith('win') and isinstance(self.injector, WinInput):
            self.injector.move_mouse_px(gx, gy)
            if msg['event'] == 'move':
                return
            if msg['event'] == 'down':
                self.injector.mouse_button(msg.get('button', 'left'), True)
            elif msg['event'] == 'up':
                self.injector.mouse_button(msg.get('button', 'left'), False)
            elif msg['event'] == 'wheel':
                self.injector.mouse_wheel(int(msg.get('delta', 0)))
        else:
            try:
                import pyautogui
                pyautogui.moveTo(gx, gy)
                if msg['event'] == 'down':
                    pyautogui.mouseDown(button=msg.get('button', 'left'))
                elif msg['event'] == 'up':
                    pyautogui.mouseUp(button=msg.get('button', 'left'))
                elif msg['event'] == 'wheel':
                    pyautogui.scroll(int(msg.get('delta', 0)) // 120)
            except Exception:
                pass

    def _handle_key(self, msg):
        if sys.platform.startswith('win') and isinstance(self.injector, WinInput):
            if 'text' in msg and msg['text']:
                for ch in msg['text']:
                    self.injector.key_unicode(ch, down=(msg['event'] == 'down'))
            else:
                special_vk = {
                    'ENTER': 0x0D, 'ESC': 0x1B, 'BACKSPACE': 0x08, 'TAB': 0x09,
                    'LEFT': 0x25, 'UP': 0x26, 'RIGHT': 0x27, 'DOWN': 0x28,
                    'DELETE': 0x2E, 'HOME': 0x24, 'END': 0x23,
                    'PAGEUP': 0x21, 'PAGEDOWN': 0x22
                }
                vk = special_vk.get(msg.get('special', ''), None)
                if vk is not None:
                    self.injector.key_vk(vk, down=(msg['event'] == 'down'))
        else:
            try:
                import pyautogui
                if 'text' in msg and msg['text']:
                    if msg['event'] == 'down':
                        pyautogui.typewrite(msg['text'])
            except Exception:
                pass

    # ── Cliente (conexión saliente) ────────────────────────────────────────────
    def connect_to_host(self, ip, port, password, target_id=""):
        self.client_active = True
        attempts = 0

        while attempts < MAX_CONNECTION_ATTEMPTS and self.client_active:
            attempts += 1
            try:
                self.connection_status.emit(f"🔗 Intentando conexión a {ip} (Intento {attempts})...")
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(CONNECTION_TIMEOUT)
                    s.connect((ip, port))

                    password_data = password.encode()
                    s.sendall(struct.pack("!I", len(password_data)) + password_data)

                    header = s.recv(4)
                    if not header:
                        self.connection_status.emit("❌ Sin respuesta de autenticación")
                        break
                    response_size = struct.unpack("!I", header)[0]
                    response = s.recv(response_size)

                    if response != b"auth_ok":
                        self.connection_status.emit(f"❌ Autenticación fallida: {response.decode(errors='ignore')}")
                        self.auth_required.emit(target_id if target_id else ip)
                        time.sleep(1)
                        continue

                    self.connection_status.emit("🔐 Autenticación exitosa")
                    self.is_connected = True
                    self.socket = s
                    self.connection_established.emit(s)

                    while self.client_active and self.is_connected:
                        try:
                            header = s.recv(4)
                            if not header:
                                break
                            size = struct.unpack("!I", header)[0]
                            data = b""
                            while len(data) < size and self.client_active:
                                packet = s.recv(min(BUFFER_SIZE, size - len(data)))
                                if not packet:
                                    break
                                data += packet
                            if not data:
                                break

                            # ¿Control pickled?
                            try:
                                decoded = pickle.loads(data)
                                if isinstance(decoded, dict):
                                    t = decoded.get('type')
                                    if t == 'screens':
                                        self.screens_received.emit(decoded['screens'])
                                        continue
                                    elif t in ('file_begin', 'file_chunk', 'file_end'):
                                        self._handle_file_message(decoded)
                                        continue
                            except Exception:
                                pass

                            # Frame comprimido
                            frame_data = decompress_data(data)
                            if frame_data:
                                self.frame_received.emit(frame_data)

                        except socket.timeout:
                            continue
                        except Exception as e:
                            self.connection_status.emit(f"❌ Error recibiendo datos: {str(e)}")
                            break

            except Exception as e:
                self.connection_status.emit(f"❌ Error de conexión: {str(e)}")
                if attempts < MAX_CONNECTION_ATTEMPTS:
                    time.sleep(1)

        if not self.is_connected:
            self.connection_status.emit("🔴 No se pudo establecer conexión")
            self.connection_lost.emit()

    def disconnect(self):
        self.client_active = False
        self.is_connected = False
        if self.socket:
            try:
                bye = pickle.dumps({'type': 'bye'})
                try:
                    self.socket.sendall(struct.pack("!I", len(bye)) + bye)
                except Exception:
                    pass
                self.socket.close()
            except Exception:
                pass
        self.socket = None
        self.connection_status.emit("🔴 Desconectado del host remoto")
        self.connection_lost.emit()

    def stop(self):
        self.client_active = False
        self.is_connected = False
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass

    # ── Transferencia de archivos ──────────────────────────────────────────────
    def send_file(self, filepath):
        """Envía un archivo al remoto en chunks."""
        if not self.is_connected or not self.socket:
            self.connection_status.emit("❌ No hay conexión para enviar archivos")
            return False
        try:
            fname = os.path.basename(filepath)
            fsize = os.path.getsize(filepath)
            file_id = f"{uuid.uuid4().hex}"

            begin = {'type': 'file_begin', 'file_id': file_id, 'name': fname, 'size': fsize}
            data = pickle.dumps(begin)
            self.socket.sendall(struct.pack("!I", len(data)) + data)

            sent = 0
            with open(filepath, 'rb') as fp:
                while True:
                    chunk = fp.read(FILE_CHUNK_SIZE)
                    if not chunk:
                        break
                    msg = {'type': 'file_chunk', 'file_id': file_id, 'data': chunk}
                    blob = pickle.dumps(msg)
                    self.socket.sendall(struct.pack("!I", len(blob)) + blob)
                    sent += len(chunk)
                    pct = (sent / fsize) * 100 if fsize else 100
                    self.connection_status.emit(f"⬆️ Enviando {fname}: {pct:.1f}%")

            end = {'type': 'file_end', 'file_id': file_id}
            data = pickle.dumps(end)
            self.socket.sendall(struct.pack("!I", len(data)) + data)
            self.connection_status.emit(f"✅ Envío completado: {fname}")
            return True
        except Exception as e:
            self.connection_status.emit(f"❌ Error enviando archivo: {e}")
            return False

    def _handle_file_message(self, msg):
        """Recibe/ensambla archivos en RECEIVED_DIR."""
        os.makedirs(RECEIVED_DIR, exist_ok=True)
        t = msg.get('type')
        if t == 'file_begin':
            file_id = msg['file_id']
            name = msg.get('name', f"file_{file_id}")
            size = int(msg.get('size', 0))
            path = os.path.join(RECEIVED_DIR, name)
            try:
                fp = open(path, 'wb')
                self._receiving_files[file_id] = {'fp': fp, 'name': name, 'size': size, 'received': 0, 'path': path}
                self.connection_status.emit(f"⬇️ Recibiendo {name} ({size} bytes)")
            except Exception as e:
                self.connection_status.emit(f"❌ No se pudo crear archivo {name}: {e}")

        elif t == 'file_chunk':
            file_id = msg['file_id']
            data = msg.get('data', b'')
            st = self._receiving_files.get(file_id)
            if st and 'fp' in st:
                try:
                    st['fp'].write(data)
                    st['received'] += len(data)
                    size = st.get('size', 0)
                    if size:
                        pct = (st['received'] / size) * 100
                        self.connection_status.emit(f"⬇️ Recibiendo {st['name']}: {pct:.1f}%")
                except Exception as e:
                    self.connection_status.emit(f"❌ Error escribiendo {st['name']}: {e}")

        elif t == 'file_end':
            file_id = msg['file_id']
            st = self._receiving_files.pop(file_id, None)
            if st:
                try:
                    st['fp'].close()
                except Exception:
                    pass
                self.connection_status.emit(f"✅ Archivo recibido: {st['path']}")

# ─── Ventana principal ─────────────────────────────────────────────────────────
class RustDeskClone(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RustDesk Clone - LAN Edition")
        self.setGeometry(100, 100, 1280, 820)
        self.setFont(QFont("Segoe UI", 10))

        self.config = {}
        self._last_target_label = None
        self._last_target_ip = None
        self._last_password = None
        self._suppress_input_until = 0.0

        # fullscreen real del visor
        self._fs_win = None
        self._remote_placeholder = QWidget()

        # botones de pantallas
        self.screen_buttons_area = None
        self.screen_buttons_widget = None
        self.screen_buttons_layout = None
        self._active_screen_index = 0

        self.init_config()
        self.hosts = load_json(HOSTS_FILE, {})
        self.init_ui()

        self.conn_manager = ConnectionManager(self.config)
        self.conn_manager_thread = threading.Thread(
            target=self.conn_manager.start_server,
            daemon=True
        )
        self.conn_manager_thread.start()

        self.setup_connections()

    def init_config(self):
        defaults = {
            "id": generate_id(),
            "password": generate_password(),
            "port": LOCAL_PORT,
            "remember_passwords": True,
            "auto_connect": False,
            "saved_passwords": {}
        }
        existing = load_json(CONFIG_FILE, {})
        if isinstance(existing, dict):
            for key in existing:
                if key == 'saved_passwords' and isinstance(existing[key], dict):
                    defaults[key].update(existing[key])
                else:
                    defaults[key] = existing[key]
        self.config = defaults
        save_json(CONFIG_FILE, self.config)

    def init_ui(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tabs.addTab(self.create_my_id_tab(), "Mi ID")
        self.tabs.addTab(self.create_connect_tab(), "Conectar")
        self.tabs.addTab(self.create_remote_screen_tab(), "Pantalla Remota")
        self.tabs.addTab(self.create_settings_tab(), "Configuración")
        self.tabs.addTab(self.create_network_info_tab(), "Red")

    def create_my_id_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        group = QGroupBox("Dispositivo Local")
        grid = QGridLayout()

        id_layout = QHBoxLayout()
        self.id_label = QLabel(f"🆔 ID: {self.config['id']}")
        self.id_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        copy_id = QPushButton("📋")
        copy_id.clicked.connect(lambda: self.copy_to_clipboard(self.config['id']))
        id_layout.addWidget(self.id_label)
        id_layout.addWidget(copy_id)

        pwd_layout = QHBoxLayout()
        self.pwd_label = QLabel(f"🔐 Contraseña: {self.config['password']}")
        self.pwd_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        copy_pwd = QPushButton("📋")
        copy_pwd.clicked.connect(lambda: self.copy_to_clipboard(self.config['password']))
        generate_pwd = QPushButton("🔄")
        generate_pwd.clicked.connect(self.generate_new_password)
        pwd_layout.addWidget(self.pwd_label)
        pwd_layout.addWidget(copy_pwd)
        pwd_layout.addWidget(generate_pwd)

        self.port_label = QLabel(f"🚪 Puerto: {self.config['port']}")
        self.port_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        refresh_btn = QPushButton("Actualizar Información")
        refresh_btn.clicked.connect(self.refresh_local_info)

        grid.addLayout(id_layout, 0, 0)
        grid.addLayout(pwd_layout, 1, 0)
        grid.addWidget(self.port_label, 2, 0)
        grid.addWidget(refresh_btn, 3, 0)
        group.setLayout(grid)

        layout.addWidget(group)
        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def create_connect_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("IP o ID del equipo remoto")

        self.hosts_combo = QListWidget()
        self.update_hosts_combo()
        self.hosts_combo.itemClicked.connect(self._host_item_clicked)

        btns = QHBoxLayout()
        self.connect_btn = QPushButton("🔗 Conectar")
        self.connect_btn.clicked.connect(self.connect_to_target)
        self.disconnect_btn = QPushButton("⛔ Desconectar")
        self.disconnect_btn.clicked.connect(self.disconnect_from_host)
        self.disconnect_btn.setEnabled(False)
        btns.addWidget(self.connect_btn)
        btns.addWidget(self.disconnect_btn)

        self.connection_status_lbl = QLabel("🔴 Desconectado")
        self.connection_status_lbl.setStyleSheet("font-weight: bold;")

        layout.addWidget(QLabel("Destino:"))
        layout.addWidget(self.target_input)
        layout.addWidget(QLabel("Hosts conocidos:"))
        layout.addWidget(self.hosts_combo)
        layout.addLayout(btns)
        layout.addWidget(self.connection_status_lbl)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def _host_item_clicked(self, item):
        label = item.text()
        if "(" in label and label.endswith(")"):
            key = label.split(" (", 1)[0].strip()
        else:
            key = label.strip()
        self.target_input.setText(key)

    def create_remote_screen_tab(self):
        tab = QWidget()
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)

        # barra de controles
        self.ctrl_bar = QWidget()
        ctrl_layout = QHBoxLayout(self.ctrl_bar)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)

        self.hide_controls_chk = QCheckBox("Ocultar controles")
        self.hide_controls_chk.stateChanged.connect(self._toggle_controls_visibility)

        self.send_file_btn = QPushButton("Enviar archivo")
        self.send_file_btn.clicked.connect(self.choose_and_send_file)

        self.open_recv_btn = QPushButton("Carpeta de descargas")
        self.open_recv_btn.clicked.connect(self.open_received_folder)

        self.remote_disconnect_btn = QPushButton("⛔ Desconectar")
        self.remote_disconnect_btn.clicked.connect(self.disconnect_from_host)
        self.remote_disconnect_btn.setEnabled(False)

        self.fullscreen_btn = QPushButton("Pantalla Completa")
        self.fullscreen_btn.clicked.connect(self.enter_remote_fullscreen)

        # selector de pantallas: botones dentro de un scroll
        self.screen_buttons_area = QScrollArea()
        self.screen_buttons_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.screen_buttons_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.screen_buttons_area.setWidgetResizable(True)
        self.screen_buttons_widget = QWidget()
        self.screen_buttons_layout = QHBoxLayout(self.screen_buttons_widget)
        self.screen_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.screen_buttons_layout.setSpacing(8)
        self.screen_buttons_area.setWidget(self.screen_buttons_widget)

        ctrl_layout.addWidget(QLabel("Pantallas:"))
        ctrl_layout.addWidget(self.screen_buttons_area, 1)
        ctrl_layout.addWidget(self.hide_controls_chk)
        ctrl_layout.addWidget(self.send_file_btn)
        ctrl_layout.addWidget(self.open_recv_btn)
        ctrl_layout.addWidget(self.remote_disconnect_btn)
        ctrl_layout.addWidget(self.fullscreen_btn)

        outer.addWidget(self.ctrl_bar)

        # visor remoto ocupa todo
        self.remote_screen = RemoteDesktopWidget()
        self.remote_screen.setStyleSheet("background-color: black;")
        self.remote_screen.request_fullscreen.connect(self.enter_remote_fullscreen)

        viewer_layout = QVBoxLayout()
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.addWidget(self.remote_screen)

        viewer_container = QWidget()
        viewer_container.setLayout(viewer_layout)
        outer.addWidget(viewer_container, 1)  # stretch 1 -> ocupa todo

        # estilo de botones de pantallas
        self.setStyleSheet("""
        QPushButton#scrbtn {
            padding: 8px 14px;
            border: 1px solid #555;
            border-radius: 8px;
            background: #222;
            color: #ddd;
        }
        QPushButton#scrbtn:hover { background: #2c2c2c; }
        QPushButton#scrbtn[active="true"] {
            background: #4c8bf5; color: white; border-color: #4c8bf5;
        }
        """)

        return tab

    def _toggle_controls_visibility(self, state):
        hide = state == Qt.Checked
        self.ctrl_bar.setVisible(not hide)

    def create_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        group = QGroupBox("Configuración de Conexión")
        grid = QGridLayout()

        self.remember_passwords = QCheckBox("Recordar contraseñas")
        self.remember_passwords.setChecked(self.config.get("remember_passwords", True))

        self.auto_connect = QCheckBox("Conectar automáticamente a hosts conocidos")
        self.auto_connect.setChecked(self.config.get("auto_connect", False))

        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Puerto:"))
        self.port_input = QLineEdit(str(self.config.get("port", LOCAL_PORT)))
        port_layout.addWidget(self.port_input)

        save_btn = QPushButton("Guardar Configuración")
        save_btn.clicked.connect(self.save_settings)

        grid.addWidget(self.remember_passwords, 0, 0, 1, 2)
        grid.addWidget(self.auto_connect, 1, 0, 1, 2)
        grid.addLayout(port_layout, 2, 0, 1, 2)
        grid.addWidget(save_btn, 3, 0, 1, 2)
        group.setLayout(grid)

        layout.addWidget(group)
        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def create_network_info_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        group = QGroupBox("Información de Red")
        grid = QGridLayout()

        self.ip_list = QListWidget()
        self.ip_list.setSelectionMode(QListWidget.NoSelection)

        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.update_network_info)

        grid.addWidget(QLabel("Direcciones IP disponibles para conexión:"), 0, 0)
        grid.addWidget(self.ip_list, 1, 0)
        grid.addWidget(refresh_btn, 2, 0)
        group.setLayout(grid)

        layout.addWidget(group)

        conn_group = QGroupBox("Información de Conexión")
        conn_layout = QVBoxLayout()

        self.conn_info = QLabel("Puerto: {}\n".format(self.config.get("port", LOCAL_PORT)))
        self.conn_info.setTextInteractionFlags(Qt.TextSelectableByMouse)

        conn_layout.addWidget(self.conn_info)
        conn_group.setLayout(conn_layout)

        layout.addWidget(conn_group)
        layout.addStretch()

        self.update_network_info()
        tab.setLayout(layout)
        return tab

    # ── Hosts conocidos ────────────────────────────────────────────────────────
    def remember_host(self, key_label: str, ip: str):
        if not key_label:
            key_label = ip
        if not ip:
            return
        self.hosts[key_label] = ip
        save_json(HOSTS_FILE, self.hosts)
        self.update_hosts_combo()

    def update_network_info(self):
        if not hasattr(self, "ip_list") or not hasattr(self, "conn_info"):
            return
        self.ip_list.clear()
        ips = get_available_ips()
        if not ips:
            self.ip_list.addItem("No se pudieron detectar direcciones IP")
        else:
            for ip in ips:
                self.ip_list.addItem(f"{ip}:{self.config.get('port', LOCAL_PORT)}")
        self.conn_info.setText(
            "Puerto: {}\n\nConexiones entrantes permitidas en:\n{}".format(
                self.config.get("port", LOCAL_PORT),
                "\n".join([f"- {ip}:{self.config.get('port', LOCAL_PORT)}" for ip in ips]) if ips else "- (ninguna)"
            )
        )

    def setup_connections(self):
        self.conn_manager.connection_status.connect(self.status_bar.showMessage)
        self.conn_manager.auth_required.connect(self.request_password)
        self.conn_manager.connection_established.connect(self.on_connection_established)
        self.conn_manager.connection_lost.connect(self.on_connection_lost)
        self.conn_manager.frame_received.connect(self.remote_screen.display_frame)
        self.conn_manager.screens_received.connect(self.update_screen_buttons)

        self.remote_screen.mouse_event.connect(self.send_mouse_event)
        self.remote_screen.keyboard_event.connect(self.send_keyboard_event)

    def refresh_local_info(self):
        self.config["id"] = generate_id()
        self.id_label.setText(f"🆔 ID: {self.config['id']}")
        self.update_network_info()
        save_json(CONFIG_FILE, self.config)
        self.status_bar.showMessage("🔄 Información local actualizada", 3000)

    def update_hosts_combo(self):
        self.hosts_combo.clear
        self.hosts_combo.clear()
        for host_id, ip in self.hosts.items():
            self.hosts_combo.addItem(f"{host_id} ({ip})")

    # ── Pantallas con botones ──────────────────────────────────────────────────
    def update_screen_buttons(self, screens):
        # limpiar
        while self.screen_buttons_layout.count():
            w = self.screen_buttons_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        if not screens or len(screens) <= 1:
            return

        if self._active_screen_index >= len(screens):
            self._active_screen_index = 0

        for i, scr in enumerate(screens):
            btn = QPushButton(f"{i+1}  {scr['width']}x{scr['height']}")
            btn.setObjectName("scrbtn")
            btn.setProperty("active", "true" if i == self._active_screen_index else "false")
            btn.setCheckable(True)
            btn.setChecked(i == self._active_screen_index)
            btn.clicked.connect(lambda _, idx=i: self._screen_btn_clicked(idx))
            self.screen_buttons_layout.addWidget(btn)

        self._refresh_screen_btn_styles()

    def _screen_btn_clicked(self, index):
        self._active_screen_index = index
        self._refresh_screen_btn_styles()
        self.change_remote_screen(index)

    def _refresh_screen_btn_styles(self):
        for i in range(self.screen_buttons_layout.count()):
            w = self.screen_buttons_layout.itemAt(i).widget()
            if not w:
                continue
            active = "true" if i == self._active_screen_index else "false"
            w.setProperty("active", active)
            w.setChecked(i == self._active_screen_index)
            w.style().unpolish(w)
            w.style().polish(w)
            w.update()

    # ── Envío/Recepción de eventos ─────────────────────────────────────────────
    def send_mouse_event(self, event_data):
        if time.time() < getattr(self, "_suppress_input_until", 0.0):
            return
        if self.conn_manager.is_connected and self.conn_manager.socket:
            try:
                self.conn_manager.socket.sendall(struct.pack("!I", len(event_data)) + event_data)
            except Exception as e:
                print(f"Error enviando evento mouse: {e}")

    def send_keyboard_event(self, event_data):
        if time.time() < getattr(self, "_suppress_input_until", 0.0):
            return
        if self.conn_manager.is_connected and self.conn_manager.socket:
            try:
                self.conn_manager.socket.sendall(struct.pack("!I", len(event_data)) + event_data)
            except Exception as e:
                print(f"Error enviando evento teclado: {e}")

    # ── Cambio de pantalla ─────────────────────────────────────────────────────
    def change_remote_screen(self, index):
        if index < 0 or not self.conn_manager.is_connected or not self.conn_manager.socket:
            return
        try:
            self._suppress_input_until = time.time() + 0.40
            self.remote_screen.set_connection_status("changing")
            self.remote_screen.clear()
            screen_data = {'type': 'screen_change', 'screen': int(index)}
            payload = pickle.dumps(screen_data)
            self.conn_manager.socket.sendall(struct.pack("!I", len(payload)) + payload)
            self.tabs.setCurrentIndex(2)
            self.remote_screen.setFocus()
        except Exception as e:
            print(f"Error cambiando pantalla: {e}")

    # ── Pantalla completa real (toggle) ─────────────────────────────────────────
    def enter_remote_fullscreen(self):
        # Toggle: si ya está en fullscreen, salimos
        if self._fs_win is not None:
            try:
                self._fs_win.close()
            except Exception:
                self._fs_win = None
            return

        parent_layout = self.remote_screen.parent().layout()
        idx = parent_layout.indexOf(self.remote_screen)
        if idx < 0:
            idx = parent_layout.count() - 1
        parent_layout.insertWidget(idx, self._remote_placeholder)
        parent_layout.removeWidget(self.remote_screen)

        def _restore(remote_widget):
            try:
                parent_layout.insertWidget(idx, remote_widget)
                parent_layout.removeWidget(self._remote_placeholder)
                self._fs_win = None
                self.remote_screen.setFocus()
            except Exception:
                self._fs_win = None

        self._fs_win = RemoteFullscreenWindow(self.remote_screen, _restore)
        self._fs_win.showFullScreen()
        self.remote_screen.setFocus()

    # ── Conectar / Desconectar ─────────────────────────────────────────────────
    def connect_to_target(self):
        target = self.target_input.text().strip()
        if not target:
            QMessageBox.warning(self, "Error", "Debes ingresar una IP o ID válida")
            return

        # Determinar destino
        is_ip = False
        parts = target.split('.')
        if len(parts) == 4:
            try:
                is_ip = all(0 <= int(p) <= 255 for p in parts)
            except Exception:
                is_ip = False

        if is_ip:
            ip = target
            host_id = ""
        else:
            ip = self.hosts.get(target, target)
            host_id = target if target in self.hosts else ""

        # Intentar recuperar contraseña guardada por ID o IP
        key_for_pwd = host_id if host_id else ip
        password = ""
        if self.config.get("remember_passwords", True):
            password = self.config.setdefault("saved_passwords", {}).get(key_for_pwd, "")

        # Si no hay, preguntar
        if not password:
            password, ok = QInputDialog.getText(
                self,
                "Autenticación",
                f"Ingrese la contraseña para {target}:\n(Contraseña actual del destino: {self.config['password'] if not host_id else 'consultar en el destino'})",
                QLineEdit.Password
            )
            if not ok or not password:
                return

        # Guardar contexto para persistir tras éxito
        self._last_target_label = key_for_pwd  # ID o IP
        self._last_target_ip = ip
        self._last_password = password

        # UI y arranque de hilo
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.remote_disconnect_btn.setEnabled(True)
        self.connection_status_lbl.setText("🟡 Conectando...")
        self.remote_screen.set_connection_status("connecting")

        threading.Thread(
            target=self.conn_manager.connect_to_host,
            args=(ip, self.config["port"], password, host_id),
            daemon=True
        ).start()

    def disconnect_from_host(self):
        self.conn_manager.disconnect()

    # ── Reintento de contraseña ────────────────────────────────────────────────
    def request_password(self, target_id: str):
        QMetaObject.invokeMethod(
            self, "_show_password_dialog", Qt.QueuedConnection, Q_ARG(str, target_id)
        )

    @pyqtSlot(str)
    def _show_password_dialog(self, target_id: str):
        password, ok = QInputDialog.getText(
            self, "Autenticación Fallida",
            f"Contraseña incorrecta para {target_id}.\nIngrese la contraseña correcta:",
            QLineEdit.Password
        )
        if ok and password:
            ip = self.hosts.get(target_id, target_id)
            self._last_target_label = target_id if target_id else ip
            self._last_target_ip = ip
            self._last_password = password
            threading.Thread(
                target=self.conn_manager.connect_to_host,
                args=(ip, self.config["port"], password, target_id),
                daemon=True
            ).start()

    # ── Transferencia de archivos (UI) ─────────────────────────────────────────
    def choose_and_send_file(self):
        if not self.conn_manager.is_connected:
            QMessageBox.information(self, "Sin conexión", "Conéctate a un equipo remoto primero.")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Selecciona archivo para enviar")
        if not path:
            return
        ok = self.conn_manager.send_file(path)
        if not ok:
            QMessageBox.warning(self, "Error", "No se pudo enviar el archivo.")

    def open_received_folder(self):
        os.makedirs(RECEIVED_DIR, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(RECEIVED_DIR)  # type: ignore
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(RECEIVED_DIR)))
        except Exception as e:
            QMessageBox.information(self, "Carpeta", f"Carpeta: {os.path.abspath(RECEIVED_DIR)}\n{e}")

    # ── Miscelánea ─────────────────────────────────────────────────────────────
    def copy_to_clipboard(self, text):
        QApplication.clipboard().setText(text)
        self.status_bar.showMessage(f"📋 Copiado: {text}", 3000)

    def generate_new_password(self):
        self.config["password"] = generate_password()
        self.pwd_label.setText(f"🔐 Contraseña: {self.config['password']}")
        save_json(CONFIG_FILE, self.config)
        self.status_bar.showMessage("🔑 Nueva contraseña generada", 3000)

    def save_settings(self):
        try:
            new_port = int(self.port_input.text())
            if new_port != self.config["port"]:
                self.config["port"] = new_port
                self.port_label.setText(f"🚪 Puerto: {self.config['port']}")
                self.status_bar.showMessage("⚙️ Reinicie la aplicación para aplicar el nuevo puerto", 5000)
        except ValueError:
            QMessageBox.warning(self, "Error", "El puerto debe ser un número válido")
            return

        self.config["remember_passwords"] = self.remember_passwords.isChecked()
        self.config["auto_connect"] = self.auto_connect.isChecked()
        save_json(CONFIG_FILE, self.config)
        self.update_network_info()
        self.status_bar.showMessage("⚙️ Configuración guardada", 3000)

    def on_connection_established(self, sock):
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.remote_disconnect_btn.setEnabled(True)
        self.connection_status_lbl.setText("🟢 Conectado")
        self.tabs.setCurrentIndex(2)
        self.remote_screen.setFocus()
        try:
            # Guardar host e incluir contraseña si está habilitado
            if self._last_target_ip:
                self.remember_host(self._last_target_label or self._last_target_ip,
                                   self._last_target_ip)
            if self.config.get("remember_passwords", True) and self._last_password:
                self.config.setdefault("saved_passwords", {})[self._last_target_label] = self._last_password
                save_json(CONFIG_FILE, self.config)
        except Exception:
            pass

    def on_connection_lost(self):
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.remote_disconnect_btn.setEnabled(False)
        self.connection_status_lbl.setText("🔴 Desconectado")
        self.remote_screen.set_connection_status("failed")
        QTimer.singleShot(1200, lambda: self.remote_screen.set_connection_status("waiting"))
        if self._fs_win is not None:
            try:
                self._fs_win.close()
            except Exception:
                self._fs_win = None

    def closeEvent(self, event):
        if self._fs_win is not None:
            try:
                self._fs_win.close()
            except Exception:
                pass
        self.conn_manager.stop()
        event.accept()

# ─── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RustDeskClone()

    def _graceful_shutdown(*_):
        try:
            window.conn_manager.stop()
        except Exception:
            pass
        QTimer.singleShot(0, app.quit)

    signal.signal(signal.SIGINT, _graceful_shutdown)
    if os.name == "nt":
        try:
            signal.signal(signal.SIGBREAK, _graceful_shutdown)
        except Exception:
            pass

    window.show()
    try:
        exit_code = app.exec_()
    except KeyboardInterrupt:
        exit_code = 0
    finally:
        try:
            window.conn_manager.stop()
        except Exception:
            pass
        sys.exit(exit_code)
