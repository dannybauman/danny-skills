#!/usr/bin/env python3
"""Take screenshots of public URLs using Playwright."""

import argparse
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

TIMEOUT_MS = 30_000
VIEWPORT = {"width": 1920, "height": 1080}


def screenshot_github(page, repo_url, output_dir):
    """Take a full-page screenshot of a GitHub repo."""
    try:
        page.set_viewport_size(VIEWPORT)
        page.goto(repo_url, wait_until="networkidle", timeout=TIMEOUT_MS)
        path = output_dir / "github.png"
        page.screenshot(path=str(path), full_page=True)
        print(f"Saved GitHub screenshot: {path}")
        return path
    except Exception as e:
        print(f"Warning: GitHub screenshot failed: {e}")
        return None


def screenshot_app(page, app_url, output_dir):
    """Take a screenshot of a live app."""
    try:
        page.set_viewport_size(VIEWPORT)
        page.goto(app_url, wait_until="networkidle", timeout=TIMEOUT_MS)
        time.sleep(2)  # extra wait for JS rendering
        path = output_dir / "app.png"
        page.screenshot(path=str(path))
        print(f"Saved app screenshot: {path}")
        return path
    except Exception as e:
        print(f"Warning: App screenshot failed: {e}")
        return None


def take_screenshots(repo_url=None, app_url=None, output_dir=None):
    """Take screenshots of a GitHub repo and/or a live app.

    Returns a dict of {"github": path_or_none, "app": path_or_none}.
    """
    if not HAS_PLAYWRIGHT:
        print("Playwright is not installed. Skipping screenshots.")
        return {"github": None, "app": None}

    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "screenshots"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {"github": None, "app": None}
    browser = None

    try:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()

        if repo_url:
            results["github"] = screenshot_github(page, repo_url, output_dir)

        if app_url:
            results["app"] = screenshot_app(page, app_url, output_dir)
    except Exception as e:
        print(f"Warning: Browser session failed: {e}")
    finally:
        if browser:
            browser.close()
        try:
            pw.stop()
        except Exception:
            pass

    return results


def main():
    parser = argparse.ArgumentParser(description="Take screenshots of public URLs")
    parser.add_argument("--repo-url", help="GitHub repository URL")
    parser.add_argument("--app-url", help="Live application URL")
    parser.add_argument("--output-dir", help="Directory to save screenshots")
    args = parser.parse_args()

    if not args.repo_url and not args.app_url:
        parser.error("Provide at least one of --repo-url or --app-url")

    results = take_screenshots(
        repo_url=args.repo_url,
        app_url=args.app_url,
        output_dir=args.output_dir,
    )
    print(f"Results: {results}")


if __name__ == "__main__":
    main()
