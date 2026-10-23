#!/usr/bin/env bash
set -euo pipefail
source "$HATCH_HOOK_RUNTIME"

out="$(python3 /home/hatch/workspace/okx-trading/okx_watch.py 2>/dev/null || true)"

if [[ -z "${out}" ]]; then
  log "watch_failed" '{}'
  silent "okx_watch.py produced no output; will retry next poll" '{}'
else
  infra="$(printf '%s' "${out}" | jq -r '.infra_error // empty')"
  if [[ -n "${infra}" ]]; then
    log "infra_error" "$(jq -nc --arg d "${infra}" '{detail: $d}')"
    silent "okx watch infra error; staying silent" '{}'
  else
    count="$(printf '%s' "${out}" | jq '.events | length')"
    if [[ "${count}" != "0" ]]; then
      payload="$(printf '%s' "${out}" | jq -c '{events: .events}')"
      wake "OKX position or system-rule events detected" "${payload}"
    else
      silent "no position changes, no rule events" '{}'
    fi
  fi
fi
