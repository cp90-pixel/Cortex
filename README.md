# Cortex Browser

Cortex is a minimal yet fully functional desktop web browser implemented in
Python using Qt. It features a navigation toolbar, URL/search bar, local file
support, and a polished landing page.

## Features

- **Modern UI** powered by Qt WebEngine with back, forward, reload, stop, and
  home controls.
- **Smart address bar** that understands both URLs and search queries (DuckDuckGo
  by default).
- **Local file browsing** for opening HTML files stored on your computer.
- **Status feedback** with loading progress and error reporting.
- **Customizable home page** bundled with the project.

## Getting started

1. Ensure Python 3.11+ is installed.
2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Launch the browser:

   ```bash
   python -m cortex_browser.app
   ```

The application will start on the Cortex home page. Enter a URL or a search
term to begin browsing.

## Development

- Format checking is handled by `python -m compileall cortex_browser`.
- Feel free to customize `cortex_browser/resources/home.html` to adjust the
  landing experience.
