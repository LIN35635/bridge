---
id: bridge-backup-email-daily
title: 每晚文档备份邮件（23:00，当天有改才发）
enabled: true
owner: goal:super-interactive-bridge
mode: task
schedule:
  kind: daily
  timezone: '@user.current'
  time: 23:00:00
delivery:
  - chat_id: c6a95dc0-fa9a-447d-a16c-6b396d089426
metadata:
  originating_chat_context_json: '{"chat_id":"c6a95dc0-fa9a-447d-a16c-6b396d089426","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"a0cda498-bbc8-48fe-a0f2-e75515e63e70"}'
  presentation_locale: zh-CN
---
每晚 23:00 的《个人交互数据桥》备份邮件（用户 2026-10-22 定版：当天文档有改动才发，一天最多一封；当天没改动、或当天已经发过备份，就不发）。

执行步骤：
1. 判断今天文档有没有改动：看 ~/workspace/bridge-deploy/data.html 的修改日期是否为今天（Asia/Shanghai 本地日期）。不是今天 → 今天没有文档更新，什么都不发，直接结束，也不要在聊天里汇报。
2. 防重复：用 Gmail 查最近的已发送邮件（/opt/hatch/bin/hatch_gws_cli gmail +triage --query 'in:sent 备份' --max 5 --format json），核对日期与主题；若今天已经发出过一封主题含《个人交互数据桥》备份的邮件 → 不再发，直接结束，不汇报。
3. 是今天、且今天还没发过 → 先刷新常青 PDF：在 ~/workspace/bridge-deploy/pagetest/ 下运行 node export-pdf.js（不带路径参数），确认 PDF 已按最新 data.html 重新生成（成品在 ~/workspace/goals/super-interactive-bridge/files/personal-bridge-latest.pdf；~/workspace/your_files/personal-bridge-latest.pdf 是它的软链）。
4. 用 Gmail 发备份邮件：/opt/hatch/bin/hatch_gws_cli gmail +send --to 'six26181@gmail.com' --subject '《个人交互数据桥》备份（当天日期 YYYY-MM-DD）' --body '《个人交互数据桥》备份（当天日期版）。附件1 PDF 是文档全文，手机上能打开看；附件2 data.html 是网站的全部数据母本，万一网站出问题靠它能完整恢复。' --attach /home/hatch/workspace/goals/super-interactive-bridge/files/personal-bridge-latest.pdf --attach /home/hatch/workspace/bridge-deploy/data.html。附件合计约 2.5MB，在 Gmail 25MB 上限内。
5. 发送成功 → 不要在聊天里汇报（邮件本身就是通知，避免打扰）。发送失败 → 在主聊天简短告诉用户今晚的备份没发出去、失败在哪一步；不要重复发送，同一晚最多尝试一次发送。
