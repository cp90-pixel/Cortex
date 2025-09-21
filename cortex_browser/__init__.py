"""Cortex Browser package."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - imported for type checkers only
    from .app import APP_NAME, BrowserWindow, build_application, main, run

__all__ = [
    "APP_NAME",
    "BrowserWindow",
    "build_application",
    "main",
    "run",
]


def __getattr__(name: str):  # pragma: no cover - trivial delegation
    if name in __all__:
        module = import_module(".app", __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(name)  # pragma: no cover - behaviour mirrors default


__version__ = "0.1.0"
