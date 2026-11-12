# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

desktop = Path(SPECPATH).resolve().parent
src = desktop / "src"
resources = src / "textshield_desktop" / "resources"
entry = desktop / "run_desktop.py"

a = Analysis(
    [str(entry)],
    pathex=[str(src)],
    binaries=[],
    datas=[(str(resources), "textshield_desktop/resources")],
    hiddenimports=["PySide6.QtSvg"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtPdf",
        "PySide6.QtPdfWidgets",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtQuick3D",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TextShieldDesktop",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(resources / "icons" / "textshield.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="TextShieldDesktop",
)
