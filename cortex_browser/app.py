"""Cortex Browser application implementation."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QUrl, Qt, Slot
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QToolBar,
)
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView


APP_NAME = "Cortex Browser"
DEFAULT_HOME_PAGE = Path(__file__).resolve().parent / "resources" / "home.html"
DEFAULT_SEARCH_PROVIDER = "https://duckduckgo.com/?q={query}"


@dataclass
class NavigationEntry:
    """Represents a navigation history entry."""

    title: str
    url: QUrl


class BrowserWindow(QMainWindow):
    """Main window for the Cortex Browser."""

    def __init__(self, home_url: Optional[QUrl] = None) -> None:
        super().__init__()
        self._home_url = home_url or QUrl.fromLocalFile(str(DEFAULT_HOME_PAGE))
        self._history: list[NavigationEntry] = []
        self._permission_store: dict[tuple[str, int], QWebEnginePage.PermissionPolicy] = {}

        self.setWindowTitle(APP_NAME)
        self.resize(1200, 800)

        self.web_view = QWebEngineView(self)
        self.web_view.setUrl(self._home_url)
        self.web_view.titleChanged.connect(self._update_title)
        self.web_view.urlChanged.connect(self._update_url_bar)
        self.web_view.loadProgress.connect(self._update_load_progress)
        self.web_view.loadFinished.connect(self._handle_load_finished)
        self.web_view.page().featurePermissionRequested.connect(
            self._handle_feature_permission_request
        )
        self.setCentralWidget(self.web_view)

        self.navigation_bar = self._create_navigation_bar()
        self._create_menu_bar()
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

    # ------------------------------------------------------------------
    # UI construction helpers
    # ------------------------------------------------------------------
    def _create_navigation_bar(self) -> QToolBar:
        toolbar = QToolBar("Navigation", self)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        back_action = QAction(QIcon.fromTheme("go-previous"), "Back", self)
        back_action.setShortcut(QKeySequence.Back)
        back_action.triggered.connect(self.web_view.back)
        toolbar.addAction(back_action)

        forward_action = QAction(QIcon.fromTheme("go-next"), "Forward", self)
        forward_action.setShortcut(QKeySequence.Forward)
        forward_action.triggered.connect(self.web_view.forward)
        toolbar.addAction(forward_action)

        reload_action = QAction(QIcon.fromTheme("view-refresh"), "Reload", self)
        reload_action.setShortcut(QKeySequence.Refresh)
        reload_action.triggered.connect(self.web_view.reload)
        toolbar.addAction(reload_action)

        stop_action = QAction(QIcon.fromTheme("process-stop"), "Stop", self)
        stop_action.setShortcut(QKeySequence.Cancel)
        stop_action.triggered.connect(self.web_view.stop)
        toolbar.addAction(stop_action)

        home_action = QAction(QIcon.fromTheme("go-home"), "Home", self)
        home_action.setShortcut(QKeySequence("Ctrl+H"))
        home_action.triggered.connect(self.navigate_home)
        toolbar.addAction(home_action)

        open_file_action = QAction(QIcon.fromTheme("document-open"), "Open File…", self)
        open_file_action.setShortcut(QKeySequence("Ctrl+O"))
        open_file_action.triggered.connect(self.open_local_file)
        toolbar.addAction(open_file_action)

        toolbar.addSeparator()

        self.url_bar = QLineEdit(self)
        self.url_bar.setPlaceholderText("Enter URL or search query")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        toolbar.addWidget(self.url_bar)

        go_action = QAction(QIcon.fromTheme("system-search"), "Go", self)
        go_action.triggered.connect(self.navigate_to_url)
        toolbar.addAction(go_action)

        self.addToolBar(toolbar)

        focus_address_action = QAction("Focus Address Bar", self)
        focus_address_action.setShortcut(QKeySequence("Ctrl+L"))
        focus_address_action.triggered.connect(self._focus_address_bar)
        self.addAction(focus_address_action)

        return toolbar

    def _create_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction("Open File…", self.open_local_file, shortcut=QKeySequence("Ctrl+O"))
        file_menu.addAction("Exit", self.close, shortcut=QKeySequence("Ctrl+Q"))

        navigate_menu = menu_bar.addMenu("&Navigate")
        navigate_menu.addAction("Home", self.navigate_home, shortcut=QKeySequence("Ctrl+H"))
        navigate_menu.addAction("Reload", self.web_view.reload, shortcut=QKeySequence.Refresh)
        navigate_menu.addAction("Show History", self.show_history)

        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction("About Cortex Browser", self.show_about_dialog)

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------
    @Slot()
    def navigate_to_url(self) -> None:
        text = self.url_bar.text().strip()
        if not text:
            return

        url = self._normalize_input(text)
        self._navigate(url)

    @Slot()
    def navigate_home(self) -> None:
        self._navigate(self._home_url)

    def open_local_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open local file",
            str(Path.home()),
            "HTML files (*.html *.htm);;All files (*)",
        )
        if file_path:
            self._navigate(QUrl.fromLocalFile(file_path))

    def _navigate(self, url: QUrl) -> None:
        self.status_bar.showMessage(f"Loading {url.toDisplayString()}…")
        self.web_view.setUrl(url)

    @staticmethod
    def _normalize_input(text: str) -> QUrl:
        """Normalize user input into a navigable :class:`QUrl`."""

        if " " in text:
            encoded = bytes(QUrl.toPercentEncoding(text)).decode()
            search_url = DEFAULT_SEARCH_PROVIDER.format(query=encoded)
            return QUrl(search_url)

        return QUrl.fromUserInput(text)

    # ------------------------------------------------------------------
    # Slots updating UI state
    # ------------------------------------------------------------------
    def _update_title(self, title: str) -> None:
        self.setWindowTitle(f"{title} - {APP_NAME}")

    def _update_url_bar(self, url: QUrl) -> None:
        display_url = url.toDisplayString()
        self.url_bar.setText(display_url)
        if self._history and self._history[-1].url == url:
            return
        self._history.append(NavigationEntry(title=self.web_view.title(), url=url))
        if len(self._history) > 100:
            self._history = self._history[-100:]

    def _update_load_progress(self, progress: int) -> None:
        self.status_bar.showMessage(f"Loading… {progress}%")

    def _handle_load_finished(self, ok: bool) -> None:
        if ok:
            self.status_bar.showMessage("Ready", 2000)
        else:
            self.status_bar.showMessage("Failed to load page", 5000)
            QMessageBox.warning(self, APP_NAME, "The page failed to load. Check your connection or the URL.")

    def _focus_address_bar(self) -> None:
        self.url_bar.setFocus()
        self.url_bar.selectAll()

    @Slot(QUrl, QWebEnginePage.Feature)
    def _handle_feature_permission_request(
        self, security_origin: QUrl, feature: QWebEnginePage.Feature
    ) -> None:
        if feature != QWebEnginePage.Feature.Geolocation:
            self.web_view.page().setFeaturePermission(
                security_origin, feature, QWebEnginePage.PermissionPolicy.PermissionDeniedByUser
            )
            return

        if not self._is_secure_geolocation_origin(security_origin):
            self.status_bar.showMessage(
                "Blocked location request: insecure context", 5000
            )
            self.web_view.page().setFeaturePermission(
                security_origin, feature, QWebEnginePage.PermissionPolicy.PermissionDeniedByUser
            )
            return

        key = (security_origin.toString(), int(feature))
        if key in self._permission_store:
            self.web_view.page().setFeaturePermission(
                security_origin, feature, self._permission_store[key]
            )
            return

        allow, remember = self._prompt_geolocation_permission(security_origin)
        policy = (
            QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
            if allow
            else QWebEnginePage.PermissionPolicy.PermissionDeniedByUser
        )
        if remember:
            self._permission_store[key] = policy

        self.web_view.page().setFeaturePermission(security_origin, feature, policy)

    def _prompt_geolocation_permission(self, security_origin: QUrl) -> tuple[bool, bool]:
        origin_display = security_origin.toDisplayString()
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Location Access Requested")
        dialog.setIcon(QMessageBox.Question)
        dialog.setText(f"{origin_display} wants to know your location.")
        dialog.setInformativeText(
            "Sharing your location provides this site with your approximate position."
        )
        allow_button = dialog.addButton("Allow", QMessageBox.AcceptRole)
        deny_button = dialog.addButton("Deny", QMessageBox.RejectRole)
        remember_choice = QCheckBox("Remember this decision")
        dialog.setCheckBox(remember_choice)
        dialog.exec()

        allow = dialog.clickedButton() == allow_button
        remember = remember_choice.isChecked()

        # If the user closes the dialog without choosing, treat it as a denial.
        if dialog.clickedButton() not in (allow_button, deny_button):
            allow = False

        return allow, remember

    @staticmethod
    def _is_secure_geolocation_origin(url: QUrl) -> bool:
        if url.scheme() in {"https", "wss", "file"}:
            return True

        if url.scheme() == "http" and url.host() in {"localhost", "127.0.0.1", "::1"}:
            return True

        return False

    def show_about_dialog(self) -> None:
        QMessageBox.about(
            self,
            APP_NAME,
            """
            <h2>Cortex Browser</h2>
            <p>A lightweight demonstration browser built with Python and Qt.</p>
            <p>Features include navigation controls, smart address bar, and local file support.</p>
            <p>Built as a portfolio example of a fully custom, single-window browser.</p>
            """,
        )

    def show_history(self) -> None:
        if not self._history:
            QMessageBox.information(self, APP_NAME, "No browsing history yet.")
            return

        history_lines = [
            f"{index + 1}. {entry.title or entry.url.toDisplayString()}\n    {entry.url.toDisplayString()}"
            for index, entry in enumerate(reversed(self._history))
        ]
        QMessageBox.information(
            self,
            f"History ({len(self._history)} entries)",
            "\n\n".join(history_lines[:20]),
        )


def build_application(arguments: Optional[list[str]] = None) -> QApplication:
    """Create a QApplication instance."""

    app = QApplication(arguments or sys.argv)
    app.setApplicationName(APP_NAME)
    return app


def run() -> int:
    """Entry point used by `python -m cortex_browser.app`."""

    app = build_application()
    window = BrowserWindow()
    window.show()
    return app.exec()


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
