"""
Fullscreen window for remote desktop with floating controls overlay.
"""

from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtGui import QFont, QCursor

from ...backend.core.logger import get_logger

logger = get_logger(__name__)


class RemoteFullscreenWindow(QWidget):
    """
    Fullscreen window displaying remote desktop with floating control overlay.
    Features:
    - Pin/unpin controls
    - Auto-hide controls when not pinned
    - Exit fullscreen with ESC/F11/double-click
    """
    
    def __init__(self, remote_widget, on_exit):
        """
        Initialize fullscreen window.
        
        Args:
            remote_widget: RemoteDesktopWidget to display
            on_exit: Callback function when exiting fullscreen
        """
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
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.remote_widget)
        
        # Capture events
        self.installEventFilter(self)
        self.remote_widget.installEventFilter(self)
        
        # Build overlay
        self._build_overlay()
        self._position_overlay()
        self._show_overlay()
    
    def _build_overlay(self) -> None:
        """Build the control overlay panel."""
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
                font-weight: bold;
            }
            QPushButton:hover { 
                background: rgba(255,255,255,0.08); 
                border-radius: 8px; 
            }
            QPushButton:checked { 
                background: rgba(76,139,245,0.3); 
            }
            QLabel { 
                color: #eee; 
                font-weight: bold;
            }
        """)
        
        lay = QHBoxLayout(self._overlay)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(6)
        
        self.pin_btn = QPushButton("📌")
        self.pin_btn.setCheckable(True)
        self.pin_btn.setChecked(True)
        self.pin_btn.setToolTip("Fijar/ocultar controles")
        self.pin_btn.toggled.connect(self._on_pin_toggled)
        
        self.exit_btn = QPushButton("⤢ Salir")
        self.exit_btn.setToolTip("Salir de pantalla completa (Esc/F11)")
        self.exit_btn.clicked.connect(self.close)
        
        lay.addWidget(self.pin_btn)
        lay.addWidget(self.exit_btn)
        
        self._overlay.installEventFilter(self)
        self._overlay.show()
    
    def _position_overlay(self) -> None:
        """Position the overlay in the top-right corner."""
        if not self._overlay:
            return
        margin = 14
        self._overlay.adjustSize()
        size = self._overlay.sizeHint()
        w = size.width()
        h = size.height()
        self._overlay.setGeometry(self.width() - w - margin, margin, w, h)
        self._overlay.raise_()
    
    def _show_overlay(self) -> None:
        """Show the control overlay."""
        if self._overlay and not self._overlay.isVisible():
            self._overlay.show()
        self._overlay.raise_()
        if not self._pinned:
            self._auto_hide_timer.start()
    
    def _hide_overlay(self) -> None:
        """Hide the control overlay."""
        if self._overlay and self._overlay.isVisible():
            self._overlay.hide()
        self._auto_hide_timer.stop()
    
    def _on_pin_toggled(self, checked: bool) -> None:
        """Handle pin button toggle."""
        self._pinned = checked
        if self._pinned:
            self._show_overlay()
        else:
            self._auto_hide_timer.start()
    
    def _maybe_auto_hide(self) -> None:
        """Automatically hide overlay if mouse is not near top edge."""
        if not self._pinned:
            pos = self.mapFromGlobal(QCursor.pos())
            if pos.y() > 60:
                self._hide_overlay()
    
    def mouseMoveEvent(self, e):
        """Show overlay when mouse moves to top edge."""
        if not self._pinned and (e.pos().y() <= 30):
            self._show_overlay()
        super().mouseMoveEvent(e)
    
    def resizeEvent(self, e):
        """Reposition overlay on window resize."""
        self._position_overlay()
        super().resizeEvent(e)
    
    def eventFilter(self, obj, event):
        """Handle keyboard and mouse events."""
        if event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Escape, Qt.Key_F11):
                self.close()
                return True
        elif event.type() == QEvent.MouseButtonDblClick and obj is self.remote_widget:
            self.close()
            return True
        elif event.type() in (QEvent.Enter, QEvent.HoverEnter):
            if not self._pinned:
                self._show_overlay()
        return QWidget.eventFilter(self, obj, event)
    
    def closeEvent(self, event):
        """Handle window close."""
        try:
            if callable(self.on_exit):
                self.on_exit(self.remote_widget)
        except Exception as e:
            logger.error(f"Error in fullscreen exit callback: {e}")
        event.accept()
