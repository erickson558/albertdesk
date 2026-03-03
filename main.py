#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AlbertDesk - Remote Desktop Control Software
A professional remote desktop application with LAN and internet connectivity.

Usage:
    python main.py
"""

import signal
import sys
import logging
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from albertdesk.backend.core.logger import setup_logging, get_logger
from albertdesk.frontend.ui.main_window import AlbertDeskWindow

__version__ = "1.2.2"

logger = get_logger(__name__)


def main():
    """Main application entry point."""
    # Setup logging
    setup_logging()
    logger.info(f"Starting AlbertDesk v{__version__}")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("AlbertDesk")
    app.setApplicationVersion(__version__)
    
    # Create main window
    window = AlbertDeskWindow()
    window.show()
    
    # Setup graceful shutdown
    def graceful_shutdown(*args):
        """Handle shutdown signals gracefully."""
        logger.info("Shutting down...")
        try:
            window.conn_manager.stop()
            window.tunnel_manager.stop_tunnel()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        QTimer.singleShot(0, app.quit)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, graceful_shutdown)
    if hasattr(signal, 'SIGBREAK'):  # Windows
        signal.signal(signal.SIGBREAK, graceful_shutdown)
    
    # Run application
    try:
        exit_code = app.exec_()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        exit_code = 0
    finally:
        # Cleanup
        try:
            window.conn_manager.stop()
            window.tunnel_manager.stop_tunnel()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
