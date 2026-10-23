#!/usr/bin/env python3
"""
BTC 突破哨兵（按用户 2026-10-17 定稿交易系统）
- 只看 K 线：日线前 20 根已收盘 K 线的最高点=阻力、最低点=支撑
- 价格上穿阻力 → 微信提醒「突破」；下穿支撑 → 微信提醒「跌破」
- 周线只做方向标注（多头/空头/震荡），不做过滤
- 同一关键位同一天只报一次；只报信，永不下单；只用公共行情，无需 API 密钥
"""

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta

sys.path.insert(0, '/usr/local/lib/python3.12/dist-packages')

WORK_DIR = os.path.expanduser("~/workspace/btc-sentinel")
CREDS_FILE = os.path.expanduser("~/workspace/wechat-ilink/creds.json")
STATE_FILE = os.path.join(WORK_DIR, "state.json")
LOG_FILE = os.path.join(WORK_DIR, "sentinel.log")
ALERTS_FILE = os.path.join(WORK_DIR, "alerts.jsonl")
HEARTBEAT_FILE = os.path.join(WORK_DIR, "heartbeat.txt")

SYMBOL = "BTC/USDT:USDT"
LOOKBACK_DAYS = 20
POLL_SECONDS = 60
BRIEF_INTERVAL = 1800  # 行情播报间隔：30 分钟
BRIEF_HOUR_START = 7   # 播报时段（CST）：工作日 07:00–次日 01:00（本人 2026-10-20 晚调整）
BRIEF_HOUR_END = 1     # 次日凌晨 1 点（算前一工作日的晚上）
# 当前持仓：无（2026-10-20 回归第一单已于 2026-10-24 06:53:38 由交易所 OCO 止损平仓）
POSITION = None
CST = timezone(timedelta(hours=8))


def log(msg):
    line = f"[{datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
    except Exception as e:
        log(f"保存状态失败: {e}")


