#!/usr/bin/env python3
"""
OKX 带人工确认的实盘闸门模块（live_gated.py）

定位：这是一个“闸门层”，不是自动交易机器人。
- 默认模式永远是 PAPER（模拟），不会发真实订单。
- 即使满足全部条件，本版本也不会真的向 OKX 发送下单请求：
  真实下单的签名请求是故意留空的，需要你单独审阅、单独接线。
  这样设计是为了保证：没有任何一次实盘订单会在“没看清”时发出去。
- 没有自动交易，没有连续下单循环，没有自动重试。
  每一笔实盘意向都必须走一次完整的：预览 -> 手动输入确认词 -> 发送前再验风控。

实盘闸门（缺一不可，任一项不通过就拒绝）：
  1) 环境变量 OKX_LIVE_ENABLED=1（默认没有这个变量 = PAPER，拒绝实盘）
  2) API 凭证齐全：只从环境变量 OKX_API_KEY / OKX_API_SECRET /
     OKX_API_PASSPHRASE 读取，或走 Secure Vault 模式注入环境变量。
     绝不硬编码、绝不打印、绝不写进文件、绝不发到聊天里。
     缺失任一项 -> 拒绝实盘，并提示用环境变量 / Secure Vault。
  3) 实盘前检查清单（preflight）：要求你亲手确认资金隔离与风险，
     必须输入指定确认词才算通过。
  4) 完整订单预览：品种、方向、数量、杠杆、入场、硬止损、最大亏损、
     保证金占用 vs 半仓 50% 上限、回撤状态，全部打印出来给你看。
  5) 手动确认：必须在终端亲手输入确切确认词 CONFIRM（区分大小写），
     只给一次机会，输错 / 输别的 / 直接回车 = 拒绝，不重试、不循环追问。
  6) 发送前再验风控：半仓 <=50%、硬止损已绑定、杠杆 <=5x（用户新规则）、
     回撤 <15%、资金隔离已确认。任一项失败 -> 拒绝。
     ⚠️ 5x 下强平缓冲约 19.5%，低于《天命》30% 目标，强平风险高于旧 3x 版本。

用户修正规则（2026-10-16）：杠杆 5x；单笔保证金 = 总资金 10%（名义 50%）；
硬止损 = 价格逆势 2%；单笔亏损 = 50% × 2% = 总资金的 1%。仅 BTC（BTC-USDT）。
入场原则：只用价格 + 成交量，无任何指标线（抛弃所有指标，指标滞后，除了成交量；
参考利弗莫尔）。突破必须放量，无放量不算有效突破。

资金隔离（必须遵守，用户需在检查清单里亲手确认）：
  - 实盘资金必须是独立子账户里的一笔小额隔离资金。
  - 绝不是借贷资金、生活费、还款资金、应急储备。
  - 交易 / 储备 / 生活资金 100% 隔离，严禁跨边界划转。
  - 如果你无法确认以上任何一条，不要开实盘。

用法（全部是演练，不发真实订单）：
  python3 live_gated.py --dry-run      # 演练：PAPER 拒绝实盘 + 确认词输错拒绝
  python3 live_gated.py --preflight    # 只跑实盘前检查清单（需手动输入确认词）
  python3 live_gated.py --preview      # 只看一笔示例订单的预览与风控计算，不确认、不发送
"""
import argparse
import os
import sys
from dataclasses import dataclass

# ===== 闸门常量 =====
# 确认词：必须一字不差输入 CONFIRM（区分大小写），只给一次机会。
CONFIRM_PHRASE = "CONFIRM"
# 检查清单确认词：必须一字不差输入“已确认资金隔离”。
PREFLIGHT_PHRASE = "已确认资金隔离"
# 实盘总开关：只有环境变量 OKX_LIVE_ENABLED=1 才算“想开实盘”，其余一律 PAPER。
LIVE_ENV_VAR = "OKX_LIVE_ENABLED"

