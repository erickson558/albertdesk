"""
Configuration management for AlbertDesk.
Handles loading and saving configuration files.
"""

import json
import os
from typing import Any, Dict
from .logger import get_logger

logger = get_logger(__name__)

CONFIG_FILE = "rustdesk_config.json"
HOSTS_FILE = "hosts.json"


def load_json(file_path: str, default: Any = None) -> Any:
    """
    Load JSON from file with error handling.
    
    Args:
        file_path: Path to JSON file
        default: Default value if file doesn't exist or is invalid
    
    Returns:
        Parsed JSON content or default value
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Error loading {file_path}: {e}")
    return default if default is not None else {}


def save_json(file_path: str, data: Dict[str, Any]) -> bool:
    """
    Save data to JSON file with error handling.
    
    Args:
        file_path: Path to JSON file
        data: Data to save
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving {file_path}: {e}")
        return False


def get_default_config() -> Dict[str, Any]:
    """Get default configuration dictionary."""
    from .utils import generate_id, generate_password
    
    return {
        "id": generate_id(),
        "password": generate_password(),
        "port": 6969,
        "remember_passwords": True,
        "auto_connect": False,
        "saved_passwords": {}
    }


class Config:
    """Configuration manager for the application."""
    
    def __init__(self, config_file: str = CONFIG_FILE):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create defaults."""
        existing = load_json(self.config_file, {})
        defaults = get_default_config()
        
        if isinstance(existing, dict):
            for key, value in existing.items():
                if key == 'saved_passwords' and isinstance(value, dict):
                    defaults[key].update(value)
                else:
                    defaults[key] = value
        
        # Save defaults to file
        save_json(self.config_file, defaults)
        return defaults
    
    def __getitem__(self, key: str) -> Any:
        """Get configuration value."""
        return self.data.get(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with default."""
        return self.data.get(key, default)
    
    def save(self) -> bool:
        """Save current configuration to file."""
        return save_json(self.config_file, self.data)
    
    def update(self, **kwargs) -> None:
        """Update multiple configuration values."""
        self.data.update(kwargs)
        self.save()
