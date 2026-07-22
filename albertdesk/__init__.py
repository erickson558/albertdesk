"""
AlbertDesk - Remote Desktop Control Software
Version: 1.3.2
A Professional RustDesk-like application for remote desktop sharing and control.
"""

__version__ = "1.3.2"
__author__ = "Albert"
__license__ = "Apache-2.0"

from .backend.core.logger import setup_logging

# Initialize logging on module import
setup_logging()