# 风控上限（用户新规则，与 config.py 一致）
# ⚠️ 5x 下强平缓冲约 19.5%，低于《天命》30% 目标，强平风险高于旧 3x 版本。
MAX_LEVERAGE = 5            # 杠杆上限 5x（用户明确要求）
PER_TRADE_MARGIN_RATIO = 0.10  # 单笔保证金 = 总资金 10%（名义 50%）
MAX_MARGIN_RATIO = 0.50     # 半仓总上限：保证金占用 <= 可用资金的 50%
MAX_DRAWDOWN = 0.15         # 回撤 <15%，达到即停机
# 硬止损价格距离 2%：价格逆势 2% 即止损；单笔亏损 = 50% 名义 × 2% = 总资金的 1%
DEFAULT_STOP_PCT = 0.02
BTC_SYMBOL = "BTC-USDT"    # 仅 BTC


@dataclass
class LiveOrderIntent:
    """一笔实盘意向（还不是订单）。止损必须在意向里就带上。"""
    symbol: str               # 如 BTC-USDT
    side: str                 # LONG 或 SHORT（多空双向，做空为做多的镜像）
    qty: float                # 数量（币数）
    entry: float              # 计划入场价
    stop: float               # 硬止损价（必须随单绑定）
    leverage: int             # 杠杆（<=5x，用户修正规则）
    balance: float            # 实盘子账户可用资金（USDT）
    peak: float               # 子账户历史最高权益（用于算回撤）
    existing_margin: float = 0.0   # 已有持仓占用的保证金
    reason: str = ""          # 进场理由（一句话）


class GateRefused(Exception):
    """闸门拒绝：任一检查不通过时抛出，绝不继续往下走。"""


# ===== 第 1 道闸：模式开关 =====
def is_live_enabled() -> bool:
    """只有 OKX_LIVE_ENABLED=1 才算想开实盘；其余情况一律 PAPER。"""
    return os.environ.get(LIVE_ENV_VAR, "") == "1"


# ===== 第 2 道闸：API 凭证（只读环境变量，绝不打印值） =====
def get_credentials_present() -> bool:
    """
    只检查三个环境变量是否都非空，不返回、不打印、不记录它们的任何值。
    凭证应由你在运行前通过环境变量或 Secure Vault 注入，例如：
      export OKX_API_KEY=...   （不要把真实值写进代码 / 聊天）
    返回 True 仅代表“都已设置”，不代表凭证正确。
    """
    key = os.environ.get("OKX_API_KEY", "")
    secret = os.environ.get("OKX_API_SECRET", "")
    passphrase = os.environ.get("OKX_API_PASSPHRASE", "")
    return bool(key and secret and passphrase)


# ===== 第 3 道闸：实盘前检查清单（必须亲手确认） =====
def preflight_checklist(input_func=input) -> None:
    """
    打印实盘前检查清单，要求亲手输入“已确认资金隔离”才算通过。
    输错 / 输别的 / 空输入 = 拒绝。只问一次，不循环追问。
    """
    print("========== 实盘前检查清单（请逐条核对） ==========")
    print("1) 实盘资金是独立子账户里的一笔小额隔离资金。")
    print("2) 这笔钱绝不是借贷资金、生活费、还款资金、应急储备。")
    print("3) 交易 / 储备 / 生活资金 100% 隔离，严禁跨边界划转。")
    print("4) 我已在模拟盘完整验证过策略、风控、日志。")
    print("5) 我清楚：加密货币合约交易可能快速亏损全部本金，")
    print("   杠杆会放大亏损，回测结果不等于未来收益。")
    print("6) API 凭证只通过环境变量 / Secure Vault 传入，")
    print("   没有写进代码、没有发到聊天里。")
    print("--------------------------------------------------")
    print(f"如果你以上全部确认，请亲手输入：{PREFLIGHT_PHRASE}")
    answer = input_func("输入确认词：").strip()
    if answer != PREFLIGHT_PHRASE:
        raise GateRefused("检查清单未确认：输入与确认词不一致，拒绝实盘。")


# ===== 风控计算（纯计算，不联网、不下单） =====
def calc_preview(order: LiveOrderIntent) -> dict:
    """算出一笔意向的全部关键数字，供预览与风控检查共用。"""
    notional = order.qty * order.entry
    new_margin = notional / order.leverage if order.leverage else float("inf")
    total_margin = order.existing_margin + new_margin
    margin_ratio = total_margin / order.balance if order.balance > 0 else float("inf")
    # 最大亏损 = 入场与硬止损之间的距离 x 数量（不含手续费/滑点，实盘只会更差）
    max_loss = abs(order.entry - order.stop) * order.qty
    drawdown = (order.peak - order.balance) / order.peak if order.peak > 0 else 0.0
    return {
        "notional": notional,
        "new_margin": new_margin,
        "total_margin": total_margin,
        "margin_ratio": margin_ratio,
        "margin_cap": order.balance * MAX_MARGIN_RATIO,
        "max_loss": max_loss,
        "drawdown": drawdown,
    }


