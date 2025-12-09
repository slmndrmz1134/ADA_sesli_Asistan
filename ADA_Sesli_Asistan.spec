# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['asistan_complete.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/SELMAN/OneDrive/Desktop/Python Asistan', 'Python Asistan')],
    hiddenimports=['pycaw.pycaw', 'comtypes', 'TTS', 'torch', 'pygame', 'cv2', 'google.generativeai', 'speech_recognition', 'keyboard'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ADA_Sesli_Asistan',
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
    icon='NONE',
)
