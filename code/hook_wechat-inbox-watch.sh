#!/usr/bin/env bash
set -euo pipefail
source "$HATCH_HOOK_RUNTIME"

INBOX_DIR="$HOME/workspace/wechat-ilink/inbox"
STATE_DIR="$HOME/hooks/state"
STATE_FILE="$STATE_DIR/wechat-inbox-seen.txt"
mkdir -p "$STATE_DIR"
touch "$STATE_FILE"

# 找收件箱里的 json 文件
NEW_MESSAGES=()
if [ -d "$INBOX_DIR" ]; then
  for f in "$INBOX_DIR"/*.json; do
    [ -e "$f" ] || continue
    base=$(basename "$f")
    if ! grep -qx "$base" "$STATE_FILE"; then
      NEW_MESSAGES+=("$f")
      # 非 dry run 时记录已见过
      if [ "${HATCH_HOOK_DRY_RUN:-0}" != "1" ]; then
        echo "$base" >> "$STATE_FILE"
      fi
    fi
  done
fi

if [ ${#NEW_MESSAGES[@]} -eq 0 ]; then
  silent "no new wechat messages" '{}'
else
  FIRST="${NEW_MESSAGES[0]}"
  FIRST_BASE=$(basename "$FIRST")
  COUNT=${#NEW_MESSAGES[@]}
  # 用 jq 构造 payload，避免手工拼引号出错；不内嵌消息原文，worker 自己读文件
  PAYLOAD=$(jq -n --arg file "$FIRST_BASE" --argjson count "$COUNT" '{"message_file": $file, "count": $count}')
  LOGPAYLOAD=$(jq -n --arg file "$FIRST_BASE" --argjson count "$COUNT" '{"count": $count, "file": $file}')
  log "new wechat message" "$LOGPAYLOAD"
  wake "new WeChat message arrived" "$PAYLOAD"
fi
