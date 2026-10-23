#!/usr/bin/env python3
"""OKX read-only account reader (user-approved 2026-10-23).

Reads the user's OKX account via the official REST API using a READ-ONLY
API key (key + secret + passphrase, HMAC-SHA256 signed requests).
This script implements GET read endpoints ONLY. It has no order-placement,
transfer, or withdrawal code paths and never will.

Credentials live in ./.okx_readonly.json (file mode 0600, same directory
as this script). Never print, log, or copy the credential values anywhere.
"""
import base64
import hashlib
import hmac
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

BASE = "https://www.okx.com"
CREDS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".okx_readonly.json")


def load_creds():
    if not os.path.exists(CREDS_PATH):
        sys.exit("ERROR: credentials file not installed yet (.okx_readonly.json missing)")
    mode = oct(os.stat(CREDS_PATH).st_mode)[-3:]
    if mode != "600":
        sys.exit(f"ERROR: credentials file permissions are {mode}, expected 600 — refusing to use")
    with open(CREDS_PATH, encoding="utf-8") as f:
        c = json.load(f)
    for k in ("api_key", "secret", "passphrase"):
        if not c.get(k):
            sys.exit(f"ERROR: credentials file missing field: {k}")
    return c


def timestamp() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def sign(secret: str, ts: str, method: str, path: str, body: str = "") -> str:
    prehash = f"{ts}{method}{path}{body}"
    digest = hmac.new(secret.encode(), prehash.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise RuntimeError("redirect refused")


def get(path: str, auth: bool = True) -> dict:
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    if auth:
        creds = load_creds()
        ts = timestamp()
        headers.update({
            "OK-ACCESS-KEY": creds["api_key"],
            "OK-ACCESS-SIGN": sign(creds["secret"], ts, "GET", path),
            "OK-ACCESS-TIMESTAMP": ts,
            "OK-ACCESS-PASSPHRASE": creds["passphrase"],
        })
    req = urllib.request.Request(BASE + path, headers=headers, method="GET")
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        sys.exit(f"HTTP {e.code}: {body}")


def cmd_time():
    out = get("/api/v5/public/time", auth=False)
    print(json.dumps(out, ensure_ascii=False))


def cmd_balance():
    out = get("/api/v5/account/balance")
    if out.get("code") != "0":
        sys.exit(f"OKX error: {out.get('code')} {out.get('msg')}")
    for acct in out.get("data", []):
        print(f"totalEq (USD): {acct.get('totalEq')}")
        for d in acct.get("details", []):
            if float(d.get("eq") or 0) != 0:
                print(f"  {d.get('ccy')}: eq={d.get('eq')} avail={d.get('availBal')} frozen={d.get('frozenBal')}")


def cmd_positions():
    out = get("/api/v5/account/positions")
    if out.get("code") != "0":
        sys.exit(f"OKX error: {out.get('code')} {out.get('msg')}")
    rows = [p for p in out.get("data", []) if float(p.get("pos") or 0) != 0]
    if not rows:
        print("no open positions")
    for p in rows:
        print(f"{p.get('instId')} {p.get('posSide')} pos={p.get('pos')} avgPx={p.get('avgPx')} "
              f"lever={p.get('lever')} mgnMode={p.get('mgnMode')} upl={p.get('upl')} uplRatio={p.get('uplRatio')} "
              f"liqPx={p.get('liqPx')} markPx={p.get('markPx')}")


def cmd_fills():
    out = get("/api/v5/trade/fills?limit=20")
    if out.get("code") != "0":
        sys.exit(f"OKX error: {out.get('code')} {out.get('msg')}")
    for f in out.get("data", []):
        ts = datetime.fromtimestamp(int(f.get("ts", "0")) / 1000, timezone.utc).isoformat()
        print(f"{ts} {f.get('instId')} {f.get('side')} px={f.get('fillPx')} sz={f.get('fillSz')} "
              f"fee={f.get('fee')} {f.get('feeCcy')} pnl={f.get('fillPnl')}")


def cmd_algo():
    rows = []
    for t in ("conditional", "oco", "trigger", "move_order_stop"):
        out = get(f"/api/v5/trade/orders-algo-pending?ordType={t}")
        if out.get("code") != "0":
            sys.exit(f"OKX error: {out.get('code')} {out.get('msg')}")
        rows.extend(out.get("data", []))
    if not rows:
        print("no pending conditional (stop/take-profit) orders")
    for o in rows:
        print(f"{o.get('instId')} {o.get('side')} sz={o.get('sz')} slTriggerPx={o.get('slTriggerPx')} "
              f"tpTriggerPx={o.get('tpTriggerPx')} ordType={o.get('ordType')} state={o.get('state')}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "balance"
    {"time": cmd_time, "balance": cmd_balance, "positions": cmd_positions, "fills": cmd_fills,
     "algo": cmd_algo}.get(
        cmd, lambda: sys.exit(f"unknown command: {cmd} (use time|balance|positions|fills|algo)"))()
