---
id: fitness-sleep-log-evening
title: 健身登记＋睡眠登记（晚上）
enabled: true
owner: goal:super-interactive-bridge
mode: task
schedule:
  kind: daily
  timezone: '@user.current'
  time: 22:17:00
delivery:
  - chat_id: c6a95dc0-fa9a-447d-a16c-6b396d089426
metadata:
  originating_chat_context_json: '{"chat_id":"c6a95dc0-fa9a-447d-a16c-6b396d089426","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"a0cda498-bbc8-48fe-a0f2-e75515e63e70"}'
  presentation_locale: zh-CN
---
给用户的晚上登记提醒（中文、简短、像兄弟聊天），只问两件事：1）健身登记：今天练没练、练了哪个部位、动作组数次数、哑铃重量、开始结束时间、身体感受；没练就记休息日和原因。2）东鹏特饮喝了几瓶、最后一次几点喝的。不问步数——用户 2026-10-21 定的规矩：步数由主会话自己从 Apple Health 读，不再问他。不问"计划几点上床"——上床时间他睡前会主动报。午睡不问——午睡默认没有，只有他主动说了才记。让他直接把数据发过来，我会记到桥上。
