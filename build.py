"""
Build script for AlbertDesk PyInstaller compilation.
Creates a standalone executable with integrated icon.

Usage:
    python build.py
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Configuration
PROJECT_NAME = "AlbertDesk"
ICON_FILE = "Albertdesk.ico"
OUTPUT_DIR = "."  # Generate exe in current folder
BUILD_DIR = "build"
SPEC_FILE = f"{PROJECT_NAME}.spec"

def check_icon():
    """Check if icon file exists."""
    if not os.path.exists(ICON_FILE):
        print(f"❌ Icon file not found: {ICON_FILE}")
        print(f"Place the icon file in the project root directory")
        return False
    print(f"✅ Icon found: {ICON_FILE}")
    return True

def clean_build_artifacts():
    """Clean previous build artifacts."""
    print("🧹 Cleaning build artifacts...")
    for directory in [BUILD_DIR, "__pycache__"]:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
                print(f"   Removed: {directory}")
            except PermissionError as e:
                print(f"   ⚠️  Could not remove {directory}: {e}")
                print(f"   Continuing anyway...")
    
    if os.path.exists(SPEC_FILE):
        try:
            os.remove(SPEC_FILE)
            print(f"   Removed: {SPEC_FILE}")
        except Exception as e:
            print(f"   ⚠️  Could not remove {SPEC_FILE}: {e}")

def build_executable():
    """Build executable using PyInstaller."""
    print("🔨 Building executable...")
    
    if not check_icon():
        print("⚠️  Continuing without icon...")
        icon_arg = ""
    else:
        icon_arg = f'--icon={ICON_FILE}'
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", PROJECT_NAME,
        "--onefile",
        "--windowed",
        "--add-data", f"albertdesk{os.pathsep}albertdesk",
        icon_arg,
        "--distpath", OUTPUT_DIR,
        "--workpath", BUILD_DIR,
        "-y",
        "main.py"
    ]
    
    # Remove empty argument if icon not found
    cmd = [arg for arg in cmd if arg != ""]
    
    print(f"📦 Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd)
    return result.returncode == 0

def create_launch_script():
    """Create a batch file for easy launching on Windows."""
    if sys.platform.startswith('win'):
        batch_content = f"""@echo off
cd /d "%~dp0"
echo Starting {PROJECT_NAME}...
dist\\{PROJECT_NAME}.exe
pause
"""
        with open(f"Launch-{PROJECT_NAME}.bat", 'w', encoding='utf-8') as f:
            f.write(batch_content)
        print(f"File created: Launch-{PROJECT_NAME}.bat")

def main():
    """Main build process."""
    print(f"🏗️  Building {PROJECT_NAME}...")
    print("=" * 60)
    
    # Check PyInstaller
    try:
        subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], 
                      capture_output=True, check=True)
        print("✅ PyInstaller found")
    except subprocess.CalledProcessError:
        print("❌ PyInstaller not installed")
        print("📥 Install it with: pip install pyinstaller")
        return False
    
    # Clean and build
    clean_build_artifacts()
    
    if not build_executable():
        print("❌ Build failed!")
        return False
    
    # Create launch script
    create_launch_script()
    
    # Print summary
    print("=" * 60)
    print(f"✅ Build completed successfully!")
    exe_name = f"{PROJECT_NAME}.exe" if sys.platform.startswith('win') else PROJECT_NAME
    print(f"📍 Executable: {exe_name} (in current folder)")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
