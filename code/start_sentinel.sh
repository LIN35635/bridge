#!/usr/bin/env bash
# BTC 哨兵启动器：单实例锁（防保活与手动同时拉起两个）；确保 venv 存在，然后运行哨兵。
set -e
cd "$HOME/workspace/btc-sentinel"
exec 9>"$HOME/workspace/btc-sentinel/sentinel.lock"
if ! flock -n 9; then
  echo "已有哨兵在运行，本次启动退出" >&2
  exit 0
fi
if [ ! -x "venv/bin/python" ]; then
  python3 -m venv venv
  ./venv/bin/pip install -q requests
fi
exec ./venv/bin/python sentinel.py
