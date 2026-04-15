#!/usr/bin/env python3
"""
KOMPAGNON Smoke-Test — Live-API-Check gegen den deployed Backend.

Verwendung:
    python kompagnon/backend/scripts/smoke_test.py
    python kompagnon/backend/scripts/smoke_test.py https://my-staging.onrender.com
    SMOKE_TEST_BASE=https://other.example python kompagnon/backend/scripts/smoke_test.py

Default-Host: https://claude-code-znq2.onrender.com

Was geprueft wird:
1. /api/ping        — Liveness (sehr schnell, kein DB-Roundtrip)
2. /api/health      — Lightweight Status
3. /api/health/full — Detaillierter Self-Check (DB, Migrations, Env-Vars)

Exit codes:
    0 — alle Checks ok ODER status=degraded (z.B. NETLIFY_API_TOKEN fehlt)
    1 — DB-Fehler, ein Endpunkt nicht erreichbar, oder JSON-Parse-Fehler
    2 — Aufruf-Fehler (z.B. ungueltige URL)

Output: Markdown-Report auf stdout — eignet sich zum Pasten in PRs / Issues.
"""
import json
import os
import sys
from urllib import request, error

DEFAULT_BASE = "https://claude-code-znq2.onrender.com"
TIMEOUT = 30  # Sekunden — Render-Free-Tier kann beim ersten Request kalt starten


def fetch(url: str) -> tuple[int, str]:
    """HTTP GET, gibt (status_code, body_text) zurueck. Wirft URLError bei Netzfehler."""
    req = request.Request(url, headers={"User-Agent": "kompagnon-smoke-test/1.0"})
    with request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")


def check_endpoint(base: str, path: str, expect_json: bool = True) -> dict:
    """Ruft `base + path` ab und gibt ein einheitliches Result-Dict zurueck."""
    url = base.rstrip("/") + path
    result = {
        "url":     url,
        "ok":      False,
        "status":  None,
        "elapsed": None,
        "body":    None,
        "error":   None,
    }
    import time
    start = time.monotonic()
    try:
        code, body = fetch(url)
        result["status"]  = code
        result["elapsed"] = round(time.monotonic() - start, 2)
        result["ok"]      = 200 <= code < 300
        if expect_json:
            try:
                result["body"] = json.loads(body)
            except json.JSONDecodeError:
                result["body"] = body[:300]
                result["error"] = "JSON parse failed"
                result["ok"] = False
        else:
            result["body"] = body[:300]
    except error.HTTPError as e:
        result["status"] = e.code
        result["elapsed"] = round(time.monotonic() - start, 2)
        result["error"] = f"HTTP {e.code}: {e.reason}"
    except error.URLError as e:
        result["elapsed"] = round(time.monotonic() - start, 2)
        result["error"] = f"network: {e.reason}"
    except Exception as e:
        result["elapsed"] = round(time.monotonic() - start, 2)
        result["error"] = f"unexpected: {str(e)[:200]}"
    return result


def render_markdown(base: str, results: list[dict]) -> str:
    """Baut den Markdown-Report aus allen Check-Results."""
    lines = []
    lines.append(f"# KOMPAGNON Smoke-Test")
    lines.append("")
    lines.append(f"**Backend:** `{base}`")
    lines.append("")
    lines.append("## Endpunkt-Checks")
    lines.append("")
    lines.append("| Endpunkt | Status | Zeit | Hinweis |")
    lines.append("|---|---|---|---|")
    for r in results:
        path = r["url"].replace(base.rstrip("/"), "")
        status_icon = "ok" if r["ok"] else "FAIL"
        status_code = r["status"] if r["status"] is not None else "—"
        elapsed = f"{r['elapsed']}s" if r["elapsed"] is not None else "—"
        hint = r["error"] or ""
        lines.append(f"| `{path}` | {status_icon} ({status_code}) | {elapsed} | {hint} |")
    lines.append("")

    # Detail aus /api/health/full extrahieren
    full = next((r for r in results if r["url"].endswith("/api/health/full")), None)
    if full and full["ok"] and isinstance(full["body"], dict):
        body = full["body"]
        lines.append(f"## Self-Check — Status: **{body.get('status', 'unknown')}**")
        lines.append("")
        lines.append("| Subsystem | OK | Detail |")
        lines.append("|---|---|---|")
        checks = body.get("checks", {}) or {}
        for name, c in checks.items():
            mark = "ok" if c.get("ok") else "FAIL"
            lines.append(f"| **{name}** | {mark} | {c.get('detail', '')} |")
        lines.append("")
        info = body.get("info", {}) or {}
        if info:
            lines.append("### Info")
            for k, v in info.items():
                lines.append(f"- **{k}:** `{v}`")
            lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    base = (
        argv[1] if len(argv) > 1
        else os.getenv("SMOKE_TEST_BASE")
        or DEFAULT_BASE
    )
    if not base.startswith(("http://", "https://")):
        print(f"Ungueltige Base-URL (muss mit http:// oder https:// beginnen): {base}", file=sys.stderr)
        return 2

    print(f"Smoke-Test gegen: {base}", file=sys.stderr)
    print("Pruefe /api/ping ...", file=sys.stderr)
    ping = check_endpoint(base, "/api/ping", expect_json=False)
    print("Pruefe /api/health ...", file=sys.stderr)
    health = check_endpoint(base, "/api/health")
    print("Pruefe /api/health/full ...", file=sys.stderr)
    full = check_endpoint(base, "/api/health/full")

    results = [ping, health, full]
    print(render_markdown(base, results))

    # Exit-Code-Logik
    if not all(r["ok"] for r in results):
        return 1

    # Bei ok-Status der Endpunkte ist der Self-Check-Subsystem-Status entscheidend:
    if isinstance(full["body"], dict):
        sub_status = full["body"].get("status", "")
        if sub_status == "error":
            return 1
        # "degraded" gibt Warning-Output, aber Exit 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
