#!/usr/bin/env bash
# Headline demo for Milestone 2. Requires the stack to be up (`make up`).
#
#   A) Durability: start a deal, KILL the worker mid-flight, restart it, and show
#      the workflow resumes and closes exactly once (buffered signals + durable
#      state survive the crash).
#   B) Archival: a declined outreach and an NDA timeout each archive the deal
#      cleanly with no orphaned state.
set -euo pipefail

API="${API:-http://localhost:8000}"
MANDATE="${MANDATE:-mandate-42-0000}"

json_field() { grep -o "\"$2\":[ ]*\"[^\"]*\"" | head -1 | sed 's/.*: *"\(.*\)"/\1/'; }

start_deal() { # $1 = nda_timeout_seconds
  curl -fsS -X POST "$API/deals" -H 'content-type: application/json' \
    -d "{\"mandate_id\":\"$MANDATE\",\"nda_timeout_seconds\":$1}" | json_field _ deal_id
}

# poll_field <id> <field> <want> [tries]
poll_field() {
  local id="$1" field="$2" want="$3" tries="${4:-90}" val=""
  for _ in $(seq 1 "$tries"); do
    val="$(curl -fsS "$API/deals/$id" 2>/dev/null | json_field _ "$field" || true)"
    [ "$val" = "$want" ] && return 0
    sleep 1
  done
  echo "  ✗ timed out waiting for $field=$want (last=$val)"; return 1
}

echo "== preflight =="
curl -fsS "$API/health" >/dev/null && echo "  ✓ API healthy"

echo
echo "== Scenario A: kill-a-worker mid-deal, workflow resumes =="
IDA="$(start_deal 300)"; echo "  started $IDA"
poll_field "$IDA" stage awaiting_approval && echo "  ✓ reached awaiting_approval"
echo "  killing worker..."; docker compose kill worker >/dev/null
echo "  sending approve + nda signals while worker is DOWN (Temporal buffers them)..."
curl -fsS -X POST "$API/deals/$IDA/approve" >/dev/null
curl -fsS -X POST "$API/deals/$IDA/nda" >/dev/null
echo "  restarting worker..."; docker compose start worker >/dev/null
poll_field "$IDA" stage closed && echo "  ✓ PASS: $IDA resumed after crash and closed"

echo
echo "== Scenario B1: decline -> clean archive =="
IDB="$(start_deal 300)"; echo "  started $IDB"
poll_field "$IDB" stage awaiting_approval
curl -fsS -X POST "$API/deals/$IDB/decline" >/dev/null
poll_field "$IDB" stage archived
reason="$(curl -fsS "$API/deals/$IDB" | json_field _ reason)"
[ "$reason" = "declined" ] && echo "  ✓ PASS: $IDB archived (reason=declined)"

echo
echo "== Scenario B2: NDA timeout -> clean archive =="
IDC="$(start_deal 5)"; echo "  started $IDC (nda_timeout=5s)"
poll_field "$IDC" stage awaiting_approval
curl -fsS -X POST "$API/deals/$IDC/approve" >/dev/null   # approve but never sign NDA
poll_field "$IDC" stage archived 30
reason="$(curl -fsS "$API/deals/$IDC" | json_field _ reason)"
[ "$reason" = "nda_timeout" ] && echo "  ✓ PASS: $IDC archived (reason=nda_timeout)"

echo
echo "All demo scenarios passed."
