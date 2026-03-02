"""
Utility functions for AlbertDesk.
Includes helpers for ID generation, password generation, network utilities, etc.
"""

import hashlib
import os
import platform
import random
import socket
import string
import struct
import uuid
import zlib
from typing import List, Optional, Set

from .logger import get_logger

logger = get_logger(__name__)


def generate_id() -> str:
    """
    Generate a unique ID for the device.
    
    Returns:
        Unique 9-digit string
    """
    try:
        node = platform.node()
        mac = uuid.getnode()
        unique_str = f"{node}-{mac}"
        return str(abs(hash(unique_str)))[:9]
    except Exception as e:
        logger.warning(f"Failed to generate ID from system info: {e}")
        return ''.join(random.choices(string.digits, k=9))


def generate_password(length: int = 12) -> str:
    """
    Generate a random password.
    
    Args:
        length: Password length
    
    Returns:
        Random password string
    """
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(chars, k=length))


def get_available_ips() -> List[str]:
    """
    Get all available IP addresses for the current system.
    
    Returns:
        Sorted list of IP addresses
    """
    ips: Set[str] = set()
    
    # Try hostname resolution
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None):
            family, _, _, _, sockaddr = info
            if family == socket.AF_INET:
                ip = sockaddr[0]
                if ip != "127.0.0.1":
                    ips.add(ip)
    except Exception as e:
        logger.debug(f"Error getting IPs from hostname: {e}")
    
    # Try external connection method
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except Exception as e:
        logger.debug(f"Error getting external IP: {e}")
    
    return sorted(ips) or ["127.0.0.1"]


def compress_data(data: bytes, level: int = 6) -> bytes:
    """
    Compress data using zlib.
    
    Args:
        data: Data to compress
        level: Compression level (0-9)
    
    Returns:
        Compressed data, or original if compression fails
    """
    try:
        return zlib.compress(data, level)
    except Exception as e:
        logger.warning(f"Compression failed: {e}")
        return data


def decompress_data(data: bytes) -> Optional[bytes]:
    """
    Decompress zlib data.
    
    Args:
        data: Compressed data
    
    Returns:
        Decompressed data or None if decompression fails
    """
    try:
        return zlib.decompress(data)
    except Exception as e:
        logger.debug(f"Decompression failed: {e}")
        return None


def pack_message(message: bytes) -> bytes:
    """
    Pack message with size header (4 bytes, big-endian).
    
    Args:
        message: Message to pack
    
    Returns:
        Packed message with size header
    """
    return struct.pack("!I", len(message)) + message


def unpack_message_size(header: bytes) -> Optional[int]:
    """
    Unpack message size from header.
    
    Args:
        header: 4-byte header
    
    Returns:
        Message size or None if invalid
    """
    try:
        if len(header) >= 4:
            return struct.unpack("!I", header[:4])[0]
    except Exception as e:
        logger.debug(f"Error unpacking message size: {e}")
    return None


def is_valid_ip(ip: str) -> bool:
    """
    Check if a string is a valid IP address.
    
    Args:
        ip: IP address string
    
    Returns:
        True if valid IPv4 address
    """
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False


def is_valid_port(port: int) -> bool:
    """
    Check if a port number is valid.
    
    Args:
        port: Port number
    
    Returns:
        True if port is between 1 and 65535
    """
    return 1 <= port <= 65535
