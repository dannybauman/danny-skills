# HtmlService CSP gotchas

Apps Script's `HtmlService` runs your HTML in a sandboxed iframe with a strict CSP. Most existing static HTML tools will work, but a few patterns need adaptation. Read this when porting an existing HTML tool to serve via Apps Script.

## Set sandbox mode to IFRAME

Default mode is more restrictive. Set explicitly to `IFRAME` for the most-permissive (still safe) sandbox:

```javascript
function doGet() {
  return HtmlService
    .createTemplateFromFile('Index')
    .evaluate()
    .setSandboxMode(HtmlService.SandboxMode.IFRAME)
    .setTitle('Your Tool Name');
}
```

Without `IFRAME` mode, external resources (Google Fonts, CDN scripts) load silently fail. With `IFRAME`, most things just work.

## What works

- `<script>` tags with inline JavaScript (the main rendering logic)
- `<style>` tags with CSS
- External fonts via `<link rel="stylesheet" href="https://fonts.googleapis.com/...">` — works under IFRAME mode
- `fetch()` to same-origin (Apps Script's own endpoints)
- `localStorage` and `sessionStorage`
- Event listeners, DOM manipulation, modern JS (ES6+)
- Emoji and Unicode characters (no escaping needed)

## What doesn't work (or needs adaptation)

- **External CDN scripts** (jQuery, Chart.js, Mapbox, etc.) — blocked by default CSP even in IFRAME mode. Workaround: inline the library code, or use Apps Script's `google.script.run` to fetch via a server-side function and inline the result
- **`<script src="external">`** — same as above. Inline scripts work
- **Dynamic code-string evaluation** — blocked. Avoid patterns that evaluate strings as code at runtime
- **Top-level navigation** (`window.location = ...`) — broken because of the iframe sandbox. Use `window.top.location` if you must navigate the parent
- **Cookies** — limited; the iframe is sandboxed. Use Apps Script's `PropertiesService` for persistent state
- **Mixed content (HTTP from HTTPS page)** — blocked

## Inline external libraries when needed

Pattern for using a library that doesn't fit the CSP:

1. Fetch the library file once
2. Save its content as a string in `Code.gs` or include in `Index.html` between `<script>` tags
3. Include the library content inline at the top of the script section

For libraries like the ones DS commonly uses (vanilla JS rendering, no jQuery/React), this isn't usually needed.

## Two common gotchas in practice

1. **Fonts that look broken on first load:** the Google Fonts stylesheet loads but the font files themselves might fail. Set explicit fallback fonts in your CSS (`font-family: 'Fraunces', Georgia, serif;`) so the tool degrades gracefully.

2. **`console.log` doesn't show in the browser console** for the sandboxed iframe — it shows in Apps Script's "Executions" log instead. Use `Logger.log()` for server-side logging, regular `console.log` for client-side, and check both during debugging.

## Testing the sandbox

To verify your HTML works under HtmlService's sandbox:

1. Deploy a test version with the tool's HTML
2. Open in a fresh browser tab (not Apps Script preview — preview is more permissive than the deployed version)
3. Open browser dev tools, look for CSP violations in console
4. Look for silently-failed external resources in Network tab (red 200s, blocked requests)

The preview-vs-deployed gap catches people — what works in preview can break in deployment.
