# Crea la carpeta del proyecto
$dir = "RustDeskClone"
New-Item -ItemType Directory -Force -Path $dir

# Archivos y contenido
$files = @{
    "client.py" = @'
import ssl, socket, sys, struct, zlib, pickle
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import json
import utils

def receive_data(sock):
    lengthbuf = sock.recv(4)
    length, = struct.unpack('!I', lengthbuf)
    data = b''
    while len(data) < length:
        to_read = length - len(data)
        data += sock.recv(4096 if to_read > 4096 else to_read)
    return pickle.loads(zlib.decompress(data))

class ClientWindow(QWidget):
    def __init__(self, host, port):
        super(ClientWindow, self).__init__()
        self.setWindowTitle("RustDesk Clone - Client")
        self.label = QLabel("Conectando...")
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.connect_to_server(host, port)

    def connect_to_server(self, host, port):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        sock = socket.create_connection((host, port))
        ssock = context.wrap_socket(sock, server_hostname=host)

        self.label.setText("Conectado, esperando imágenes...")
        self.show()

        while True:
            frame = receive_data(ssock)
            img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(img)
            self.label.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatio))

if __name__ == '__main__':
    with open("config.json") as f:
        cfg = json.load(f)
    app = QApplication(sys.argv)
    window = ClientWindow(cfg["host"], cfg["port"])
    sys.exit(app.exec_())
'@;

    "server.py" = @'
import ssl, socket, struct, pickle, zlib, threading, time
from PIL import ImageGrab
import io
import utils
import json

def send_data(conn, data):
    compressed = zlib.compress(pickle.dumps(data))
    length = struct.pack('!I', len(compressed))
    conn.sendall(length + compressed)

def handle_client(conn):
    try:
        while True:
            img = ImageGrab.grab().resize((800, 600)).convert('RGB')
            b = io.BytesIO()
            img.save(b, format='RAW')
            frame_data = b.getvalue()
            send_data(conn, frame_data)
            time.sleep(0.1)
    except:
        conn.close()

def start_server(host, port, certfile, keyfile):
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=certfile, keyfile=keyfile)

    bindsocket = socket.socket()
    bindsocket.bind((host, port))
    bindsocket.listen(5)
    print("Servidor escuchando en", host, "puerto", port)

    while True:
        newsocket, fromaddr = bindsocket.accept()
        conn = context.wrap_socket(newsocket, server_side=True)
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

if __name__ == '__main__':
    with open("config.json") as f:
        cfg = json.load(f)
    start_server(cfg["host"], cfg["port"], cfg["certfile"], cfg["keyfile"])
'@;

    "utils.py" = @'
import os, json, uuid

def get_or_create_id():
    if not os.path.exists("config.json"):
        device_id = str(uuid.uuid4())
        config = {
            "id": device_id,
            "host": "127.0.0.1",
            "port": 6969,
            "certfile": "server_cert.pem",
            "keyfile": "server_key.pem"
        }
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)
    else:
        with open("config.json") as f:
            config = json.load(f)
        if "id" not in config:
            config["id"] = str(uuid.uuid4())
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)

    return config["id"]

get_or_create_id()
'@;

    "cert_gen.py" = @'
import subprocess
import os

def generate_self_signed_cert(certfile="server_cert.pem", keyfile="server_key.pem"):
    if os.path.exists(certfile) and os.path.exists(keyfile):
        return
    subprocess.call([
        "openssl", "req", "-x509", "-newkey", "rsa:2048",
        "-keyout", keyfile, "-out", certfile, "-days", "365",
        "-nodes", "-subj", "/CN=RustDeskClone"
    ])

if __name__ == "__main__":
    generate_self_signed_cert()
'@;

    "config.json" = @'
{
    "id": "auto",
    "host": "127.0.0.1",
    "port": 6969,
    "certfile": "server_cert.pem",
    "keyfile": "server_key.pem"
}
'@;

    "requirements.txt" = @'
pyautogui
PyQt5
pillow
'@
}

# Crear y escribir cada archivo
foreach ($name in $files.Keys) {
    $path = Join-Path $dir $name
    Set-Content -Path $path -Value $files[$name] -Encoding UTF8
}

Write-Host "✅ Proyecto 'RustDeskClone' creado con todos los archivos."
