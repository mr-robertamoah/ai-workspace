"""Resolve bundled data paths for both source and PyInstaller frozen builds."""

from __future__ import annotations

import sys
from pathlib import Path


def data_path(*parts: str) -> Path:
    """Return path to bundled data, works in both source and PyInstaller builds."""
    if getattr(sys, "frozen", False):
        # PyInstaller extracts data to sys._MEIPASS
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = Path(__file__).parent.parent / "data"
    return base.joinpath(*parts)