def _okx_get(path, params):
    import requests
    r = requests.get("https://www.okx.com" + path, params=params, timeout=20,
                     headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.json()["data"]


def _candles(bar, limit):
    """返回已收盘 K 线（旧→新）：每条为 dict(o,h,l,c)。"""
    data = _okx_get("/api/v5/market/candles",
                    {"instId": "BTC-USDT-SWAP", "bar": bar, "limit": str(limit)})
    rows = [{"o": float(x[1]), "h": float(x[2]), "l": float(x[3]), "c": float(x[4])}
            for x in data if x[8] == "1"]
    rows.reverse()
    return rows


def compute_levels():
    """返回 (阻力, 支撑)：最近 LOOKBACK_DAYS 根已收盘日线的高/低点。"""
    recent = _candles("1D", LOOKBACK_DAYS + 3)[-LOOKBACK_DAYS:]
    resistance = max(c["h"] for c in recent)
    support = min(c["l"] for c in recent)
    return resistance, support


def weekly_trend():
    """周线方向标注：看最近 3 根已收盘周线的收盘与高点走向。"""
    closed = _candles("1W", 6)
    if len(closed) < 3:
        return "未知"
    last3 = closed[-3:]
    closes = [c["c"] for c in last3]
    highs = [c["h"] for c in last3]
    if closes[-1] > closes[0] and highs[-1] >= highs[0]:
        return "多头"
    if closes[-1] < closes[0] and highs[-1] <= highs[0]:
        return "空头"
    return "震荡"


def fetch_price():
    data = _okx_get("/api/v5/market/ticker", {"instId": "BTC-USDT-SWAP"})
    return float(data[0]["last"])


def detect_cross(prev_price, price, resistance, support):
    """返回 'breakout' / 'breakdown' / None。纯函数，可回放测试。"""
    if prev_price is None:
        return None
    if prev_price <= resistance and price > resistance:
        return "breakout"
    if prev_price >= support and price < support:
        return "breakdown"
    return None


def send_wechat(text):
    from weixin_ilink import WeixinBot
    ctx_file = os.path.expanduser("~/workspace/wechat-ilink/context.json")
    with open(ctx_file, "r", encoding="utf-8") as f:
        ctx = json.load(f)
    bot = WeixinBot(credentials_file=CREDS_FILE)
    bot.send_text(ctx["userId"], text, context_token=ctx["context_token"])


def format_alert(kind, price, level, trend):
    now = datetime.now(CST).strftime("%H:%M")
    if kind == "breakout":
        return (
            f"🚨 BTC 突破提醒\n"
            f"现价 {price:,.0f}，已上穿前{LOOKBACK_DAYS}日阻力 {level:,.0f}\n"
            f"周线方向：{trend}\n"
            f"时间 {now}\n"
            f"哨兵只报信，做不做你定。"
        )
    return (
        f"📉 BTC 跌破提醒\n"
        f"现价 {price:,.0f}，已下穿前{LOOKBACK_DAYS}日支撑 {level:,.0f}\n"
        f"周线方向：{trend}\n"
        f"时间 {now}\n"
        f"哨兵只报信，做不做你定。"
    )


def format_stop_alert(price, stop):
    now = datetime.now(CST).strftime("%H:%M")
    return (
        f"🚨 止损线提醒\n"
        f"现价 {price:,.0f}，已打到你多单的硬止损 {stop:,}\n"
        f"时间 {now}\n"
        f"按你的规则：硬止损到了就离场，别加仓别硬扛。"
    )


def fetch_day_open():
    data = _okx_get("/api/v5/market/candles",
                    {"instId": "BTC-USDT-SWAP", "bar": "1D", "limit": "1"})
    return float(data[0][1])


def compose_brief(price, resistance, support, trend):
    now = datetime.now(CST)
    try:
        day_open = fetch_day_open()
        day_chg = (price - day_open) / day_open * 100
        chg_txt = f"今日 {day_chg:+.1f}%"
    except Exception:
        chg_txt = "今日涨跌暂缺"
    up = (resistance - price) / price * 100
    dn = (price - support) / price * 100
    lines = [
        "📊 BTC 行情播报",
        f"现价 {price:,.0f}（{chg_txt}）",
        f"阻力 {resistance:,.0f}（+{up:.1f}%）｜支撑 {support:,.0f}（-{dn:.1f}%）",
        f"周线方向：{trend}",
    ]
    if POSITION:
        pnl = (price - POSITION["entry"]) / POSITION["entry"] * 100
        to_stop = (price - POSITION["stop"]) / price * 100
        lines.append(
            f"你的多单 {POSITION['entry']:,}：价格浮动 {pnl:+.1f}%，距止损 {POSITION['stop']:,} 还有 {to_stop:.1f}%"
        )
    lines.append(f"{now.strftime('%H:%M')} · 哨兵播报（每30分钟）")
    return "\n".join(lines)


def main():
    state = load_state()
    resistance, support = compute_levels()
    day_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    state.update({"resistance": resistance, "support": support, "day": day_key})
    save_state(state)
    log(f"哨兵启动：阻力 {resistance:,.0f} / 支撑 {support:,.0f}")

    prev_price = None
    while True:
        try:
            price = fetch_price()
            # 跨天则重算关键位并重置当日去重
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if today != state.get("day"):
                resistance, support = compute_levels()
                state.update({"resistance": resistance, "support": support, "day": today})
                save_state(state)
                log(f"新的一天，重算关键位：阻力 {resistance:,.0f} / 支撑 {support:,.0f}")
            kind = detect_cross(prev_price, price, resistance, support)
            if kind:
                dedupe_key = f"alerted_{today}_{kind}"
                if not state.get(dedupe_key) and not state.get("pending_alert"):
                    trend = weekly_trend()
                    level = resistance if kind == "breakout" else support
                    state["pending_alert"] = {
                        "date": today, "kind": kind, "price": price,
                        "level": level, "trend": trend,
                    }
                    save_state(state)
            # 持仓硬止损：价格打到止损位就排队发提醒（同天只发一次）
            if POSITION and price <= POSITION["stop"]:
                dedupe_key = f"alerted_{today}_stop"
                if not state.get(dedupe_key) and not state.get("pending_alert"):
                    state["pending_alert"] = {
                        "date": today, "kind": "stop", "price": price,
                        "level": POSITION["stop"], "trend": "",
                    }
                    save_state(state)
                    log(f"价格 {price:,.0f} 打到止损 {POSITION['stop']:,}，已排队提醒")
            # 有待发报警就尝试发送；成功才记账并去重，失败下分钟重试
            pending = state.get("pending_alert")
            if pending and pending.get("date") == today:
                if pending["kind"] == "stop":
                    text = format_stop_alert(pending["price"], pending["level"])
                else:
                    text = format_alert(pending["kind"], pending["price"],
                                        pending["level"], pending["trend"])
                try:
                    send_wechat(text)
                    log(f"已发送提醒：{pending['kind']} 现价 {pending['price']:,.0f}")
                    with open(ALERTS_FILE, "a", encoding="utf-8") as f:
                        f.write(json.dumps({
                            "time": datetime.now(CST).isoformat(),
                            "kind": pending["kind"], "price": pending["price"],
                            "level": pending["level"], "trend": pending["trend"],
                        }, ensure_ascii=False) + "\n")
                    state[f"alerted_{today}_{pending['kind']}"] = True
                    state["pending_alert"] = None
                    save_state(state)
                except Exception as e:
                    log(f"微信发送失败（下分钟重试）：{e}")
            prev_price = price
            # 行情播报：每 BRIEF_INTERVAL 秒、仅在播报时段内发送；失败就跳过本轮（旧行情没价值）
            now_cst = datetime.now(CST)
            last_brief = float(state.get("brief_last", 0))
            wd = now_cst.weekday()
            in_window = ((BRIEF_HOUR_START <= now_cst.hour and wd < 5)
                         or (now_cst.hour < BRIEF_HOUR_END and 1 <= wd <= 5))
            if (time.time() - last_brief >= BRIEF_INTERVAL and in_window):
                try:
                    trend = weekly_trend()
                    send_wechat(compose_brief(price, resistance, support, trend))
                    log(f"行情播报已发送：现价 {price:,.0f}")
                except Exception as e:
                    log(f"行情播报发送失败（跳过本轮）：{e}")
                state["brief_last"] = time.time()
                save_state(state)
            with open(HEARTBEAT_FILE, "w", encoding="utf-8") as f:
                f.write(datetime.now(CST).isoformat() + f" price={price}")
        except Exception as e:
            log(f"轮询出错（继续运行）：{e}")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