def check_risk(order: LiveOrderIntent) -> dict:
    """
    发送前再验风控。返回预览字典；任一项不通过就抛 GateRefused。
    注意：这个函数在“确认之后、发送之前”会再跑一次，
    防止确认后市场/资金状态变化导致的风险超标。
    """
    errors = []
    if order.symbol != BTC_SYMBOL:
        errors.append(f"本套件只做 BTC（{BTC_SYMBOL}），拒绝品种：{order.symbol}")
    if order.qty <= 0 or order.entry <= 0 or order.stop <= 0 or order.balance <= 0:
        errors.append("数量 / 价格 / 止损 / 账户余额非法。")
    if order.leverage < 1 or order.leverage > MAX_LEVERAGE:
        errors.append(f"杠杆 {order.leverage}x 超过上限 {MAX_LEVERAGE}x。")
    # 多空双向：做多或做空均可，做空为做多的镜像（久涨后跌破回抽做空）。
    if order.side not in ("LONG", "SHORT"):
        errors.append("方向非法：只接受 LONG 或 SHORT。")
    # 硬止损必须随单绑定，且方向合理
    if order.side == "LONG" and not (order.stop < order.entry):
        errors.append("做多意向的硬止损必须低于入场价，且必须随单绑定。")
    if order.side == "SHORT" and not (order.stop > order.entry):
        errors.append("做空意向的硬止损必须高于入场价，且必须随单绑定。")
    preview = calc_preview(order)
    # 半仓
    if preview["total_margin"] > preview["margin_cap"] + 1e-9:
        errors.append(
            f"半仓不通过：已有保证金 {order.existing_margin:.2f} + 新单 {preview['new_margin']:.2f} "
            f"= {preview['total_margin']:.2f} > 上限 {preview['margin_cap']:.2f}（可用 {order.balance:.2f} 的 50%）"
        )
    # 回撤
    if preview["drawdown"] >= MAX_DRAWDOWN:
        errors.append(f"回撤 {preview['drawdown'] * 100:.2f}% 已达 {MAX_DRAWDOWN * 100:.0f}% 上限，停机，拒绝新开仓。")
    if errors:
        raise GateRefused("风控检查不通过：" + "；".join(errors))
    return preview


# ===== 第 4 道闸：完整订单预览（全部数字摊开给你看） =====
def show_preview(order: LiveOrderIntent, preview: dict) -> None:
    print("========== 订单预览（请仔细核对，确认前不会发送） ==========")
    print(f"品种：{order.symbol}    方向：{order.side}    理由：{order.reason or '（未填）'}")
    print(f"数量：{order.qty}    入场价：{order.entry:.2f}    硬止损：{order.stop:.2f}")
    print(f"杠杆：{order.leverage}x（上限 {MAX_LEVERAGE}x）    名义价值：{preview['notional']:.2f} USDT")
    print(f"本单保证金：{preview['new_margin']:.2f} USDT")
    print(f"保证金占用：{preview['total_margin']:.2f} / 上限 {preview['margin_cap']:.2f} USDT"
          f"（占比 {preview['margin_ratio'] * 100:.1f}% / 50%）")
    print(f"最大亏损（按止损算，不含手续费/滑点）：约 {preview['max_loss']:.2f} USDT")
    print(f"子账户可用：{order.balance:.2f} USDT    回撤：{preview['drawdown'] * 100:.2f}%（上限 15%）")
    print("资金隔离：本单资金来自独立子账户小额隔离资金，不动用借贷 / 生活 / 还款 / 储备资金。")
    print("================================================================")


