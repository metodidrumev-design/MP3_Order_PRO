# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all


# ============================================================
# DATA FILES
# ============================================================

datas = [
    (
        'D:/Visual Studio Code Projects/MP3_Order/assets',
        'assets'
    )
]


# ============================================================
# BINARIES
# ============================================================

binaries = []


# ============================================================
# HIDDEN IMPORTS
# ============================================================

hiddenimports = [
    'yt_dlp'
]


# ============================================================
# PYSIDE6
# ============================================================

tmp_ret = collect_all('PySide6')

datas += tmp_ret[0]

binaries += tmp_ret[1]

hiddenimports += tmp_ret[2]


# ============================================================
# ANALYSIS
# ============================================================

a = Analysis(
    [
        'D:/Visual Studio Code Projects/MP3_Order/mp3_order.py'
    ],

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


# ============================================================
# PYZ
# ============================================================

pyz = PYZ(
    a.pure
)


# ============================================================
# EXE
# ============================================================

exe = EXE(
    pyz,

    a.scripts,

    a.binaries,

    a.datas,

    [],

    name='MP3_Order_PRO',

    debug=False,

    bootloader_ignore_signals=False,

    strip=False,

    upx=True,

    upx_exclude=[],

    runtime_tmpdir=None,

    console=False,

    disable_windowed_traceback=False,

    argv_emulation=False,

    target_arch=None,

    codesign_identity=None,

    entitlements_file=None,

    icon=[
        'D:/Visual Studio Code Projects/MP3_Order/assets/MP3_Order_PRO.ico'
    ],
)