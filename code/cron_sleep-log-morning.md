---
id: sleep-log-morning
title: 睡眠登记（早上）
enabled: true
owner: goal:super-interactive-bridge
mode: task
schedule:
  kind: daily
  timezone: '@user.current'
  time: 08:06:00
delivery:
  - chat_id: c6a95dc0-fa9a-447d-a16c-6b396d089426
metadata:
  tags: [cron:flexible-time]
  originating_chat_context_json: '{"chat_id":"c6a95dc0-fa9a-447d-a16c-6b396d089426","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"a0cda498-bbc8-48fe-a0f2-e75515e63e70"}'
  presentation_locale: zh-CN
---
早上睡眠登记（中文、简短、像兄弟聊天）。2026-10-22 起睡眠数据由 Apple Health 自动写入桥，他的规矩是「以后自己去读」——所以先自己读、再开口：1）先自己从 Apple Health 读昨晚睡眠（入睡时间、起床时间、时长、夜醒次数）；2）再查桥（~/workspace/bridge-deploy/data.html）确认这条睡眠已记入，已在的数据一律不再问他。只问 Health 没有、只能他自己感受的两个事：昨晚睡得怎么样（质量感受）、今天白天精神怎么样。如果他说今天休息没练，也记下来。不问步数——步数由主会话自己读。不问计划几点上床——他睡前会自己报。午睡不问——默认没有。他回了之后按桥的格式记入文档。
