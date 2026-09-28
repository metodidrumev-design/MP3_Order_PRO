# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all


datas = [
    ('assets', 'assets'),
    ('ffmpeg-n9.0-latest-win64-gpl-9.0', 'ffmpeg-n9.0-latest-win64-gpl-9.0')
]


binaries = []

hiddenimports = [
    'yt_dlp',
]


tmp_ret = collect_all('numpy')

datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]


tmp_ret = collect_all('PySide6')

datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]


a = Analysis(
    ['mp3_order.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)


# =====================================================
# BOOTLOADER SPLASH SCREEN
# =====================================================

splash = Splash(
    'assets/MP3_Order_PRO.ico',
    binaries=a.binaries,
    datas=a.datas,
)


pyz = PYZ(
    a.pure,
)


# =====================================================
# DEBUG EXE
# =====================================================

exe = EXE(
    pyz,
    splash,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MP3_Order_PRO_DEBUG',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/MP3_Order_PRO.ico'],
)


# =====================================================
# DEBUG COLLECT
# =====================================================

coll = COLLECT(
    exe,
    splash.binaries,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MP3_Order_PRO_DEBUG',
)