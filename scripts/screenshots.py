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


# WebKit keeps listing a view transition's finished animations, so only running ones count.
SETTLED = (
    "!document.documentElement.hasAttribute('data-sidebar-animating')"
    " && !document.getAnimations().some(a => a.playState === 'running')"
)


def check_sidebar_overlay(p, browser, base):
    """On a touch screen the toggle slides the sidebar over the content and anything else closes it."""
    options = dict(p.devices["iPad Pro 11 landscape"])
    options.pop("default_browser_type", None)
    context = browser.new_context(**options)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(base + PAGES["chapter"])
    sidebar = page.locator("#starlight__sidebar")
    toggle = page.locator("sidebar-toggle button")
    content = "document.querySelector('.main-pane').getBoundingClientRect().left"
    left = page.evaluate(content)
    assert not sidebar.is_visible(), "sidebar should start hidden on a touch device"
    for close in ("scrim", "escape", "toggle"):
        toggle.click()
        page.wait_for_function(SETTLED)
        assert sidebar.is_visible(), "toggle should show the sidebar"
        assert toggle.get_attribute("aria-expanded") == "true"
        assert page.evaluate(content) == left, "the overlay should not move the content"
        if close == "scrim":
            page.locator(".sidebar-scrim").click(position={"x": 900, "y": 300})
        elif close == "escape":
            page.keyboard.press("Escape")
        else:
            toggle.click()
        page.wait_for_function(SETTLED)
        assert not sidebar.is_visible(), f"{close} should hide the sidebar"
        assert toggle.get_attribute("aria-expanded") == "false"
    toggle.click()
    sidebar.locator("li:has(> a[aria-current='page']) + li > a").click()
    page.wait_for_load_state()
    assert page.url != base + PAGES["chapter"], "sidebar link should navigate"
    assert not sidebar.is_visible(), "the next page should start with the sidebar hidden"
    assert not errors, errors
    context.close()
    log("sidebar overlay check passed")


def check_sidebar_docked(browser, base):
    """With a pointer the toggle hides the docked sidebar, widening the content, and remembers that."""
    for reduced_motion in ("no-preference", "reduce"):
        context = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion=reduced_motion)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(base + PAGES["chapter"])
        sidebar = page.locator("#starlight__sidebar")
        toggle = page.locator("sidebar-toggle button")
        content = "document.querySelector('.main-pane').getBoundingClientRect().left"
        left = page.evaluate(content)
        assert sidebar.is_visible(), "sidebar should start shown in a wide window"
        toggle.click()
        page.wait_for_function(SETTLED)
        assert not sidebar.is_visible(), "toggle should hide the sidebar"
        assert page.evaluate(content) < left, "hiding the sidebar should widen the content"
        page.reload()
        assert not sidebar.is_visible(), "hidden sidebar should stay hidden after reload"
        toggle.click()
        page.wait_for_function(SETTLED)
        assert sidebar.is_visible() and page.evaluate(content) == left
        assert not errors, errors
        context.close()
    log("docked sidebar check passed")


def check_view_transitions(browser, base):
    """Sidebar navigation runs a cross-document view transition, which keeps Safari from flashing."""
    for reduced_motion in ("no-preference", "reduce"):
        context = browser.new_context(
            viewport={"width": 1440, "height": 900}, reduced_motion=reduced_motion
        )
        context.add_init_script(
            "addEventListener('pagereveal', e => { window.revealedWithTransition = !!e.viewTransition; });"
        )
        page = context.new_page()
        page.goto(base + PAGES["chapter"])
        page.locator("#starlight__sidebar li:has(> a[aria-current='page']) + li > a").click()
        page.wait_for_function("window.revealedWithTransition !== undefined")
        assert page.evaluate("window.revealedWithTransition"), f"no view transition ({reduced_motion})"
        context.close()
    log("view transition check passed")


def check_menus(p, browser, base):
    """Menus with scripted animations still end up open or closed as Starlight expects."""
    options = dict(p.devices["iPhone 15"])
    options.pop("default_browser_type", None)
    context = browser.new_context(**options)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(base + PAGES["chapter"])

    toc = "#starlight__mobile-toc"
    page.click(f"{toc} summary")
    page.wait_for_function(f"document.querySelector('{toc}').open")
    page.click(f"{toc} summary")
    page.wait_for_function(f"!document.querySelector('{toc}').open")
    page.click(f"{toc} summary")
    page.locator(f"{toc} .dropdown a").nth(1).click()
    page.wait_for_function(f"!document.querySelector('{toc}').open")

    menu = "#starlight__sidebar"
    button = "button[popovertarget='starlight__sidebar']"
    page.click(button)
    page.wait_for_function(f"document.querySelector('{menu}').matches(':popover-open')")
    page.click(button)
    page.wait_for_function(f"!document.querySelector('{menu}').matches(':popover-open')")
    assert not page.locator(menu).is_visible(), "menu should be hidden after closing"

    page.click("button[data-open-modal]")
    page.wait_for_function("document.querySelector('site-search dialog').open")
    page.keyboard.press("Escape")
    # Starlight releases the page's scroll lock from the dialog's `close` event.
    page.wait_for_function(
        "!document.querySelector('site-search dialog').open"
        " && !document.body.hasAttribute('data-search-modal-open')"
    )
    assert not errors, errors
    context.close()
    log("menu check passed")


def main():
    only = set(sys.argv[1:])
    base = serve()
    with sync_playwright() as p:
        browser = p.webkit.launch()
        check_sidebar_overlay(p, browser, base)
        check_sidebar_docked(browser, base)
        check_view_transitions(browser, base)
        check_menus(p, browser, base)
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
                        toggle.click()
                        page.wait_for_function(SETTLED)
                        page.screenshot(path=os.path.join(OUT, stem + "-toggled.png"))
                        toggle.click()
                        page.wait_for_function(SETTLED)
                    if page_name == "chapter" and name == "phone":
                        page.locator("button[popovertarget='starlight__sidebar']").click()
                        page.wait_for_selector("#starlight__sidebar:popover-open")
                        page.screenshot(path=os.path.join(OUT, stem + "-menu.png"))
                context.close()
        browser.close()
    log("done")


if __name__ == "__main__":
    main()
