"""
Connection management for AlbertDesk.
Handles server and client connections with file transfer support.
"""

import os
import pickle
import socket
import sys
import threading
import time
import uuid
from io import BytesIO
from typing import Dict, Optional, Any

from PIL import Image
import mss
from PyQt5.QtCore import QObject, pyqtSignal

from ..core.logger import get_logger
from ..core.utils import compress_data, decompress_data, pack_message, unpack_message_size
from .input_handler import WinInput

logger = get_logger(__name__)

# Configuration constants
SCREENSHOT_DELAY = 0.05
BUFFER_SIZE = 131072
MAX_CONNECTION_ATTEMPTS = 3
CONNECTION_TIMEOUT = 5
RECEIVED_DIR = "received_files"
FILE_CHUNK_SIZE = 262144  # 256 KiB


class ConnectionManager(QObject):
    """
    Manages network connections for both server and client modes.
    Handles frame capture, input injection, and file transfers.
    """
    
    # Signals
    connection_status = pyqtSignal(str)
    auth_required = pyqtSignal(str)
    connection_established = pyqtSignal(object)
    connection_lost = pyqtSignal()
    frame_received = pyqtSignal(object)
    screens_received = pyqtSignal(list)
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize connection manager.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__()
        self.config = config
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.client_active = False
        self.is_connected = False
        self.current_screen = 0
        self.screens: list = []
        self.injector: Optional[WinInput] = None
        self._receiving_files: Dict[str, Dict[str, Any]] = {}
        
        # Initialize input injector for Windows
        if sys.platform.startswith('win'):
            try:
                self.injector = WinInput()
            except Exception as e:
                logger.error(f"Failed to initialize WinInput: {e}")
                self.injector = None
    
    def start_server(self) -> None:
        """Start server listening for incoming connections."""
        self.running = True
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind(('0.0.0.0', self.config.get("port", 6969)))
                server.listen(1)
                server.settimeout(1)
                self.connection_status.emit("🟢 Servidor esperando conexiones...")
                logger.info(f"Server started on port {self.config.get('port')}")
                
                while self.running:
                    try:
                        conn, addr = server.accept()
                        logger.info(f"Incoming connection from {addr[0]}")
                        self.connection_status.emit(f"📡 Conexión entrante de {addr[0]}")
                        threading.Thread(
                            target=self.handle_incoming_connection,
                            args=(conn,),
                            daemon=True
                        ).start()
                    except socket.timeout:
                        continue
                    except Exception as e:
                        logger.error(f"Server error: {e}")
                        self.connection_status.emit(f"❌ Error en servidor: {str(e)}")
                        break
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            self.connection_status.emit(f"❌ No se pudo iniciar el servidor: {str(e)}")
        finally:
            self.running = False
    
    def handle_incoming_connection(self, conn: socket.socket) -> None:
        """
        Handle incoming client connection with authentication.
        
        Args:
            conn: Client socket connection
        """
        try:
            conn.settimeout(CONNECTION_TIMEOUT)
            
            # Receive and verify password
            header = conn.recv(4)
            if not header:
                conn.close()
                return
            
            auth_size = unpack_message_size(header)
            if not auth_size:
                conn.close()
                return
            
            auth_data = conn.recv(auth_size).decode().strip()
            
            if auth_data != self.config.get("password", ""):
                error_msg = b"auth_failed"
                conn.send(pack_message(error_msg))
                logger.warning(f"Authentication failed for {auth_data}")
                self.connection_status.emit("❌ Autenticación fallida")
                conn.close()
                return
            
            # Send authentication success
            success_msg = b"auth_ok"
            conn.send(pack_message(success_msg))
            logger.info("Client authenticated successfully")
            
            self.is_connected = True
            self.socket = conn
            self.connection_status.emit("🔐 Conexión autenticada")
            self.connection_established.emit(conn)
            
            # Send screen information
            self.update_screens_info()
            screens_data = pickle.dumps({'type': 'screens', 'screens': self.screens})
            conn.sendall(pack_message(screens_data))
            
            # Start event listener thread
            threading.Thread(
                target=self.receive_remote_events_server,
                args=(conn,),
                daemon=True
            ).start()
            
            # Send screenshots
            while self.running and self.is_connected:
                try:
                    screenshot = self.take_screenshot()
                    if screenshot:
                        compressed = compress_data(screenshot)
                        conn.sendall(pack_message(compressed))
                except Exception as e:
                    logger.debug(f"Error sending screenshot: {e}")
                    break
                time.sleep(SCREENSHOT_DELAY)
        
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.connection_status.emit(f"❌ Error en conexión: {str(e)}")
        finally:
            self.is_connected = False
            try:
                conn.close()
            except Exception:
                pass
            self.socket = None
            self.connection_lost.emit()
    
    def receive_remote_events_server(self, conn: socket.socket) -> None:
        """
        Receive and process remote events from client.
        
        Args:
            conn: Client socket connection
        """
        try:
            while self.running and self.is_connected:
                header = conn.recv(4)
                if not header:
                    break
                
                msg_size = unpack_message_size(header)
                if not msg_size:
                    continue
                
                # Receive complete message
                payload = b""
                while len(payload) < msg_size and self.running:
                    chunk = conn.recv(min(BUFFER_SIZE, msg_size - len(payload)))
                    if not chunk:
                        break
                    payload += chunk
                
                if not payload:
                    break
                
                # Process message
                try:
                    msg = pickle.loads(payload)
                    if isinstance(msg, dict):
                        self._process_message(msg)
                except Exception as e:
                    logger.debug(f"Error processing message: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Event receiving error: {e}")
    
    def _process_message(self, msg: Dict[str, Any]) -> None:
        """
        Process incoming message from client.
        
        Args:
            msg: Message dictionary
        """
        msg_type = msg.get("type")
        
        if msg_type == "screen_change":
            idx = int(msg.get("screen", 0))
            if 0 <= idx < max(1, len(self.screens)):
                self.current_screen = idx
        elif msg_type == "mouse":
            self._handle_mouse(msg)
        elif msg_type == "key":
            self._handle_key(msg)
        elif msg_type in ("file_begin", "file_chunk", "file_end"):
            self._handle_file_message(msg)
        elif msg_type == "bye":
            self.is_connected = False
    
    def update_screens_info(self) -> None:
        """Update information about available screens."""
        self.screens = []
        try:
            with mss.mss() as sct:
                for i, monitor in enumerate(sct.monitors[1:], 1):
                    self.screens.append({
                        'id': i,
                        'width': monitor['width'],
                        'height': monitor['height'],
                        'top': monitor['top'],
                        'left': monitor['left']
                    })
            logger.debug(f"Updated screens info: {len(self.screens)} screens")
        except Exception as e:
            logger.error(f"Error updating screens: {e}")
    
    def take_screenshot(self) -> Optional[bytes]:
        """
        Take a screenshot of the current screen.
        
        Returns:
            JPEG screenshot data or None if failed
        """
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
            logger.error(f"Screenshot error: {e}")
            return None
    
    def _handle_mouse(self, msg: Dict[str, Any]) -> None:
        """
        Handle mouse input from remote client.
        
        Args:
            msg: Mouse event message
        """
        try:
            x = int(msg.get('x', 0))
            y = int(msg.get('y', 0))
            
            if self.screens:
                mon = self.screens[min(self.current_screen, len(self.screens)-1)]
                gx = mon['left'] + x
                gy = mon['top'] + y
            else:
                gx, gy = x, y
            
            if self.injector:
                self.injector.move_mouse_px(gx, gy)
                
                event_type = msg.get('event', '')
                if event_type == 'down':
                    self.injector.mouse_button(msg.get('button', 'left'), True)
                elif event_type == 'up':
                    self.injector.mouse_button(msg.get('button', 'left'), False)
                elif event_type == 'wheel':
                    self.injector.mouse_wheel(int(msg.get('delta', 0)))
        except Exception as e:
            logger.error(f"Mouse handling error: {e}")
    
    def _handle_key(self, msg: Dict[str, Any]) -> None:
        """
        Handle keyboard input from remote client.
        
        Args:
            msg: Keyboard event message
        """
        try:
            if not self.injector:
                return
            
            event_type = msg.get('event', '')
            is_down = event_type == 'down'
            
            if 'text' in msg and msg['text']:
                for ch in msg['text']:
                    self.injector.key_unicode(ch, down=is_down)
            else:
                special_vk = {
                    'ENTER': 0x0D, 'ESC': 0x1B, 'BACKSPACE': 0x08, 'TAB': 0x09,
                    'LEFT': 0x25, 'UP': 0x26, 'RIGHT': 0x27, 'DOWN': 0x28,
                    'DELETE': 0x2E, 'HOME': 0x24, 'END': 0x23,
                    'PAGEUP': 0x21, 'PAGEDOWN': 0x22
                }
                vk = special_vk.get(msg.get('special', ''), None)
                if vk is not None:
                    self.injector.key_vk(vk, down=is_down)
        except Exception as e:
            logger.error(f"Keyboard handling error: {e}")
    
    def connect_to_host(self, ip: str, port: int, password: str, target_id: str = "") -> None:
        """
        Connect to remote host as a client.
        
        Args:
            ip: Remote host IP address
            port: Remote host port
            password: Authentication password
            target_id: Optional target ID for identification
        """
        self.client_active = True
        attempts = 0
        
        while attempts < MAX_CONNECTION_ATTEMPTS and self.client_active:
            attempts += 1
            try:
                self.connection_status.emit(f"🔗 Intentando conexión a {ip} (Intento {attempts})...")
                logger.info(f"Attempting connection to {ip}:{port}")
                
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(CONNECTION_TIMEOUT)
                    s.connect((ip, port))
                    
                    # Send password
                    password_data = password.encode()
                    s.sendall(pack_message(password_data))
                    
                    # Receive authentication response
                    header = s.recv(4)
                    if not header:
                        self.connection_status.emit("❌ Sin respuesta de autenticación")
                        break
                    
                    resp_size = unpack_message_size(header)
                    if not resp_size:
                        break
                    
                    response = s.recv(resp_size)
                    
                    if response != b"auth_ok":
                        logger.warning(f"Authentication failed: {response}")
                        self.connection_status.emit(f"❌ Autenticación fallida")
                        self.auth_required.emit(target_id if target_id else ip)
                        time.sleep(1)
                        continue
                    
                    logger.info("Authentication successful")
                    self.connection_status.emit("🔐 Autenticación exitosa")
                    self.is_connected = True
                    self.socket = s
                    self.connection_established.emit(s)
                    
                    # Receive frames from server
                    while self.client_active and self.is_connected:
                        try:
                            header = s.recv(4)
                            if not header:
                                break
                            
                            size = unpack_message_size(header)
                            if not size:
                                continue
                            
                            # Receive complete frame
                            data = b""
                            while len(data) < size and self.client_active:
                                packet = s.recv(min(BUFFER_SIZE, size - len(data)))
                                if not packet:
                                    break
                                data += packet
                            
                            if not data:
                                break
                            
                            # Try to decompress as frame first
                            frame_data = decompress_data(data)
                            if frame_data:
                                self.frame_received.emit(frame_data)
                                continue
                            
                            # Otherwise try as pickle message
                            try:
                                decoded = pickle.loads(data)
                                if isinstance(decoded, dict):
                                    msg_type = decoded.get('type')
                                    if msg_type == 'screens':
                                        self.screens_received.emit(decoded.get('screens', []))
                                    elif msg_type in ('file_begin', 'file_chunk', 'file_end'):
                                        self._handle_file_message(decoded)
                            except Exception:
                                pass
                        
                        except socket.timeout:
                            continue
                        except Exception as e:
                            logger.error(f"Error receiving data: {e}")
                            break
            
            except Exception as e:
                logger.error(f"Connection error: {e}")
                self.connection_status.emit(f"❌ Error de conexión: {str(e)}")
                if attempts < MAX_CONNECTION_ATTEMPTS:
                    time.sleep(1)
        
        if not self.is_connected:
            logger.warning("Failed to establish connection")
            self.connection_status.emit("🔴 No se pudo establecer conexión")
            self.connection_lost.emit()
    
    def disconnect(self) -> None:
        """Disconnect from remote host."""
        self.client_active = False
        self.is_connected = False
        if self.socket:
            try:
                bye = pickle.dumps({'type': 'bye'})
                try:
                    self.socket.sendall(pack_message(bye))
                except Exception:
                    pass
                self.socket.close()
            except Exception as e:
                logger.debug(f"Error during disconnect: {e}")
        self.socket = None
        self.connection_status.emit("🔴 Desconectado del host remoto")
        self.connection_lost.emit()
        logger.info("Disconnected from host")
    
    def stop(self) -> None:
        """Stop server and disconnect."""
        self.client_active = False
        self.is_connected = False
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        logger.info("Connection manager stopped")
    
    def send_file(self, filepath: str) -> bool:
        """
        Send file to remote host.
        
        Args:
            filepath: Path to file to send
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected or not self.socket:
            self.connection_status.emit("❌ No hay conexión para enviar archivos")
            return False
        
        try:
            fname = os.path.basename(filepath)
            fsize = os.path.getsize(filepath)
            file_id = f"{uuid.uuid4().hex}"
            
            logger.info(f"Sending file: {filepath}")
            
            # Send file begin notification
            begin = {'type': 'file_begin', 'file_id': file_id, 'name': fname, 'size': fsize}
            data = pickle.dumps(begin)
            self.socket.sendall(pack_message(data))
            
            # Send file chunks
            sent = 0
            with open(filepath, 'rb') as fp:
                while True:
                    chunk = fp.read(FILE_CHUNK_SIZE)
                    if not chunk:
                        break
                    msg = {'type': 'file_chunk', 'file_id': file_id, 'data': chunk}
                    blob = pickle.dumps(msg)
                    self.socket.sendall(pack_message(blob))
                    sent += len(chunk)
                    pct = (sent / fsize) * 100 if fsize else 100
                    self.connection_status.emit(f"⬆️ Enviando {fname}: {pct:.1f}%")
            
            # Send file end notification
            end = {'type': 'file_end', 'file_id': file_id}
            data = pickle.dumps(end)
            self.socket.sendall(pack_message(data))
            
            logger.info(f"File sent successfully: {fname}")
            self.connection_status.emit(f"✅ Envío completado: {fname}")
            return True
        
        except Exception as e:
            logger.error(f"File send error: {e}")
            self.connection_status.emit(f"❌ Error enviando archivo: {e}")
            return False
    
    def _handle_file_message(self, msg: Dict[str, Any]) -> None:
        """
        Handle file transfer message.
        
        Args:
            msg: File message dictionary
        """
        os.makedirs(RECEIVED_DIR, exist_ok=True)
        msg_type = msg.get('type')
        
        try:
            if msg_type == 'file_begin':
                file_id = msg.get('file_id', '')
                name = msg.get('name', f"file_{file_id}")
                size = int(msg.get('size', 0))
                path = os.path.join(RECEIVED_DIR, name)
                
                try:
                    fp = open(path, 'wb')
                    self._receiving_files[file_id] = {
                        'fp': fp, 'name': name, 'size': size, 'received': 0, 'path': path
                    }
                    logger.info(f"Receiving file: {name} ({size} bytes)")
                    self.connection_status.emit(f"⬇️ Recibiendo {name} ({size} bytes)")
                except Exception as e:
                    logger.error(f"Cannot create file {name}: {e}")
                    self.connection_status.emit(f"❌ No se pudo crear archivo {name}: {e}")
            
            elif msg_type == 'file_chunk':
                file_id = msg.get('file_id', '')
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
                        logger.error(f"Error writing to file: {e}")
                        self.connection_status.emit(f"❌ Error escribiendo {st['name']}: {e}")
            
            elif msg_type == 'file_end':
                file_id = msg.get('file_id', '')
                st = self._receiving_files.pop(file_id, None)
                
                if st:
                    try:
                        st['fp'].close()
                        logger.info(f"File received: {st['path']}")
                        self.connection_status.emit(f"✅ Archivo recibido: {st['path']}")
                    except Exception as e:
                        logger.error(f"Error closing file: {e}")
        
        except Exception as e:
            logger.error(f"File message handling error: {e}")
