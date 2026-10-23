---
id: asset-report-feb-end
title: 二月资产报告（28 号补月末）
enabled: true
owner: goal:super-interactive-bridge
mode: task
schedule:
  kind: yearly
  timezone: Asia/Shanghai
  time: 20:06:00
  dom: [28]
  month: [2]
delivery:
  - chat_id: c6a95dc0-fa9a-447d-a16c-6b396d089426
metadata:
  tags: [cron:flexible-time]
  originating_chat_context_json: '{"chat_id":"c6a95dc0-fa9a-447d-a16c-6b396d089426","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"a0cda498-bbc8-48fe-a0f2-e75515e63e70"}'
  presentation_locale: zh-CN
---
二月资产报告（用户林志锋 2026-10-23 定下：每月底做资产报告；二月没有 30 号，用 28 号即二月最后一天补这一期，内容口径与每月 30 号的资产报告完全相同）。

执行步骤：
1. OKX 账户自读：运行 `python3 ~/workspace/okx-trading/okx_read.py balance` 和 `python3 ~/workspace/okx-trading/okx_read.py positions`，取账户总权益（USD）、各币种明细、未平仓持仓的浮盈亏。（只读接口 2026-10-23 已接通；失败则在报告里如实标注 OKX 数据未取到，不编造。）
2. ETF 取价：他的持仓为标普500ETF博时 513500 ×300 份、纳指ETF广发 159941 ×100 份（份额以《个人交互数据桥》文档 1.12 的最新记录为准，如已变更按最新份额）。用 `curl -s 'https://qt.gtimg.cn/q=sh513500,sz159941'`（GBK 编码需转码）取当日收盘价（20:00 已收盘，最新价即收盘价），算人民币市值，并注明成本与浮盈（成本：513500 建仓 2.695、159941 建仓 1.634，同样以文档最新记录为准）。
3. 汇率：取当日 USD/CNY 在岸价（新浪 fx_susdcny 或 Frankfurter 二选一，注明来源与日期）。
4. 现金类：支付宝小荷包等用他最近一次报告的金额并标注报告日期（最近一次为 2026-10-20 的 ¥300；如文档里已有更新的数字，用新数）。不要在月中口径外向他追问余额；本报告在月底，属月度核对窗口。
5. 汇总：总资产分别给出 USD 与 RMB 两个总数；每项列数量、单价、折算值；与上月报告比增减（报告存档在 ~/workspace/goals/super-interactive-bridge/hidden_files/asset-reports/）。另起一行备忘：自认债务余额（取桥文档当期口径）与净资产（资产−债务），与资产明细分开呈现。
6. 存档：把报告全文存到 ~/workspace/goals/super-interactive-bridge/hidden_files/asset-reports/asset-report-YYYY-MM-DD.md。
7. 文档同步：把本月快照按《个人交互数据桥》的文档更新流程并入 1.12 资产节（改 data.html → build → 渲染测试 → 部署 → 刷新 PDF）；若某步失败，在给用户的报告末尾如实标注未完成项，不要声称已完成。
8. 交付：在主聊天把报告发给用户。只报数与计算过程，不给投资建议，不劝买卖。所有数字注明来源与时点；取不到的写「未取到」，绝不补造。
