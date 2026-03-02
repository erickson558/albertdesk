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
import urllib.request
import shutil
from typing import Optional, Callable

logger = logging.getLogger(__name__)

TUNNEL_CONFIG_DIR = ".cloudflare"
TUNNEL_CONFIG_FILE = os.path.join(TUNNEL_CONFIG_DIR, "tunnel_config.json")


class CloudflareTunnelManager:
    """Manages Cloudflare Tunnel for internet connectivity."""
    
    def __init__(self, on_status_change: Optional[Callable[[str], None]] = None,
                 on_output: Optional[Callable[[str], None]] = None):
        """
        Initialize Cloudflare Tunnel Manager.
        
        Args:
            on_status_change: Callback function for status updates
            on_output: Callback function for terminal output
        """
        self.on_status_change = on_status_change
        self.on_output = on_output
        self.tunnel_process: Optional[subprocess.Popen] = None
        self.running = False
        self.tunnel_url: Optional[str] = None
        self.tunnel_id: Optional[str] = None
        
        # Ensure config directory exists
        os.makedirs(TUNNEL_CONFIG_DIR, exist_ok=True)
    
    def is_cloudflare_installed(self) -> bool:
        """Check if Cloudflare tunnel CLI is installed."""
        # First try to execute cloudflared command
        try:
            result = subprocess.run(
                ["cloudflared", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass
        
        # If that fails, check in common installation paths
        if sys.platform.startswith('win'):
            # Check Program Files
            program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
            exe_path_1 = os.path.join(program_files, 'cloudflared', 'cloudflared.exe')
            if os.path.exists(exe_path_1):
                return True
            
            # Check AppData Local Programs
            appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
            exe_path_2 = os.path.join(appdata, 'Programs', 'cloudflared', 'cloudflared.exe')
            if os.path.exists(exe_path_2):
                return True
        
        return False
    
    def get_installation_instructions(self) -> str:
        """Get instructions for installing Cloudflare Tunnel."""
        if sys.platform.startswith('win'):
            return """
📥 Instalación de Cloudflare Tunnel en Windows:

Método 1 (Automático - Recomendado):
  Haz clic en el botón "Instalar" y la app descargará e instalará cloudflared automáticamente.

Método 2 (Manual):
  1. Descarga desde: https://github.com/cloudflare/cloudflared/releases
  2. Busca: cloudflared-windows-amd64.exe
  3. Renómbralo a cloudflared.exe
  4. Muévelo a una carpeta en tu PATH

Método 3 (Con Scoop):
  scoop install cloudflared
"""
        elif sys.platform.startswith('darwin'):
            return """
📥 Instalación de Cloudflare Tunnel en macOS:

1. Con Homebrew (Recomendado):
   brew install cloudflared

2. Manual:
   Descarga desde: https://github.com/cloudflare/cloudflared/releases
   Busca: cloudflared-darwin-amd64.tgz

Una vez instalado, AlbertDesk lo detectará automáticamente.
"""
        else:  # Linux
            return """
📥 Instalación de Cloudflare Tunnel en Linux:

1. Debian/Ubuntu:
   curl -L https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
   echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/linux focal main' | sudo tee /etc/apt/sources.list.d/cloudflare-main.list
   sudo apt-get update && sudo apt-get install cloudflared

2. Manual:
   Descarga desde: https://github.com/cloudflare/cloudflared/releases
   Busca: cloudflared-linux-amd64

Una vez instalado, AlbertDesk lo detectará automáticamente.
"""
    
    def install_cloudflared(self) -> bool:
        """
        Install cloudflared automatically (Windows only).
        For other OS, shows manual instructions.
        
        Returns:
            True if installation successful or already installed
        """
        # Check if already installed
        if self.is_cloudflare_installed():
            if self.on_output:
                self.on_output("✅ Cloudflared ya está instalado")
            return True
        
        if sys.platform.startswith('win'):
            return self._install_windows()
        elif sys.platform.startswith('darwin'):
            if self.on_output:
                self.on_output("⚠️ En macOS, usa: brew install cloudflared")
                self.on_output(self.get_installation_instructions())
            return False
        else:  # Linux
            if self.on_output:
                self.on_output("⚠️ En Linux, consulta las instrucciones:")
                self.on_output(self.get_installation_instructions())
            return False
    
    def _install_windows(self) -> bool:
        """Install cloudflared on Windows automatically."""
        try:
            if self.on_output:
                self.on_output("="*60)
                self.on_output("🚀 INSTALACIÓN AUTOMÁTICA DE CLOUDFLARE TUNNEL")
                self.on_output("="*60)
                self.on_output("")
                self.on_output("📥 Descargando cloudflared desde GitHub...")
            
            # URL de la última versión de cloudflared para Windows
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
            
            # Crear carpeta temporal
            temp_dir = os.path.join(os.environ.get('TEMP', '.'), 'albertdesk_install')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Descargar archivo
            exe_path = os.path.join(temp_dir, "cloudflared.exe")
            
            if self.on_output:
                self.on_output(f"📂 Descargando a: {exe_path}")
            
            # Descargar con barra de progreso
            def download_progress(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min(100, (block_num * block_size * 100) // total_size)
                    if self.on_output and block_num % 50 == 0:  # Actualizar cada ~50 bloques
                        self.on_output(f"⏬ Progreso: {percent}%")
            
            urllib.request.urlretrieve(url, exe_path, download_progress)
            
            if self.on_output:
                self.on_output("✅ Descarga completada")
                self.on_output("")
                self.on_output("📦 Instalando cloudflared...")
            
            # Determinar la carpeta de instalación
            # Intentar instalar en C:\Program Files\cloudflared o en AppData del usuario
            program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
            install_dir = os.path.join(program_files, 'cloudflared')
            
            # Si no tenemos permisos para Program Files, usar AppData
            try:
                os.makedirs(install_dir, exist_ok=True)
            except PermissionError:
                appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
                install_dir = os.path.join(appdata, 'Programs', 'cloudflared')
                os.makedirs(install_dir, exist_ok=True)
                if self.on_output:
                    self.on_output(f"ℹ️ Instalando en perfil de usuario (sin permisos de admin)")
            
            # Copiar ejecutable
            final_path = os.path.join(install_dir, "cloudflared.exe")
            shutil.copy2(exe_path, final_path)
            
            if self.on_output:
                self.on_output(f"✅ Cloudflared instalado en: {install_dir}")
                self.on_output("")
                self.on_output("🔧 Agregando al PATH del sistema...")
            
            # Agregar al PATH del usuario (no requiere admin)
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_ALL_ACCESS)
                try:
                    current_path, _ = winreg.QueryValueEx(key, 'Path')
                except FileNotFoundError:
                    current_path = ''
                
                if install_dir not in current_path:
                    new_path = f"{current_path};{install_dir}" if current_path else install_dir
                    winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ, new_path)
                    if self.on_output:
                        self.on_output(f"✅ PATH actualizado")
                else:
                    if self.on_output:
                        self.on_output(f"ℹ️ La carpeta ya está en el PATH")
                
                winreg.CloseKey(key)
                
                # Notificar al sistema del cambio en las variables de entorno
                import ctypes
                HWND_BROADCAST = 0xFFFF
                WM_SETTINGCHANGE = 0x001A
                ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, 'Environment')
                
            except Exception as e:
                if self.on_output:
                    self.on_output(f"⚠️ No se pudo actualizar PATH automáticamente: {e}")
                    self.on_output(f"💡 Agrega manualmente al PATH: {install_dir}")
            
            # Limpiar archivos temporales
            try:
                os.remove(exe_path)
            except:
                pass
            
            if self.on_output:
                self.on_output("")
                self.on_output("="*60)
                self.on_output("✅ ¡INSTALACIÓN COMPLETADA!")
                self.on_output("="*60)
                self.on_output("")
                self.on_output("ℹ️ NOTA IMPORTANTE:")
                self.on_output("   Cierra y vuelve a abrir AlbertDesk para que los cambios")
                self.on_output("   en el PATH surtan efecto.")
                self.on_output("")
                self.on_output("   Después podrás usar el botón 'Iniciar Tunnel'")
                self.on_output("="*60)
            
            logger.info(f"Cloudflared installed successfully at {install_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install cloudflared: {e}")
            if self.on_output:
                self.on_output("")
                self.on_output(f"❌ Error durante la instalación: {e}")
                self.on_output("")
                self.on_output("💡 Puedes instalar manualmente:")
                self.on_output(self.get_installation_instructions())
            return False
    
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
                
                # Send output to terminal
                if self.on_output:
                    self.on_output(line.rstrip())
                
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
