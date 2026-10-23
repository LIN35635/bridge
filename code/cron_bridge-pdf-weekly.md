---
id: bridge-pdf-weekly
title: 每周导出个人数据桥 PDF
enabled: true
owner: goal:super-interactive-bridge
mode: task
schedule:
  kind: weekly
  timezone: '@user.current'
  time: 20:06:00
  dow: [Tue]
delivery:
  - chat_id: c6a95dc0-fa9a-447d-a16c-6b396d089426
metadata:
  tags: [cron:flexible-time]
  originating_chat_context_json: '{"chat_id":"c6a95dc0-fa9a-447d-a16c-6b396d089426","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"a0cda498-bbc8-48fe-a0f2-e75515e63e70"}'
  presentation_locale: zh-CN
---
任务：每周导出最新版《个人交互数据桥》PDF 并发给用户保存（用户 2026-10-20 要求：「记得每周提醒我导出一份个人数据桥PDF版本」；形式定为由助手直接生成 PDF 发给他，他只需存到手机上）。2026-10-20 晚用户又确认新增「常驻最新版 PDF」：固定一份 ~/workspace/your_files/personal-bridge-latest.pdf，每次文档更新后都重新生成覆盖；本每周任务改为刷新并发送这一份常驻版。2026-10-20 晚用户再明确：他的文件区只保留 PDF 版，不要 HTML 文件——网站 HTML 主文件存放在助手工作区 ~/workspace/bridge-deploy/index.html，导出一律从该文件生成；用户文件区不得再放入任何 HTML 文档。

做法（生成器已于 2026-10-20 实测通过，格式固定，不要另发明方法）：
1. 运行：cd ~/workspace/bridge-deploy/pagetest && node export-pdf.js（不带参数时自动用当天日期）。它从 ~/workspace/bridge-deploy/index.html 提取《个人交互数据桥》全文，套用已定稿的打印版式（A4、封面含导出日期与字数、每部分分页、表格跨页重复表头、页脚带页码），输出 dated PDF 到 ~/workspace/your_files/personal-bridge-YYYY-MM-DD.pdf，并自动把常驻版 ~/workspace/your_files/personal-bridge-latest.pdf 同步覆盖为同一内容（中间 HTML 只留在 bridge-deploy/pagetest 工作区，不进用户文件区）。
2. 校验：pdfinfo 常驻版确认页数 > 10、A4；pdftotext 抽查「个人交互数据桥」「统一分析标准」等关键词存在。校验不过就如实报告失败步骤，不要发坏文件。
3. 把常驻版 PDF（personal-bridge-latest.pdf）作为附件发到主聊天，附一句话：本周数据桥 PDF 已刷新，存手机上吧；顺带报页数与当前字数。
