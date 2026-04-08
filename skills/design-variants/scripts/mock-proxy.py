#!/usr/bin/env python3
"""
Simple reverse proxy that injects a mock-auth script into HTML pages.
Works for any web app — the injected script handles auth mocking client-side.

Usage:
  # Single proxy
  python3 mock-proxy.py --target 5200 --port 6200 --mock-script mock.js

  # Multiple proxies (one per variant)
  python3 mock-proxy.py --targets 5200,5201,5202,5203,5204,5205 --base-port 6200 --mock-script mock.js

The proxy is intentionally dumb — it only:
1. Forwards requests to the target
2. Injects <script src="/__mock__.js"> into HTML <head>
3. Serves the mock script at /__mock__.js

All mocking logic lives in the mock script file, making it easy to customize
per project without touching the proxy.
"""

import argparse
import json
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import URLError


def make_handler(target_port, mock_script_content):
    """Create a handler class bound to a specific target port and mock script."""

    class ProxyHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def do_GET(self):
            # Serve mock script
            if self.path == "/__mock__.js":
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript")
                body = mock_script_content.encode("utf-8")
                self.send_header("Content-Length", len(body))
                self.end_headers()
                self.wfile.write(body)
                return
            self._proxy()

        def do_POST(self):
            self._proxy()

        def do_PUT(self):
            self._proxy()

        def do_PATCH(self):
            self._proxy()

        def do_DELETE(self):
            self._proxy()

        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "*")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.end_headers()

        def _proxy(self):
            target_url = f"http://localhost:{target_port}{self.path}"
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length) if content_length > 0 else None

                req = Request(target_url, data=body, method=self.command)
                for key in ["Content-Type", "Accept", "Authorization", "apikey",
                            "X-Client-Info", "Prefer"]:
                    val = self.headers.get(key)
                    if val:
                        req.add_header(key, val)

                resp = urlopen(req, timeout=15)
                resp_body = resp.read()
                content_type = resp.headers.get("Content-Type", "")

                # Inject mock script tag into HTML
                if "text/html" in content_type:
                    html = resp_body.decode("utf-8", errors="replace")
                    inject = '<script src="/__mock__.js"></script>'
                    if "</head>" in html:
                        html = html.replace("</head>", f"{inject}</head>", 1)
                    elif "<body" in html:
                        html = html.replace("<body", f"{inject}<body", 1)
                    resp_body = html.encode("utf-8")

                self.send_response(resp.status)
                for key in ["Content-Type", "Cache-Control", "ETag"]:
                    val = resp.headers.get(key)
                    if val:
                        self.send_header(key, val)
                self.send_header("Content-Length", len(resp_body))
                self.end_headers()
                self.wfile.write(resp_body)

            except URLError as e:
                self.send_response(502)
                self.end_headers()
                self.wfile.write(f"Proxy error: {e}".encode())

    return ProxyHandler


def run_proxy(target_port, proxy_port, mock_script_content):
    handler = make_handler(target_port, mock_script_content)
    server = HTTPServer(("127.0.0.1", proxy_port), handler)
    print(f"  :{proxy_port} -> :{target_port}")
    server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description="HTML-injecting reverse proxy for design variant comparison")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--target", type=int, help="Single target port")
    group.add_argument("--targets", help="Comma-separated target ports (e.g. 5200,5201,5202)")
    parser.add_argument("--port", type=int, help="Proxy listen port (for --target)")
    parser.add_argument("--base-port", type=int, default=6200, help="Starting proxy port (for --targets)")
    parser.add_argument("--mock-script", required=True, help="Path to JS file to inject")
    args = parser.parse_args()

    if not os.path.exists(args.mock_script):
        print(f"Error: mock script not found: {args.mock_script}", file=sys.stderr)
        sys.exit(1)

    with open(args.mock_script) as f:
        mock_script_content = f.read()

    if args.target:
        port = args.port or (args.target + 1000)
        run_proxy(args.target, port, mock_script_content)
    else:
        targets = [int(p) for p in args.targets.split(",")]
        threads = []
        for i, target in enumerate(targets):
            proxy_port = args.base_port + i
            t = threading.Thread(target=run_proxy, args=(target, proxy_port, mock_script_content), daemon=True)
            t.start()
            threads.append(t)
        print(f"\n  {len(targets)} proxies running. Ctrl+C to stop.\n")
        try:
            for t in threads:
                t.join()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
