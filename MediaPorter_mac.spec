# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for macOS .app bundle
# Build: pyinstaller MediaPorter_mac.spec

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('appicon.icns', '.'),
        ('appicon.ico', '.'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.pool',
        'exifread',
        'pymediainfo',
        'tomli',
        'tomli_w',
        'backend.core.scanner',
        'backend.core.importer',
        'backend.core.rules',
        'backend.core.dedup',
        'backend.core.safety',
        'backend.core.inspector',
        'backend.core.models',
        'backend.core.camera_profiles',
        'backend.db.models',
        'backend.db.repository',
        'backend.utils.detector',
        'backend.utils.config',
        'backend.utils.log_setup',
        'gui.main_window',
        'gui.theme',
        'gui.widgets.source_panel',
        'gui.widgets.dest_panel',
        'gui.widgets.file_table',
        'gui.widgets.history_panel',
        'gui.widgets.settings_panel',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy'],
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
    name='Media Porter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='appicon.icns',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Media Porter',
)

app = BUNDLE(
    coll,
    name='Media Porter.app',
    icon='appicon.icns',
    bundle_identifier='com.mediaporter.app',
    info_plist={
        'CFBundleName': 'Media Porter',
        'CFBundleDisplayName': 'Media Porter',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSMinimumSystemVersion': '11.0',
        'CFBundleDocumentTypes': [],
        'NSHumanReadableCopyright': '© 2026 Media Porter',
    },
)
