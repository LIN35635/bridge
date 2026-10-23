#!/usr/bin/env python3
"""OKX position watcher + system-rule auditor (user-approved 2026-10-23).

Polls the user's OKX account through the read-only helper (okx_read.py),
diffs positions against the last snapshot, and audits open positions
against the user's final trading system (~/workspace/okx-trading/SYSTEM.md):

  - single-trade margin ~10% of total equity (flag if > 11%)
  - leverage <= 5x
  - hard stop: an exchange-side conditional SL order should exist;
    for a fresh position its trigger should sit ~2% from entry
    (flag if missing entirely, or if distance > 3%)
  - +2% rule: if a position's mark gain peaked >= +2% and later falls
    back below entry with no SL order at/above entry, flag it
    (profitable trade must never become a loser)
  - max hold 1 month (flag beyond 30 days)

Output: one JSON object on stdout: {"events": [ {type, detail, ...} ]}
Empty events = nothing to report. Infrastructure failures (no creds,
API errors) produce {"events": [], "infra_error": "..."} so the caller
stays silent — never wake the user for our own plumbing problems.

State: ./.okx_watch_state.json next to this script (positions snapshot,
first-seen timestamps, peak gains). Not a credential file.
"""
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import okx_read  # noqa: E402

STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".okx_watch_state.json")


def f(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    return {"positions": {}}


def save_state(state):
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE_PATH)


def main():
    try:
        bal = okx_read.get("/api/v5/account/balance")
        pos = okx_read.get("/api/v5/account/positions")
        algo = {"data": []}
        for t in ("conditional", "oco"):
            part = okx_read.get(f"/api/v5/trade/orders-algo-pending?ordType={t}")
            if part.get("code") != "0":
                raise RuntimeError(f"algo {t} code {part.get('code')}")
            algo["data"].extend(part.get("data", []))
    except SystemExit as e:
        print(json.dumps({"events": [], "infra_error": str(e)}))
        return
    except Exception as e:  # network etc. — stay silent
        print(json.dumps({"events": [], "infra_error": f"{type(e).__name__}: {e}"}))
        return
    if bal.get("code") != "0" or pos.get("code") != "0":
        print(json.dumps({"events": [], "infra_error": f"okx codes bal={bal.get('code')} pos={pos.get('code')}"}))
        return

    total_eq = f(bal["data"][0].get("totalEq")) if bal.get("data") else 0.0
    algo_by_inst = {}
    for o in algo.get("data", []):
        algo_by_inst.setdefault(o.get("instId"), []).append(o)

    now = datetime.now(timezone.utc).isoformat()
    state = load_state()
    old = state.get("positions", {})
    new = {}
    events = []

    for p in pos.get("data", []):
        if f(p.get("pos")) == 0:
            continue
        key = f"{p.get('instId')}|{p.get('posSide')}"
        avg = f(p.get("avgPx"))
        mark = f(p.get("markPx"))
        gain = (mark - avg) / avg if avg else 0.0
        if p.get("posSide") == "short":
            gain = -gain
        prev = old.get(key)
        peak = max(prev.get("peak_gain", gain), gain) if prev else gain
        new[key] = {
            "instId": p.get("instId"), "posSide": p.get("posSide"),
            "pos": p.get("pos"), "avgPx": avg, "lever": f(p.get("lever")),
            "mgnMode": p.get("mgnMode"), "margin": f(p.get("margin")),
            "upl": f(p.get("upl")), "markPx": mark,
            "first_seen": prev.get("first_seen", now) if prev else now,
            "peak_gain": peak,
        }

        if prev is None:
            events.append({"type": "NEW_POSITION", "key": key, **new[key]})
        elif prev.get("pos") != p.get("pos"):
            events.append({"type": "SIZE_CHANGED", "key": key,
                           "old_pos": prev.get("pos"), **new[key]})

        # --- rule audit (only on new/changed positions, plus the +2% and hold checks) ---
        audit = prev is None or prev.get("pos") != p.get("pos")
        margin_share = (f(p.get("margin")) / total_eq) if total_eq else 0.0
        if audit and total_eq and margin_share > 0.11:
            events.append({"type": "RULE_MARGIN", "key": key,
                           "margin_share": round(margin_share, 4), "totalEq": total_eq})
        if audit and f(p.get("lever")) > 5:
            events.append({"type": "RULE_LEVER", "key": key, "lever": f(p.get("lever"))})
        orders = algo_by_inst.get(p.get("instId"), [])
        sl_prices = [f(o.get("slTriggerPx")) for o in orders if f(o.get("slTriggerPx")) > 0]
        if audit:
            if not sl_prices:
                events.append({"type": "RULE_NO_EXCHANGE_SL", "key": key, "avgPx": avg})
            else:
                for sl in sl_prices:
                    dist = abs(avg - sl) / avg if avg else 0.0
                    if dist > 0.03:
                        events.append({"type": "RULE_SL_FAR", "key": key,
                                       "avgPx": avg, "slTriggerPx": sl, "dist": round(dist, 4)})
        # +2% -> back below entry, without a protective SL at/above entry
        if peak >= 0.02 and gain < 0:
            protected = False
            for sl in sl_prices:
                if p.get("posSide") == "long" and sl >= avg:
                    protected = True
                if p.get("posSide") == "short" and 0 < sl <= avg:
                    protected = True
            if not protected and not new[key].get("flagged_2pct"):
                events.append({"type": "RULE_2PCT_GIVEBACK", "key": key,
                               "peak_gain": round(peak, 4), "gain_now": round(gain, 4)})
                new[key]["flagged_2pct"] = True
        if prev and prev.get("flagged_2pct"):
            new[key]["flagged_2pct"] = True
        # hold > 30 days
        first_seen = new[key]["first_seen"]
        try:
            age_days = (datetime.now(timezone.utc) - datetime.fromisoformat(first_seen)).days
        except ValueError:
            age_days = 0
        if age_days > 30 and not new[key].get("flagged_hold"):
            events.append({"type": "RULE_HOLD_30D", "key": key, "age_days": age_days})
            new[key]["flagged_hold"] = True
        if prev and prev.get("flagged_hold"):
            new[key]["flagged_hold"] = True

    for key, prev in old.items():
        if key not in new:
            events.append({"type": "CLOSED", "key": key,
                           "avgPx": prev.get("avgPx"), "last_upl": prev.get("upl"),
                           "first_seen": prev.get("first_seen")})

    state["positions"] = new
    state["last_check"] = now
    state["totalEq"] = total_eq
    save_state(state)
    print(json.dumps({"events": events}, ensure_ascii=False))


if __name__ == "__main__":
    main()
