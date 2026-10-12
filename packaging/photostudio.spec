# PyInstaller spec for PhotoStudio (used by the CI release pipeline).
# Build from the project root:
#     pyinstaller packaging/photostudio.spec
# Produces dist/PhotoStudio/PhotoStudio.exe (one-folder, windowed).
# Inno Setup then wraps dist/PhotoStudio into PhotoStudio-Setup.exe.
import os

ROOT = os.path.abspath(os.getcwd())
ICON = os.path.join(ROOT, 'photostudio', 'resources', 'icon.ico')
VERSION_FILE = os.path.join(ROOT, 'packaging', 'version_info.txt')

block_cipher = None

a = Analysis(
    [os.path.join(ROOT, 'run.py')],
    pathex=[ROOT],
    binaries=[],
    datas=[(os.path.join(ROOT, 'photostudio', 'resources'), 'photostudio/resources')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'PySide6.QtWebEngineCore', 'PySide6.Qt3D'],
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PhotoStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=ICON if os.path.exists(ICON) else None,
    version=VERSION_FILE if os.path.exists(VERSION_FILE) else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='PhotoStudio',
)
