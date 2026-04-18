# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('ui/styles.qss', 'ui'), ('ui/resources', 'ui/resources'), ('locales', 'locales'), ('web_app', 'web_app'), ('controllers', 'controllers'), ('database', 'database'), ('models', 'models'), ('utils', 'utils'), ('deploy.ps1', '.'), ('Dockerfile', '.'), ('docker-compose.yml', '.'), ('requirements-web.txt', '.'), ('.dockerignore', '.'), ('README.md', '.'), ('LICENSE', '.'), ('PRIVACY.txt', '.')],
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
    name='Shark Contabilidad',
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
    icon=['icono.ico'],
)
