# OKX (custom.okx) — local read-only helper

Status: local helper, NOT a registered vault connector. Muse's secure
connector flow declined OKX on 2026-10-23 because its API authenticates
with HMAC-signed requests (API key + secret + passphrase). The user
explicitly approved the alternative the same day: a read-only API key
kept in a local file, used only by a local read-only script.

## Helper
- Script: `~/workspace/okx-trading/okx_read.py` (Python stdlib only)
- Commands: `time` (public connectivity check), `balance`, `positions`, `fills`
- Endpoints (GET only): /api/v5/public/time, /api/v5/account/balance,
  /api/v5/account/positions, /api/v5/trade/fills
- There are NO order/transfer/withdraw code paths. Do not add any without
  the user's explicit new approval; real order placement stays governed
  by the gated module rules in ~/workspace/okx-trading/SYSTEM.md.

## Credential
- The user's READ-ONLY OKX API key set (api_key, secret, passphrase) lives
  in `~/workspace/okx-trading/.okx_readonly.json`, file mode 0600.
- Never print, log, copy, or store the values anywhere else (not in this
  doc, not in memory files, not in chat summaries).
- The key must have the "read" permission only — no trade, no withdraw.
- Rotation/revocation: the user manages keys in OKX (profile → API). To
  rotate, replace the JSON file's values and keep mode 600.

## Verified
- 2026-10-23: script compiles; `time` returns code 0 from this VM
  (www.okx.com requires a browser-like User-Agent header; urllib default
  gets HTTP 403).
- 2026-10-23 morning: authenticated reads VERIFIED end-to-end —
  `balance` and `positions` return the user's real account (BTC-USDT-SWAP
  long @ 82,349 matches his reported open). First passphrase attempt
  failed with 50105 (a capital letter had been typed lowercase); the
  exact passphrase is case-sensitive and is stored only in the creds
  file. `fills` returned an empty list on first call (endpoint live,
  no rows in default window).

## Troubleshooting
- 401 / code 50111-50113: wrong key/secret/passphrase or clock skew —
  re-check values with the user; do not retry blindly.
- HTTP 403 on public endpoints: User-Agent header missing.
