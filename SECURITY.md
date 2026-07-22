# Política de Seguridad

## Reportar una vulnerabilidad

Si encuentras una vulnerabilidad de seguridad en AlbertDesk, por favor **no abras un
issue público**. Repórtala de forma privada abriendo un
[GitHub Security Advisory](https://github.com/erickson558/albertdesk/security/advisories/new)
en el repositorio, o contactando directamente al mantenedor. Incluye pasos para
reproducir y el impacto potencial.

## Versiones soportadas

Sólo la última versión publicada recibe parches de seguridad.

## Estado actual (a partir de V1.3.2)

### Mitigado
- **Deserialización insegura (RCE vía pickle)**: todo dato que llega por red pasa por
  `safe_pickle_loads()` (`albertdesk/backend/core/utils.py`), un `Unpickler`
  restringido que bloquea la reconstrucción de cualquier clase/función
  (`find_class` siempre lanza `UnpicklingError`). Los mensajes del protocolo son
  siempre tipos primitivos (dict/list/str/int/bytes), que nunca requieren
  `find_class`, así que esto no cambia el comportamiento normal.
- **Path traversal en transferencia de archivos**: el nombre de archivo recibido se
  sanea con `os.path.basename()` antes de usarse en una ruta local
  (`connection_manager.py::_handle_file_message`).
- **DoS por tamaño de mensaje no acotado en el handshake de autenticación**: el
  tamaño anunciado antes de validar la contraseña está acotado a
  `MAX_AUTH_MESSAGE_SIZE` (4 KiB).
- **Comparación de contraseña no constante en tiempo**: ahora usa
  `hmac.compare_digest()`.

### Limitaciones conocidas (no mitigadas — roadmap)
- **Sin TLS/cifrado end-to-end**: la conexión P2P directa (`connection_manager.py`)
  viaja en texto plano sobre TCP. Cualquiera con acceso a la red entre los dos
  equipos (o que intercepte el tráfico del Cloudflare Tunnel a nivel de aplicación)
  puede ver la contraseña, los eventos de teclado/mouse y las capturas de pantalla.
  Esto es un rediseño de protocolo (versión major), no un patch — se recomienda usar
  AlbertDesk sólo en redes de confianza (LAN propia) o a través de Cloudflare Tunnel
  entendiendo que el cifrado que aporta Cloudflare cubre el transporte hasta su
  borde, no un cifrado end-to-end verificado por la app.
- **Contraseñas guardadas en disco sin cifrar**: `saved_passwords` en
  `rustdesk_config.json` se guarda en JSON plano. Cualquiera con acceso al
  sistema de archivos del usuario puede leerlas.
- **Sin límite de intentos de autenticación por IP**: un atacante puede intentar
  fuerza bruta de contraseña repetidamente contra el puerto del servidor; no hay
  rate-limiting ni bloqueo temporal todavía.

Si necesitas un canal cifrado hoy, usa AlbertDesk únicamente dentro de una red ya
protegida (VPN propia, LAN de confianza) hasta que el cifrado end-to-end esté
implementado.
