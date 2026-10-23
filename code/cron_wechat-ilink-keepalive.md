---
id: wechat-ilink-keepalive
title: 微信 iLink 机器人保活
enabled: true
owner: goal:wechat-ilink
mode: task
schedule:
  kind: interval
  timezone: UTC
  at: 2026-10-20T03:21:21
  every: 10m
metadata:
  tags: [cron:automatic-interval-anchor]
  originating_chat_context_json: '{"chat_id":"c6a95dc0-fa9a-447d-a16c-6b396d089426","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"a0cda498-bbc8-48fe-a0f2-e75515e63e70"}'
  presentation_locale: zh-CN
---
微信 iLink 机器人保活检查。背景：用户 2026-10-20 要求搭建微信 iLink 机器人并已扫码绑定（bot 在线收发微信消息），守护进程为 ~/workspace/wechat-ilink/bot_daemon.py（Python 长轮询，收到消息写 inbox/、等主代理回写 outbox/ 再发回微信）。用户被承诺过 24 小时在线，但 VM 重启会杀掉进程。另有 BTC 突破哨兵 ~/workspace/btc-sentinel/sentinel.py（2026-10-20 上线，盯 OKX BTC 永续日线关键位，突破/跌破时借机器人通道主动发微信提醒），同样需要保活。

每次运行做这四件事：
1. 检查机器人进程：用 `pgrep -f '[b]ot_daemon.py'` 找 PID，再用 `ps -o cmd -p <PID>` 二次确认确实是 bot_daemon.py（不要直接信 pgrep，历史上出现过把自家 shell 误报成守护进程的情况）。如果进程不存在，先确认 ~/workspace/wechat-ilink/creds.json 存在，然后用 `cd ~/workspace/wechat-ilink && nohup python3 bot_daemon.py >> daemon_stdout.log 2>&1 &` 重启（若报 ModuleNotFoundError: weixin_ilink，先 `pip install --break-system-packages weixin-ilink` 再重启），并在 bot_daemon.log 追加一行带时间的重启记录。重启成功后向用户报告一次"机器人掉线已自动重启"。
2. 查看最近 15 分钟的 bot_daemon.log 是否出现登录失效信号（关键词：登录过期 / expired / 401 / token 无效 / 扫码 / login）。如果出现，说明微信会话过期、需要用户重新扫码绑定——这是唯一需要打扰用户的情况，向用户报告"微信机器人登录过期，需要重新扫码"，并说明需要他配合扫码。
3. 顺手检查哨兵进程：用 `ps aux | grep '[s]entinel.py'` 确认 ~/workspace/btc-sentinel/sentinel.py 在跑；不在时用 `cd ~/workspace/btc-sentinel && nohup ./start_sentinel.sh >> sentinel_stdout.log 2>&1 &` 重启（start_sentinel.sh 会自建 venv 并装 requests）。哨兵重启不单独打扰用户，sentinel.log 里有启动记录即可。如果 sentinel.log 最近 15 分钟反复出现"微信发送失败"，多半是 ~/workspace/wechat-ilink/context.json 里的通行证过期——用户下次给机器人发消息会自动刷新，不用打扰；只有同时命中第 2 条登录失效时才按第 2 条报告。
4. 进程正常、日志无异常时保持完全安静，不要发任何消息。

不要碰 creds.json 和 context.json 的内容，不要把凭据写入日志或报告。
