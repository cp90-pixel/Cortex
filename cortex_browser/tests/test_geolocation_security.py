"""Tests covering the geolocation origin security checks."""

from __future__ import annotations

import unittest

from PySide6.QtCore import QUrl

from cortex_browser.geolocation import is_secure_geolocation_origin


class GeolocationOriginSecurityTests(unittest.TestCase):
    """Validate the logic enforcing modern geolocation security requirements."""

    def assert_secure(self, url: str) -> None:
        self.assertTrue(
            is_secure_geolocation_origin(QUrl(url)),
            msg=f"Expected secure origin for {url}",
        )

    def assert_insecure(self, url: str) -> None:
        self.assertFalse(
            is_secure_geolocation_origin(QUrl(url)),
            msg=f"Expected insecure origin for {url}",
        )

    def test_https_is_secure(self) -> None:
        self.assert_secure("https://example.com")

    def test_wss_is_secure(self) -> None:
        self.assert_secure("wss://example.com/socket")

    def test_local_file_is_secure(self) -> None:
        self.assert_secure("file:///home/user/index.html")

    def test_localhost_variants_are_secure(self) -> None:
        self.assert_secure("http://localhost")
        self.assert_secure("http://subdomain.localhost")

    def test_loopback_addresses_are_secure(self) -> None:
        self.assert_secure("http://127.4.5.6")
        self.assert_secure("http://[::1]/")
        self.assert_secure("http://[::ffff:127.0.0.1]/")

    def test_standard_http_origin_is_insecure(self) -> None:
        self.assert_insecure("http://example.com")

    def test_private_network_address_is_insecure(self) -> None:
        self.assert_insecure("http://192.168.1.10")

    def test_blob_origin_inherits_security(self) -> None:
        self.assert_secure("blob:https://example.com/identifier")
        self.assert_insecure("blob:http://example.com/identifier")


if __name__ == "__main__":  # pragma: no cover - direct execution helper
    unittest.main()
