#!/usr/bin/env bash
set -euo pipefail
source "$HATCH_HOOK_RUNTIME"

STOP=80702

resp="$(curl --fail --silent --show-error --max-time 10 'https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT-SWAP' 2>/dev/null || true)"

if [[ -z "${resp}" ]]; then
  log "fetch_failed" '{}'
  silent "OKX ticker fetch failed; will retry next poll" '{}'
else
  last="$(printf '%s' "${resp}" | jq -r '.data[0].last // empty')"
  if [[ -z "${last}" ]]; then
    log "parse_failed" '{}'
    silent "could not parse price; will retry next poll" '{}'
  else
    hit="$(awk -v p="${last}" -v s="${STOP}" 'BEGIN{print (p+0 <= s+0) ? 1 : 0}')"
    if [[ "${hit}" == "1" ]]; then
      disable_after_run
      wake "BTC price hit the hard stop 80702" "{\"price\": ${last}, \"stop\": ${STOP}, \"entry\": 82349}"
    elif awk -v p="${last}" 'BEGIN{exit !(p+0 <= 81500)}'; then
      log "approaching_stop" "{\"price\": ${last}, \"stop\": ${STOP}}"
      silent "price approaching stop; still watching" "{\"price\": ${last}}"
    else
      silent "price above stop" "{\"price\": ${last}}"
    fi
  fi
fi
