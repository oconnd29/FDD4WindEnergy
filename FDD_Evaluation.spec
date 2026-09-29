# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

root = Path(SPECPATH)
hidden = collect_submodules("fdd_eval")

a = Analysis(
    [str(root / "launch.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "fdd_eval" / "assets"), "fdd_eval/assets"),
        (str(root / "tutorials"), "tutorials"),
    ],
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="FDD_Evaluation",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=str(root / "fdd_eval" / "assets" / "app.ico"),
)
