---
id: iphone-shipment-check-20261031
title: iPhone发货跟进（10-30最晚发货日）
enabled: true
owner: goal:2027-3-2
mode: task
schedule:
  kind: runonce
  timezone: Asia/Shanghai
  at: 2026-10-31T09:00:00
delivery:
  - chat_id: c6a95dc0-fa9a-447d-a16c-6b396d089426
metadata:
  originating_chat_context_json: '{"origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false}'
  presentation_locale: zh-CN
---
老大，iPhone 18 Pro Max 的最晚发货日（2026-10-30）已经过了，问一句：手机发货了吗？

- 如果发货/到货了：把物流状态、预计到手价/实际卖出价告诉我，我记到文档 7.3 和网站（个人盈利 + 交易日记相关）。
  - 如果已经卖出、钱已到账：当场提醒他 2026-10-21 定的计划——¥3,000 对应金额现价买 BTC、¥2,000 对应金额现价买 USDT，买完转进他的冷钱包（买到多少标的他会告知，之后再入账；他明确过这事不记文档、只提醒）。
  - 如果到货了但还没卖：回一句，让他卖出到账后告诉我一声，到时候我提醒他买入计划。
- 如果还没发货：回一下新的预计发货时间，我更新记录。

如果这次还没发货：再安排一次一次性的跟进，7 天后（2026-11-07 09:00）问一次；发货确认后这个跟进就停，不再打扰。