# ===== 第 5 道闸：手动确认（只给一次机会，不重试） =====
def confirm_order(input_func=input) -> None:
    """
    要求亲手输入确切确认词 CONFIRM。只问一次。
    输错 / 输别的 / 空输入 / 直接回车 = 拒绝，不重试、不循环追问。
    """
    print(f"确认下单请输入确切确认词：{CONFIRM_PHRASE}（区分大小写，输错即拒绝，不重试）")
    answer = input_func("输入确认词：").strip()
    if answer != CONFIRM_PHRASE:
        raise GateRefused("手动确认未通过：输入与确认词不一致，拒绝下单，不重试。")


# ===== 完整闸门流程：预览 -> 确认 -> 再验风控 ->（本版本不发送） =====
def run_gated_order(order: LiveOrderIntent, input_func=input) -> dict:
    """
    走完整个闸门流程。返回结果字典，绝不抛出以外的副作用。
    成功时 status = "gated_ready_not_sent"：意思是“已通过全部闸门，
    但本版本故意不发送真实订单”，真实下单请求需你单独审阅、单独接线。
    """
    # 第 1 道闸：模式开关
    if not is_live_enabled():
        return {
            "status": "refused_paper_mode",
            "message": "当前为 PAPER 模式（未设置 OKX_LIVE_ENABLED=1），拒绝实盘，未发送任何订单。",
        }
    # 第 2 道闸：凭证齐全（只检查是否设置，不打印值）
    if not get_credentials_present():
        return {
            "status": "refused_missing_credentials",
            "message": "API 凭证缺失：请通过环境变量 OKX_API_KEY / OKX_API_SECRET / "
                       "OKX_API_PASSPHRASE 或 Secure Vault 注入，绝不写进代码 / 聊天。",
        }
    try:
        # 第 3 道闸：检查清单
        preflight_checklist(input_func)
        # 预览前先验一次风控（提前拦截明显违规的意向）
        preview = check_risk(order)
        # 第 4 道闸：完整预览
        show_preview(order, preview)
        # 第 5 道闸：手动确认（一次机会）
        confirm_order(input_func)
        # 第 6 道闸：发送前再验风控（确认后、发送前最后一次）
        preview = check_risk(order)
    except GateRefused as e:
        return {"status": "refused", "message": str(e)}
    # 全部闸门通过，但本版本故意不发送真实订单。
    return {
        "status": "gated_ready_not_sent",
        "message": "已通过全部闸门，但本版本未接入真实下单请求，未发送任何订单。"
                   "如需真正下单，请单独审阅并接线 OKX 签名下单接口，绝不要跳过任一闸门。",
        "preview": {
            "symbol": order.symbol,
            "side": order.side,
            "qty": order.qty,
            "entry": order.entry,
            "stop": order.stop,
            "leverage": order.leverage,
            "notional": round(preview["notional"], 2),
            "new_margin": round(preview["new_margin"], 2),
            "total_margin": round(preview["total_margin"], 2),
            "margin_cap": round(preview["margin_cap"], 2),
            "max_loss": round(preview["max_loss"], 2),
            "drawdown_pct": round(preview["drawdown"] * 100, 2),
        },
    }


def _sample_order() -> LiveOrderIntent:
    """演练用示例意向：符合用户修正规则。数字仅用于演示。"""
    # 子账户 10000 USDT，BTC 90000，单笔保证金 10% = 1000，5x -> 名义 5000（= 50%，顶到半仓上限）
    # qty = 5000 / 90000 ≈ 0.055556；止损 88200（价格 -2%），最大亏损约 100 USDT（= 总资金 1%）
    return LiveOrderIntent(
        symbol="BTC-USDT", side="LONG", qty=0.055556,
        entry=90000.0, stop=88200.0, leverage=5,
        balance=10000.0, peak=10000.0, existing_margin=0.0,
        reason="dry-run 演示",
    )


