"""Resolve bundled assets and tutorials (source tree or frozen exe)."""

from __future__ import annotations

import sys
from pathlib import Path


def resource_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def assets_dir() -> Path:
    return Path(__file__).resolve().parent / "assets"


def app_icon_path() -> Path:
    return assets_dir() / "app.ico"
