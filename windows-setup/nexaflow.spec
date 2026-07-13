# -*- mode: python ; coding: utf-8 -*-
# NexaFlow — PyInstaller Build Spec
# Usage:  pyinstaller nexaflow.spec
# Output: dist\NexaFlow\NexaFlow.exe

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None
SPEC_DIR    = Path(os.path.abspath(sys.argv[0])).resolve().parent
PROJECT_ROOT = SPEC_DIR.parent
SCRIPT      = PROJECT_ROOT / 'nexaflow.py'
ICON        = SPEC_DIR / 'nexaflow.ico'
HAS_ICON    = ICON.exists()
try:
    TZDATA = collect_data_files('tzdata')
except Exception:
    TZDATA = []

a = Analysis(
    [str(SCRIPT)],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        # Include icon if present
        *([('nexaflow.ico', '.')] if HAS_ICON else []),
        # Include timezone database for reliable world time support on Windows.
        *TZDATA,
    ],
    hiddenimports=[
        # pynput — must be explicit, detection fails on some builds
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'pynput.keyboard._base',
        'pynput.mouse._base',
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        'pynput.keyboard._darwin',
        'pynput.mouse._darwin',
        'pynput.keyboard._xorg',
        'pynput.mouse._xorg',
        # clipboard
        'pyperclip',
        # Pillow
        'PIL',
        'PIL.Image',
        'PIL.ImageGrab',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'PIL.ImageTk',
        # tkinter — bundled with Python but declare explicitly
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.simpledialog',
        # Optional tray
        'pystray',
        # Timezone database
        'tzdata',
        # NexaFlow remote access (local LAN only)
        'remote_host',
        'http.server',
        'socketserver',
        'urllib.request',
        'urllib.parse',
        'secrets',
        'base64',
        # stdlib — sometimes missed by hook
        'threading',
        'pathlib',
        'json',
        'shutil',
        'subprocess',
        'datetime',
        'glob',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Keep the binary lean
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PyQt5',
        'PyQt6',
        'wx',
        'gi',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NexaFlow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,           # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON) if HAS_ICON else None,
    version_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NexaFlow',
)

