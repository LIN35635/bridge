#!/usr/bin/env python3
"""
WeChat iLink Bot 守护程序
- 长轮询接收微信消息
- 收到消息 -> 写到 inbox/<id>.json
- 等待 Muse 主代理把回复写到 outbox/<id>.json
- 读到回复 -> 通过微信发回去

凭据从 creds.json 读取（bot_token 等）。
消息 ID 用时间戳+序号，保证唯一。
"""

import sys
import os
import json
import time
import threading

sys.path.insert(0, '/usr/local/lib/python3.12/dist-packages')

WORK_DIR = os.path.expanduser("~/workspace/wechat-ilink")
CREDS_FILE = os.path.join(WORK_DIR, "creds.json")
INBOX_DIR = os.path.join(WORK_DIR, "inbox")
OUTBOX_DIR = os.path.join(WORK_DIR, "outbox")
LOG_FILE = os.path.join(WORK_DIR, "bot_daemon.log")
CONTEXT_FILE = os.path.join(WORK_DIR, "context.json")
REPLY_TIMEOUT = 600  # 最多等 Muse 回复 600 秒（hook worker 冷启动+查上下文常超 120 秒）

os.makedirs(INBOX_DIR, exist_ok=True)
os.makedirs(OUTBOX_DIR, exist_ok=True)

_seq = [0]
_seq_lock = threading.Lock()

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + "\n")
    except Exception:
        pass

def save_context(msg):
    """保存最新 context_token 到磁盘，供哨兵等外部程序主动发消息时使用。"""
    try:
        token = msg.context_token
        if token:
            with open(CONTEXT_FILE, 'w', encoding='utf-8') as f:
                json.dump({'userId': str(msg.from_user), 'context_token': token,
                           'updated_at': time.time()}, f, ensure_ascii=False)
    except Exception as e:
        log(f"保存 context_token 失败: {e}")

def next_msg_id():
    with _seq_lock:
        _seq[0] += 1
        return f"{int(time.time()*1000)}_{_seq[0]}"

def wait_for_reply(msg_id):
    """等待 Muse 把回复写到 outbox/<msg_id>.json"""
    reply_file = os.path.join(OUTBOX_DIR, f"{msg_id}.json")
    start = time.time()
    while time.time() - start < REPLY_TIMEOUT:
        if os.path.exists(reply_file):
            try:
                with open(reply_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                os.remove(reply_file)
                return data.get('text', '')
            except Exception as e:
                log(f"读取回复失败: {e}")
                return None
        time.sleep(1)
    return None

def main():
    from weixin_ilink import WeixinBot

    if not os.path.exists(CREDS_FILE):
        log("未找到凭据，请先扫码登录")
        sys.exit(1)

    # 直接用凭据文件（info_json 格式：botToken/accountId/baseUrl/userId）
    bot = WeixinBot(credentials_file=CREDS_FILE)

    @bot.on_text
    def handle_text(msg):
        msg_id = next_msg_id()
        save_context(msg)
        log(f"[收到文本] id={msg_id} from={msg.from_user}: {msg.text[:60]}")
        # 写进 inbox，唤醒 Muse
        inbox_file = os.path.join(INBOX_DIR, f"{msg_id}.json")
        with open(inbox_file, 'w', encoding='utf-8') as f:
            json.dump({
                'id': msg_id,
                'type': 'text',
                'sender': str(msg.from_user),
                'text': msg.text,
                'time': time.time(),
            }, f, ensure_ascii=False)
        # 等回复
        reply = wait_for_reply(msg_id)
        if reply:
            log(f"[发送回复] id={msg_id}: {reply[:60]}")
            try:
                msg.reply_text(reply)
            except Exception as e:
                log(f"发送回复失败: {e}")
        else:
            log(f"[超时] id={msg_id} 未等到回复")
            try:
                msg.reply_text("老大，我这边处理超时了，你在 Muse App 里直接找我吧。")
            except Exception:
                pass

    @bot.on_image
    def handle_image(msg):
        msg_id = next_msg_id()
        save_context(msg)
        log(f"[收到图片] id={msg_id} from={msg.from_user}")
        img_path = os.path.join(INBOX_DIR, f"{msg_id}.jpg")
        try:
            msg.save(img_path)
        except Exception as e:
            log(f"保存图片失败: {e}")
            img_path = None
        inbox_file = os.path.join(INBOX_DIR, f"{msg_id}.json")
        with open(inbox_file, 'w', encoding='utf-8') as f:
            json.dump({
                'id': msg_id,
                'type': 'image',
                'sender': str(msg.from_user),
                'image_path': img_path,
                'time': time.time(),
            }, f, ensure_ascii=False)
        reply = wait_for_reply(msg_id)
        if reply:
            try:
                msg.reply_text(reply)
            except Exception as e:
                log(f"发送图片回复失败: {e}")

    log("机器人启动，开始长轮询...")
    bot.run()

if __name__ == '__main__':
    main()
