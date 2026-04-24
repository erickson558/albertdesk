"""
Build script for AlbertDesk PyInstaller compilation.
Creates a standalone executable with integrated icon in the project root folder.

Selecciona automáticamente el .venv del proyecto si existe, garantizando
que las dependencias correctas (PyQt5, Pillow, mss) sean bundleadas.

Usage:
    python build.py
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Forzar UTF-8 en la salida para que los emojis funcionen en Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Configuración del build ────────────────────────────────────────────────────
PROJECT_NAME = "AlbertDesk"
ICON_FILE    = "Albertdesk.ico"
OUTPUT_DIR   = "."        # El .exe se genera en la misma carpeta que los .py
BUILD_DIR    = "build"
SPEC_FILE    = f"{PROJECT_NAME}.spec"

# Dependencias requeridas (nombre de importación, nombre de paquete pip)
REQUIRED_PACKAGES = [
    ("PyQt5",   "PyQt5"),
    ("PIL",     "Pillow"),
    ("mss",     "mss"),
]


def get_python_exe() -> str:
    """Devuelve el Python del .venv del proyecto si existe; si no, el actual.

    Esto garantiza que PyInstaller use el entorno correcto con PyQt5
    y no el Python del sistema que podría tener PyQt6 u otras versiones
    incompatibles.
    """
    # Rutas del venv según plataforma
    if sys.platform.startswith("win"):
        venv_python = os.path.join(".venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join(".venv", "bin", "python")

    if os.path.exists(venv_python):
        print(f"🐍 Usando Python del .venv: {os.path.abspath(venv_python)}")
        return os.path.abspath(venv_python)

    print(f"🐍 .venv no encontrado, usando Python actual: {sys.executable}")
    return sys.executable


def check_dependencies(python_exe: str) -> bool:
    """Verifica que todas las dependencias requeridas estén disponibles.

    Args:
        python_exe: Ruta al ejecutable Python a verificar.

    Returns:
        True si todas las dependencias están presentes.
    """
    print("🔍 Verificando dependencias...")
    missing = []

    for import_name, pkg_name in REQUIRED_PACKAGES:
        result = subprocess.run(
            [python_exe, "-c", f"import {import_name}"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"   ✅ {pkg_name}")
        else:
            print(f"   ❌ {pkg_name} — NO encontrado")
            missing.append(pkg_name)

    if missing:
        print(f"\n❌ Dependencias faltantes: {', '.join(missing)}")
        print(f"   Instálalas con: {python_exe} -m pip install {' '.join(missing)}")
        return False

    print("✅ Todas las dependencias OK")
    return True


def check_icon() -> bool:
    """Verifica que el archivo de icono exista."""
    if not os.path.exists(ICON_FILE):
        print(f"❌ Icono no encontrado: {ICON_FILE}")
        print(f"   Coloca el icono en la carpeta raíz del proyecto")
        return False
    print(f"✅ Icono encontrado: {ICON_FILE}")
    return True


def clean_build_artifacts() -> None:
    """Elimina artefactos del build anterior."""
    print("🧹 Limpiando artefactos previos...")
    for directory in [BUILD_DIR, "__pycache__"]:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
                print(f"   Eliminado: {directory}")
            except PermissionError as e:
                print(f"   ⚠️  No se pudo eliminar {directory}: {e}")
                print(f"   Continuando de todos modos...")

    if os.path.exists(SPEC_FILE):
        try:
            os.remove(SPEC_FILE)
            print(f"   Eliminado: {SPEC_FILE}")
        except Exception as e:
            print(f"   ⚠️  No se pudo eliminar {SPEC_FILE}: {e}")


def build_executable(python_exe: str) -> bool:
    """Compila el ejecutable con PyInstaller usando el Python indicado.

    Args:
        python_exe: Ruta al ejecutable Python (preferiblemente el del .venv).

    Returns:
        True si la compilación fue exitosa.
    """
    print("🔨 Compilando ejecutable...")

    icon_arg = f"--icon={ICON_FILE}" if check_icon() else ""

    cmd = [
        python_exe, "-m", "PyInstaller",
        "--name",       PROJECT_NAME,
        "--onefile",                     # Un solo .exe autocontenido
        "--windowed",                    # Sin consola CMD al ejecutar
        # Incluye el paquete completo (backend, frontend, i18n)
        "--add-data",   f"albertdesk{os.pathsep}albertdesk",
        # PyQt5.sip está embebido en PyQt5 >= 5.11; declararlo evita el warning
        "--hidden-import", "PyQt5.sip",
        icon_arg,
        "--distpath",   OUTPUT_DIR,      # .exe queda junto a los .py
        "--workpath",   BUILD_DIR,
        "-y",
        "main.py",
    ]

    # Eliminar argumentos vacíos (cuando no hay icono)
    cmd = [arg for arg in cmd if arg]

    print(f"📦 Comando: {' '.join(cmd)}\n")

    result = subprocess.run(cmd)
    return result.returncode == 0


def create_launch_script() -> None:
    """Genera un .bat de lanzamiento para Windows."""
    if sys.platform.startswith("win"):
        batch_content = (
            f"@echo off\n"
            f"cd /d \"%~dp0\"\n"
            f"echo Starting {PROJECT_NAME}...\n"
            f"{PROJECT_NAME}.exe\n"
            f"pause\n"
        )
        bat_path = f"Launch-{PROJECT_NAME}.bat"
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(batch_content)
        print(f"📄 Launcher creado: {bat_path}")


def print_exe_info(python_exe: str) -> None:
    """Muestra información del .exe generado."""
    exe_name = f"{PROJECT_NAME}.exe" if sys.platform.startswith("win") else PROJECT_NAME
    exe_path = os.path.abspath(exe_name)

    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"📍 Ejecutable: {exe_path}")
        print(f"📦 Tamaño:     {size_mb:.1f} MB")
    else:
        print(f"⚠️  No se encontró el ejecutable en: {exe_path}")


def main() -> bool:
    """Proceso principal de compilación."""
    print(f"🏗️  Compilando {PROJECT_NAME}...")
    print("=" * 60)

    # Seleccionar el Python correcto (.venv > sistema)
    python_exe = get_python_exe()
    print()

    # Verificar PyInstaller en el Python seleccionado
    try:
        result = subprocess.run(
            [python_exe, "-m", "PyInstaller", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"✅ PyInstaller {result.stdout.strip()} disponible")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"❌ PyInstaller no está instalado en el entorno seleccionado")
        print(f"   Instálalo con: {python_exe} -m pip install pyinstaller")
        return False

    # Verificar dependencias del proyecto
    if not check_dependencies(python_exe):
        return False

    print()

    # Limpiar y compilar
    clean_build_artifacts()
    print()

    if not build_executable(python_exe):
        print("❌ Compilación fallida. Revisa los errores arriba.")
        return False

    # Crear launcher y mostrar resultado
    create_launch_script()

    print()
    print("=" * 60)
    print(f"✅ Compilación completada exitosamente!")
    print_exe_info(python_exe)
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
