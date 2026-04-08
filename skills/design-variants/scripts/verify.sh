#!/usr/bin/env bash
# Verify each variant server actually renders UI content (not just HTTP 200).
# Usage: verify.sh <variants_json>
# Requires: python3 with playwright installed
set -euo pipefail

VARIANTS_JSON="$1"

if ! python3 -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
    echo "  WARN: Playwright not available, falling back to HTTP-only checks" >&2
    # Fallback: just check HTTP status
    while IFS= read -r entry; do
        name=$(echo "$entry" | jq -r '.name')
        url=$(echo "$entry" | jq -r '.url')
        status=$(curl -s -o /dev/null -w "%{http_code}" "$url/" 2>/dev/null || echo "000")
        if [[ "$status" == "200" ]]; then
            echo "  $name: HTTP $status (content not verified)" >&2
        else
            echo "  $name: FAILED (HTTP $status)" >&2
        fi
    done < <(echo "$VARIANTS_JSON" | jq -c '.[]')
    exit 0
fi

# Use Playwright for real content verification
python3 -c "
import json, sys
from playwright.sync_api import sync_playwright

variants = json.loads('''$VARIANTS_JSON''')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for v in variants:
        name = v['name']
        url = v['url']
        try:
            context = browser.new_context(viewport={'width': 1280, 'height': 720})
            page = context.new_page()
            page.goto(url + '/login', wait_until='domcontentloaded', timeout=8000)
            page.wait_for_timeout(2000)

            # Check for real content: buttons, inputs, headings
            has_content = page.evaluate('''() => {
                const buttons = document.querySelectorAll('button');
                const inputs = document.querySelectorAll('input');
                const headings = document.querySelectorAll('h1, h2, h3');
                const bodyText = document.body.innerText.trim();
                return {
                    buttons: buttons.length,
                    inputs: inputs.length,
                    headings: headings.length,
                    textLength: bodyText.length,
                    hasError: bodyText.includes('Something went wrong') || bodyText.includes('Cannot read') || bodyText.includes('Error'),
                    title: document.title
                };
            }''')

            if has_content['hasError']:
                print(f'  {name}: BROKEN (renders error page)', file=sys.stderr)
            elif has_content['buttons'] == 0 and has_content['inputs'] == 0 and has_content['textLength'] < 20:
                print(f'  {name}: BLANK (no interactive elements)', file=sys.stderr)
            else:
                print(f'  {name}: OK ({has_content[\"buttons\"]} buttons, {has_content[\"inputs\"]} inputs)', file=sys.stderr)

            context.close()
        except Exception as e:
            print(f'  {name}: UNREACHABLE ({str(e)[:60]})', file=sys.stderr)

    browser.close()
" 2>&1
