"""Capture screenshots of the built site in WebKit at phone, tablet and desktop sizes.

Runs inside the Playwright container started by `scripts/screenshots`; it serves `dist/` itself.
"""

import functools
import http.server
import os
import sys
import threading

from playwright.sync_api import sync_playwright

DIST = "/site"
OUT = "/out"
PAGES = {
    "home": "/",
    "chapter": "/ownership-system/ownership-basics/",
}
VIEWPORTS = {
    "phone": "iPhone 15",
    "ipad-portrait": "iPad Pro 11",
    "ipad-landscape": "iPad Pro 11 landscape",
    "desktop": None,
}


def log(message):
    print(message, file=sys.stderr, flush=True)


def serve():
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(QuietHandler, directory=DIST)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_address[1]}"


def check_sidebar_toggle(p, browser, base):
    """The toggle hides and shows the docked sidebar, and the choice survives navigation."""
    options = dict(p.devices["iPad Pro 11 landscape"])
    options.pop("default_browser_type", None)
    context = browser.new_context(**options)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(base + PAGES["chapter"])
    sidebar = page.locator("#starlight__sidebar")
    toggle = page.locator("sidebar-toggle button")
    assert not sidebar.is_visible(), "sidebar should start hidden on a touch device"
    toggle.click()
    assert sidebar.is_visible(), "toggle should show the sidebar"
    assert toggle.get_attribute("aria-expanded") == "true"
    sidebar.locator("li:has(> a[aria-current='page']) + li > a").click()
    page.wait_for_load_state()
    assert page.url != base + PAGES["chapter"], "sidebar link should navigate"
    assert sidebar.is_visible(), "shown sidebar should stay shown after navigation"
    toggle.click()
    page.reload()
    assert not sidebar.is_visible(), "hidden sidebar should stay hidden after reload"
    assert not errors, errors
    context.close()
    log("sidebar toggle check passed")


def main():
    only = set(sys.argv[1:])
    base = serve()
    with sync_playwright() as p:
        browser = p.webkit.launch()
        check_sidebar_toggle(p, browser, base)
        for name, device in VIEWPORTS.items():
            if only and name not in only:
                continue
            options = dict(p.devices[device]) if device else {"viewport": {"width": 1440, "height": 900}}
            options.pop("default_browser_type", None)
            for scheme in ("light", "dark"):
                context = browser.new_context(color_scheme=scheme, **options)
                page = context.new_page()
                for page_name, path in PAGES.items():
                    stem = f"{name}-{scheme}-{page_name}"
                    log(f"capture {stem}")
                    page.goto(base + path, wait_until="networkidle")
                    page.screenshot(path=os.path.join(OUT, stem + ".png"))
                    toggle = page.locator("sidebar-toggle button")
                    if page_name == "chapter" and toggle.is_visible():
                        state = "document.documentElement.hasAttribute('data-sidebar-collapsed')"
                        before = page.evaluate(state)
                        toggle.click()
                        page.wait_for_function(f"{state} !== {str(before).lower()}")
                        page.screenshot(path=os.path.join(OUT, stem + "-toggled.png"))
                        toggle.click()
                    if page_name == "chapter" and name == "phone":
                        page.locator("button[popovertarget='starlight__sidebar']").click()
                        page.wait_for_selector("#starlight__sidebar:popover-open")
                        page.screenshot(path=os.path.join(OUT, stem + "-menu.png"))
                context.close()
        browser.close()
    log("done")


if __name__ == "__main__":
    main()
