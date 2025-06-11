# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['dd_cli.py'],
    pathex=[],
    binaries=[],
    datas=[('configs.yml', '.'), ('assets/base_heroes', 'assets/base_heroes'), ('assets/dungeon_assets', 'assets/dungeon_assets'), ('assets/icons', 'assets/icons'), ('assets/screens', 'assets/screens'), ('assets/themes', 'assets/themes'), ('assets/dungeon_despair_logo.png', 'assets/dungeon_despair_logo.png')],
    hiddenimports=[],
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
    name='dd_cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
