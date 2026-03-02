"""
Cloudflare Tunnel integration for internet connectivity.
Provides optional relay connection without needing a personal server.
"""

import json
import logging
import os
import subprocess
import sys
import threading
from typing import Optional, Callable

logger = logging.getLogger(__name__)

TUNNEL_CONFIG_DIR = ".cloudflare"
TUNNEL_CONFIG_FILE = os.path.join(TUNNEL_CONFIG_DIR, "tunnel_config.json")


class CloudflareTunnelManager:
    """Manages Cloudflare Tunnel for internet connectivity."""
    
    def __init__(self, on_status_change: Optional[Callable[[str], None]] = None):
        """
        Initialize Cloudflare Tunnel Manager.
        
        Args:
            on_status_change: Callback function for status updates
        """
        self.on_status_change = on_status_change
        self.tunnel_process: Optional[subprocess.Popen] = None
        self.running = False
        self.tunnel_url: Optional[str] = None
        self.tunnel_id: Optional[str] = None
        
        # Ensure config directory exists
        os.makedirs(TUNNEL_CONFIG_DIR, exist_ok=True)
    
    def is_cloudflare_installed(self) -> bool:
        """Check if Cloudflare tunnel CLI is installed."""
        try:
            result = subprocess.run(
                ["cloudflared", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"Cloudflared not found: {e}")
            return False
    
    def get_installation_instructions(self) -> str:
        """Get instructions for installing Cloudflare Tunnel."""
        if sys.platform.startswith('win'):
            return """
📥 Instala Cloudflare Tunnel en Windows:

1. Descarga desde: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
2. O usa PowerShell:
   scoop install cloudflare-warp
   
3. O descarga directo:
   https://github.com/cloudflare/cloudflared/releases (buscas cloudflared-windows-amd64.exe)

4. Una vez instalado, AlbertDesk lo detectará automáticamente
"""
        elif sys.platform.startswith('darwin'):
            return """
📥 Instala Cloudflare Tunnel en macOS:

1. Con Homebrew:
   brew install cloudflare/warp/cloudflared

2. Una vez instalado, AlbertDesk lo detectará automáticamente
"""
        else:  # Linux
            return """
📥 Instala Cloudflare Tunnel en Linux:

1. Con apt (Debian/Ubuntu):
   curl -L https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
   echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/linux focal main' | sudo tee /etc/apt/sources.list.d/cloudflare-main.list
   sudo apt-get update && sudo apt-get install cloudflared

2. Una vez instalado, AlbertDesk lo detectará automáticamente
"""
    
    def start_tunnel(self, local_port: int) -> bool:
        """
        Start Cloudflare Tunnel.
        
        Args:
            local_port: Local port to expose (default 6969)
        
        Returns:
            True if tunnel started successfully
        """
        if not self.is_cloudflare_installed():
            logger.error("Cloudflare tunnel is not installed")
            if self.on_status_change:
                self.on_status_change("❌ Cloudflare Tunnel no está instalado")
            return False
        
        try:
            if self.on_status_change:
                self.on_status_change("🔄 Iniciando Cloudflare Tunnel...")
            
            logger.info(f"Starting tunnel for localhost:{local_port}")
            
            self.tunnel_process = subprocess.Popen(
                ["cloudflared", "tunnel", "--url", f"localhost:{local_port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            self.running = True
            
            # Start thread to capture tunnel URL
            threading.Thread(target=self._capture_tunnel_url, daemon=True).start()
            
            if self.on_status_change:
                self.on_status_change("🌐 Tunnel iniciado, esperando URL...")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to start tunnel: {e}")
            if self.on_status_change:
                self.on_status_change(f"❌ Error iniciando tunnel: {e}")
            return False
    
    def _capture_tunnel_url(self) -> None:
        """Capture the tunnel URL from cloudflared output."""
        if not self.tunnel_process:
            return
        
        try:
            while self.running and self.tunnel_process.poll() is None:
                line = self.tunnel_process.stderr.readline()
                if not line:
                    continue
                
                logger.debug(f"Tunnel output: {line.strip()}")
                
                # Look for URL in output
                if "Accessible at" in line or "https://" in line:
                    # Extract URL (format: "Accessible at https://xxxxx.trycloudflare.com")
                    parts = line.split("https://")
                    if len(parts) > 1:
                        url_part = parts[1].strip().split()[0]
                        self.tunnel_url = f"https://{url_part}"
                        logger.info(f"Tunnel URL: {self.tunnel_url}")
                        
                        # Save tunnel URL
                        self._save_tunnel_config()
                        
                        if self.on_status_change:
                            self.on_status_change(f"✅ URL Tunnel: {self.tunnel_url}")
                else:
                    if self.on_status_change:
                        self.on_status_change(line.strip())
        
        except Exception as e:
            logger.error(f"Error capturing tunnel URL: {e}")
    
    def _save_tunnel_config(self) -> None:
        """Save tunnel configuration to file."""
        try:
            config = {
                "tunnel_url": self.tunnel_url,
                "tunnel_id": self.tunnel_id
            }
            with open(TUNNEL_CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tunnel config: {e}")
    
    def load_tunnel_config(self) -> Optional[dict]:
        """Load saved tunnel configuration."""
        try:
            if os.path.exists(TUNNEL_CONFIG_FILE):
                with open(TUNNEL_CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Failed to load tunnel config: {e}")
        return None
    
    def stop_tunnel(self) -> None:
        """Stop the Cloudflare Tunnel."""
        self.running = False
        if self.tunnel_process:
            try:
                self.tunnel_process.terminate()
                self.tunnel_process.wait(timeout=5)
                logger.info("Tunnel stopped")
            except subprocess.TimeoutExpired:
                self.tunnel_process.kill()
                logger.warning("Tunnel force-killed")
            except Exception as e:
                logger.error(f"Error stopping tunnel: {e}")
            finally:
                self.tunnel_process = None
        
        if self.on_status_change:
            self.on_status_change("🔴 Tunnel detenido")
    
    def get_tunnel_url(self) -> Optional[str]:
        """Get the current tunnel URL."""
        return self.tunnel_url
