"""
Utility functions for AlbertDesk.
Includes helpers for ID generation, password generation, network utilities, etc.
"""

import hashlib
import io
import os
import pickle
import platform
import random
import socket
import string
import struct
import uuid
import zlib
from typing import Any, List, Optional, Set

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


class _RestrictedUnpickler(pickle.Unpickler):
    """Unpickler que sólo reconstruye datos primitivos (dict/list/str/int/float/
    bytes/bool/None/tuple/set). Los mensajes del protocolo de AlbertDesk son
    siempre de este tipo y nunca invocan find_class, así que bloquear cualquier
    referencia a clase/función (opcodes GLOBAL/STACK_GLOBAL) neutraliza el RCE
    clásico de pickle sin cambiar el formato de wire ni el comportamiento normal.
    """

    def find_class(self, module: str, name: str):
        raise pickle.UnpicklingError(
            f"Deserialización bloqueada: '{module}.{name}' no está permitido"
        )


def safe_pickle_loads(data: bytes) -> Any:
    """Deserializa datos pickle recibidos de un peer de red de forma segura.

    Usar SIEMPRE en vez de pickle.loads() para datos que llegan por el socket,
    ya que un pickle.loads() directo sobre datos no confiables permite ejecución
    de código arbitrario (ver specs/constitution.md § Seguridad).

    Args:
        data: Bytes pickle recibidos de la red.

    Returns:
        El objeto deserializado (dict/list/str/int/etc.).

    Raises:
        pickle.UnpicklingError: si los datos referencian una clase/función, o
            están corruptos/no son pickle válido.
    """
    return _RestrictedUnpickler(io.BytesIO(data)).load()


def recv_exact(sock: socket.socket, size: int, chunk_size: int = 131072) -> Optional[bytes]:
    """Lee exactamente `size` bytes de un socket, acumulando sobre varios recv().

    Un único recv() puede devolver menos bytes de los pedidos (streams TCP
    fragmentados); usar esta función evita truncar mensajes cortos como el
    handshake de autenticación.

    Args:
        sock: Socket conectado del que leer.
        size: Cantidad exacta de bytes a leer.
        chunk_size: Tamaño máximo de cada recv() individual.

    Returns:
        Los `size` bytes leídos, o None si la conexión se cerró antes de
        completar la lectura.
    """
    data = b""
    while len(data) < size:
        chunk = sock.recv(min(chunk_size, size - len(data)))
        if not chunk:
            return None
        data += chunk
    return data


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
