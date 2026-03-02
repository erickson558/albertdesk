"""
Windows input injection for remote control.
Handles mouse and keyboard events on Windows systems.
"""

import ctypes
from typing import Optional, Union

from ..core.logger import get_logger

logger = get_logger(__name__)


class MOUSEINPUT(ctypes.Structure):
    """Windows MOUSEINPUT structure."""
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]


class KEYBDINPUT(ctypes.Structure):
    """Windows KEYBDINPUT structure."""
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]


class HARDWAREINPUT(ctypes.Structure):
    """Windows HARDWAREINPUT structure."""
    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_short),
        ("wParamH", ctypes.c_short)
    ]


class INPUT_UNION(ctypes.Union):
    """Union for INPUT structure."""
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT)
    ]


class INPUT(ctypes.Structure):
    """Windows INPUT structure."""
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("union", INPUT_UNION)
    ]


class WinInput:
    """
    Windows input controller for mouse and keyboard injection.
    Uses ctypes to call Windows API functions.
    """
    
    # Input types
    INPUT_MOUSE = 0
    INPUT_KEYBOARD = 1
    
    # Keyboard event flags
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_UNICODE = 0x0004
    KEYEVENTF_SCANCODE = 0x0008
    
    # Mouse event flags
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
        """Initialize Windows input controller."""
        try:
            self.user32 = ctypes.windll.user32
            # Set DPI awareness for proper coordinate handling
            try:
                self.user32.SetProcessDPIAware()
            except Exception as e:
                logger.debug(f"Could not set DPI aware: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize WinInput: {e}")
            raise
    
    def _send(self, inputs: list) -> None:
        """
        Send input events to Windows.
        
        Args:
            inputs: List of INPUT structures
        """
        try:
            n = len(inputs)
            arr = (INPUT * n)(*inputs)
            self.user32.SendInput(n, ctypes.byref(arr), ctypes.sizeof(INPUT))
        except Exception as e:
            logger.error(f"Error sending input: {e}")
    
    def move_mouse_px(self, x: int, y: int) -> None:
        """
        Move mouse to absolute position.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        try:
            self.user32.SetCursorPos(int(x), int(y))
        except Exception as e:
            logger.error(f"Error moving mouse: {e}")
    
    def mouse_button(self, button: str, down: bool = True) -> None:
        """
        Simulate mouse button press/release.
        
        Args:
            button: Button name ('left', 'right', 'middle')
            down: True for press, False for release
        """
        flags_map = {
            "left": (self.MOUSEEVENTF_LEFTDOWN if down else self.MOUSEEVENTF_LEFTUP),
            "right": (self.MOUSEEVENTF_RIGHTDOWN if down else self.MOUSEEVENTF_RIGHTUP),
            "middle": (self.MOUSEEVENTF_MIDDLEDOWN if down else self.MOUSEEVENTF_MIDDLEUP),
        }
        
        flags = flags_map.get(button.lower())
        if flags is None:
            logger.warning(f"Unknown mouse button: {button}")
            return
        
        mi = MOUSEINPUT(0, 0, 0, flags, 0, None)
        self._send([INPUT(self.INPUT_MOUSE, INPUT_UNION(mi=mi))])
    
    def mouse_wheel(self, delta: int) -> None:
        """
        Simulate mouse wheel scroll.
        
        Args:
            delta: Scroll delta (positive=up, negative=down)
        """
        mi = MOUSEINPUT(0, 0, ctypes.c_ulong(int(delta)), self.MOUSEEVENTF_WHEEL, 0, None)
        self._send([INPUT(self.INPUT_MOUSE, INPUT_UNION(mi=mi))])
    
    def key_vk(self, vk: int, down: bool = True) -> None:
        """
        Simulate key press/release using virtual key code.
        
        Args:
            vk: Virtual key code
            down: True for press, False for release
        """
        ki = KEYBDINPUT(vk, 0, 0 if down else self.KEYEVENTF_KEYUP, 0, None)
        self._send([INPUT(self.INPUT_KEYBOARD, INPUT_UNION(ki=ki))])
    
    def key_unicode(self, char: str, down: bool = True) -> None:
        """
        Simulate key press/release using unicode character.
        
        Args:
            char: Character to type
            down: True for press, False for release
        """
        ki = KEYBDINPUT(
            0, 
            ord(char), 
            self.KEYEVENTF_UNICODE | (0 if down else self.KEYEVENTF_KEYUP), 
            0, 
            None
        )
        self._send([INPUT(self.INPUT_KEYBOARD, INPUT_UNION(ki=ki))])
