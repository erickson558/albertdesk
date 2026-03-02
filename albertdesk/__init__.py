"""
AlbertDesk - Remote Desktop Control Software
Version: 1.1.0
A Professional RustDesk-like application for remote desktop sharing and control.
"""

__version__ = "1.1.0"
__author__ = "Albert"
__license__ = "MIT"

from .backend.core.logger import setup_logging

# Initialize logging on module import
setup_logging()
