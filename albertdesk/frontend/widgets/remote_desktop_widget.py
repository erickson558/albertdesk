"""
Remote desktop display widget for viewing remote screen.
"""

import pickle
import time
from typing import Optional

from PyQt5.QtCore import Qt, QPoint, QSize, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QLabel, QSizePolicy

from ...backend.core.logger import get_logger

logger = get_logger(__name__)


class RemoteDesktopWidget(QLabel):
    """Widget for displaying remote desktop screenshots."""
    
    mouse_event = pyqtSignal(bytes)
    keyboard_event = pyqtSignal(bytes)
    request_fullscreen = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Initialize remote desktop widget.
        
        Args:
            parent: Parent widget
        """
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
    
    def set_connection_status(self, status: str) -> None:
        """
        Update connection status display.
        
        Args:
            status: Status string ('waiting', 'connecting', 'changing', 'failed', 'connected')
        """
        status_messages = {
            "waiting": ("🔲 Esperando conexión...", "background-color: black; color: white;"),
            "connecting": ("🔄 Conectando...", "background-color: #333; color: white;"),
            "changing": ("🔁 Cambiando de pantalla…", "background-color: #222; color: white;"),
            "failed": ("❌ Conexión fallida", "background-color: #330000; color: white;"),
            "connected": ("", "background-color: black;"),
        }
        
        if status in status_messages:
            text, stylesheet = status_messages[status]
            if text:
                self.setText(text)
            self.setStyleSheet(stylesheet)
    
    @pyqtSlot(object)
    def display_frame(self, frame_data: bytes) -> None:
        """
        Display frame received from server.
        
        Args:
            frame_data: JPEG frame data
        """
        current_time = time.time()
        if self.last_frame_time > 0:
            self.frame_count += 1
            if current_time - self.last_frame_time >= 1.0:
                self.fps = self.frame_count
                self.frame_count = 0
                self.last_frame_time = current_time
        else:
            self.last_frame_time = current_time
        
        try:
            image = QImage.fromData(frame_data, "JPEG")
            if not image.isNull():
                self.set_connection_status("connected")
                self.remote_size = QPoint(image.width(), image.height())
                pixmap = QPixmap.fromImage(image)
                self.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.setToolTip(f"FPS: {self.fps}")
        except Exception as e:
            logger.error(f"Error displaying frame: {e}")
    
    def resizeEvent(self, event):
        """Handle resize event."""
        if self.pixmap():
            self.setPixmap(self.pixmap().scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        super().resizeEvent(event)
    
    def mouseDoubleClickEvent(self, e):
        """Handle double-click to enter fullscreen."""
        self.request_fullscreen.emit()
    
    def calculate_remote_position(self, local_pos: QPoint) -> QPoint:
        """
        Convert local widget coordinates to remote display coordinates.
        
        Args:
            local_pos: Position in widget
        
        Returns:
            Position on remote display
        """
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
    
    def mouseMoveEvent(self, e):
        """Handle mouse move event."""
        pos = self.calculate_remote_position(e.pos())
        if pos.x() < 0:
            return
        
        now = time.time()
        if now - self._last_move_emit >= 0.01:
            msg = {'type': 'mouse', 'event': 'move', 'x': pos.x(), 'y': pos.y()}
            self.mouse_event.emit(pickle.dumps(msg))
            self._last_move_emit = now
    
    def mousePressEvent(self, e):
        """Handle mouse press event."""
        btn = {
            1: 'left',
            2: 'right',
            4: 'middle'
        }.get(e.button(), 'left')
        
        pos = self.calculate_remote_position(e.pos())
        if pos.x() < 0:
            return
        
        msg = {'type': 'mouse', 'event': 'down', 'button': btn, 'x': pos.x(), 'y': pos.y()}
        self.mouse_event.emit(pickle.dumps(msg))
    
    def mouseReleaseEvent(self, e):
        """Handle mouse release event."""
        btn = {
            1: 'left',
            2: 'right',
            4: 'middle'
        }.get(e.button(), 'left')
        
        pos = self.calculate_remote_position(e.pos())
        if pos.x() < 0:
            return
        
        msg = {'type': 'mouse', 'event': 'up', 'button': btn, 'x': pos.x(), 'y': pos.y()}
        self.mouse_event.emit(pickle.dumps(msg))
    
    def wheelEvent(self, e):
        """Handle mouse wheel event."""
        delta = e.angleDelta().y()
        msg = {'type': 'mouse', 'event': 'wheel', 'delta': int(delta)}
        self.mouse_event.emit(pickle.dumps(msg))
    
    def keyPressEvent(self, e):
        """Handle key press event."""
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
        """Handle key release event."""
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
    def _special_from_qt(qkey: int) -> Optional[str]:
        """Map Qt key codes to special key names."""
        mapping = {
            Qt.Key_Return: 'ENTER', Qt.Key_Enter: 'ENTER',
            Qt.Key_Escape: 'ESC', Qt.Key_Backspace: 'BACKSPACE',
            Qt.Key_Tab: 'TAB', Qt.Key_Left: 'LEFT', Qt.Key_Right: 'RIGHT',
            Qt.Key_Up: 'UP', Qt.Key_Down: 'DOWN', Qt.Key_Delete: 'DELETE',
            Qt.Key_Home: 'HOME', Qt.Key_End: 'END',
            Qt.Key_PageUp: 'PAGEUP', Qt.Key_PageDown: 'PAGEDOWN',
        }
        return mapping.get(qkey, None)
