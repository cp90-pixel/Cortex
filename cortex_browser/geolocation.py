"""Helpers for enforcing modern geolocation security requirements."""

from __future__ import annotations

from ipaddress import ip_address

from PySide6.QtCore import QUrl


def is_secure_geolocation_origin(url: QUrl) -> bool:
    """Return ``True`` if *url* qualifies as a secure geolocation origin."""

    scheme = url.scheme().lower()

    if url.isLocalFile() or scheme in {"https", "wss"}:
        return True

    if scheme in {"blob", "filesystem"}:
        inner_url = QUrl(url.path())
        if inner_url.isValid() and inner_url != url:
            return is_secure_geolocation_origin(inner_url)
        return False

    if scheme == "http":
        host = url.host().lower()
        if not host:
            return False

        if host == "localhost" or host.endswith(".localhost"):
            return True

        try:
            return ip_address(host).is_loopback
        except ValueError:
            return False

    return False


__all__ = ["is_secure_geolocation_origin"]