def dry_run() -> None:
    """演练（不发真实订单，不需要凭证）：演示两类拒绝。"""
    print("========== 演练模式 dry-run（不发真实订单） ==========")
    # 演练 1：PAPER 模式下直接拒绝实盘
    os.environ.pop(LIVE_ENV_VAR, None)
    result = run_gated_order(_sample_order(), input_func=lambda _prompt: CONFIRM_PHRASE)
    print(f"[演练 1] PAPER 模式：{result['status']} — {result['message']}")
    # 演练 2：模拟已开 LIVE 开关但凭证缺失 -> 拒绝（不打印凭证值）
    os.environ[LIVE_ENV_VAR] = "1"
    os.environ.pop("OKX_API_KEY", None)
    os.environ.pop("OKX_API_SECRET", None)
    os.environ.pop("OKX_API_PASSPHRASE", None)
    result = run_gated_order(_sample_order(), input_func=lambda _prompt: CONFIRM_PHRASE)
    print(f"[演练 2] LIVE 开关已开但凭证缺失：{result['status']} — {result['message']}")
    # 演练 3：凭证齐全（用假占位值，仅演练流程），检查清单通过，
    # 但下单确认词输错（CONFIRN）-> 拒绝，不重试。
    # 注意输入顺序：先是检查清单确认词，再是下单确认词。
    os.environ["OKX_API_KEY"] = "DUMMY_PLACEHOLDER_NOT_REAL"
    os.environ["OKX_API_SECRET"] = "DUMMY_PLACEHOLDER_NOT_REAL"
    os.environ["OKX_API_PASSPHRASE"] = "DUMMY_PLACEHOLDER_NOT_REAL"
    drill3_answers = iter([PREFLIGHT_PHRASE, "CONFIRN"])
    result = run_gated_order(
        _sample_order(),
        input_func=lambda _prompt: next(drill3_answers),
    )
    print(f"[演练 3] 下单确认词输错：{result['status']} — {result['message']}")
    # 演练 4：风控违规意向（杠杆 6x，超过 5x 上限）-> 检查清单通过后，
    # 在预览前风控检查即拒绝，根本走不到下单确认。
    bad = _sample_order()
    bad.leverage = 6
    drill4_answers = iter([PREFLIGHT_PHRASE])
    result = run_gated_order(
        bad, input_func=lambda _prompt: next(drill4_answers),
    )
    print(f"[演练 4] 杠杆 6x 超上限：{result['status']} — {result['message']}")
    # 演练 5：做空（SHORT）意向通过风控检查 + 预览（做空为做多的镜像，
    # 止损在入场价上方）。只做风控 + 预览，不走手动确认、不发送。
    short = LiveOrderIntent(
        symbol="BTC-USDT", side="SHORT", qty=0.055556,
        entry=90000.0, stop=91800.0, leverage=5,
        balance=10000.0, peak=10000.0, existing_margin=0.0,
        reason="dry-run 演示 SHORT",
    )
    try:
        short_preview = check_risk(short)
        print(f"[演练 5] 做空 SHORT 通过风控：保证金 {short_preview['new_margin']:.2f}，"
              f"最大亏损约 {short_preview['max_loss']:.2f} USDT（总资金 1%）")
        show_preview(short, short_preview)
    except GateRefused as e:
        print(f"[演练 5] 做空 SHORT 被拒绝：{e}")
    # 清理演练用的假占位凭证与开关，避免污染后续真实运行环境
    for k in (LIVE_ENV_VAR, "OKX_API_KEY", "OKX_API_SECRET", "OKX_API_PASSPHRASE"):
        os.environ.pop(k, None)
    print("演练结束：全程未发送任何真实订单，未调用任何 OKX 实盘接口。")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="OKX 带人工确认的实盘闸门模块（默认 PAPER，不自动下单）")
    ap.add_argument("--dry-run", action="store_true", help="演练：演示 PAPER 拒绝 + 凭证缺失拒绝 + 确认词输错拒绝 + 风控拒绝")
    ap.add_argument("--preflight", action="store_true", help="只跑实盘前检查清单（需手动输入确认词）")
    ap.add_argument("--preview", action="store_true", help="只看示例订单预览与风控计算，不确认、不发送")
    args = ap.parse_args()
    if args.dry_run:
        dry_run()
    elif args.preflight:
        try:
            preflight_checklist()
            print("检查清单通过。")
        except GateRefused as e:
            print(f"拒绝：{e}")
            sys.exit(1)
    elif args.preview:
        order = _sample_order()
        try:
            preview = check_risk(order)
            show_preview(order, preview)
            print("预览结束：未确认、未发送。")
        except GateRefused as e:
            print(f"拒绝：{e}")
            sys.exit(1)
    else:
        print("默认 PAPER 模式，不发真实订单。")
        print("演练：python3 live_gated.py --dry-run")
        print("检查清单：python3 live_gated.py --preflight")
        print("只看预览：python3 live_gated.py --preview")
